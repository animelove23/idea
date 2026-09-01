#!/usr/bin/env python3
"""Run the 64-image batch=1 fixed-prefix VSV x SLA factorial."""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import torch

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import myutils
from experiments.termination_audit.fixed_prefix_sanity import (
    cpu_components,
    ensure_clean_model_state,
    extend_prefix,
    forward_components,
    greedy_prefix,
    image_path_from_id,
    load_selected_ids,
    parse_layer_indices,
    prepare_image,
    prompt_kwargs,
    tensor_metrics,
    vsv_mode,
)
from llava.utils import disable_torch_init
from model_loader import ModelLoader
from steering_vector import obtain_vsv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mechanism-manifest", type=Path, required=True)
    parser.add_argument("--data-path", type=Path, required=True)
    parser.add_argument("--checkpoint-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="llava-1.5")
    parser.add_argument("--num-pairs", type=int, default=32)
    parser.add_argument("--prefix-lengths", default="0,1,3,5,10")
    parser.add_argument("--seed", type=int, default=1994)
    parser.add_argument("--vsv-lambda", type=float, default=0.17)
    parser.add_argument("--sla-alpha", type=float, default=0.3)
    parser.add_argument("--sla-layers", default="26,30")
    parser.add_argument("--prompt", default="Please help me describe the image in detail")
    return parser.parse_args()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_jsonl(handle, row: dict[str, Any]) -> None:
    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    handle.flush()


def main() -> None:
    args = parse_args()
    prefix_lengths = sorted({int(value) for value in args.prefix_lengths.split(",")})
    if prefix_lengths != [0, 1, 3, 5, 10]:
        raise ValueError("required prefixes are 0,1,3,5,10")
    selected = load_selected_ids(args.mechanism_manifest, args.num_pairs)
    sla_indices = parse_layer_indices(args.sla_layers)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = args.output_dir / "fixed_prefix_factorial_64.jsonl"
    config_path = args.output_dir / "fixed_prefix_factorial_64_config.json"
    summary_path = args.output_dir / "fixed_prefix_factorial_64_summary.json"
    for path in (metrics_path, config_path, summary_path):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite {path}")

    config: dict[str, Any] = {
        "run_id": "E1-B1-004-fixed-prefix-factorial-64",
        "model": args.model,
        "checkpoint_path": str(args.checkpoint_path.resolve()),
        "mechanism_manifest": str(args.mechanism_manifest.resolve()),
        "data_path": str(args.data_path.resolve()),
        "selected_images": [
            {"image_id": image_id, "cohort_class": cohort_class}
            for image_id, cohort_class in selected
        ],
        "prompt": args.prompt,
        "prefix_source": "M00 greedy",
        "prefix_lengths": prefix_lengths,
        "batch_size": 1,
        "teacher_forcing": "full-prefix non-cached forward",
        "seed": args.seed,
        "vsv_lambda": args.vsv_lambda,
        "sla_alpha": args.sla_alpha,
        "sla_layers_inclusive": sla_indices,
        "methods": {
            "M00": "VSV off, SLA off",
            "M10": "VSV on, SLA off",
            "M01": "VSV off, SLA on",
            "M11": "VSV on, SLA on",
        },
    }
    write_json(config_path, config)

    completed = 0
    exceptions = 0
    model = None
    runtime_error: str | None = None
    with metrics_path.open("w", encoding="utf-8") as handle:
        try:
            myutils.seed_everything(args.seed)
            disable_torch_init()
            loader = ModelLoader(args.model, str(args.checkpoint_path.resolve()))
            model = loader.llm_model
            model.eval()
            ensure_clean_model_state(model)
            template = myutils.prepare_template(SimpleNamespace(model=args.model))
            eos_id = int(loader.tokenizer.eos_token_id)
            pad_id = int(loader.tokenizer.pad_token_id)
            config.update(
                {
                    "model_dtype": str(next(model.parameters()).dtype),
                    "eos_token_id": eos_id,
                    "pad_token_id": pad_id,
                    "torch": torch.__version__,
                    "transformers": __import__("transformers").__version__,
                }
            )
            write_json(config_path, config)

            for image_id, cohort_class in selected:
                status: dict[str, Any] = {
                    "record_type": "image_status",
                    "image_id": image_id,
                    "cohort_class": cohort_class,
                    "record_status": "ok",
                }
                try:
                    with torch.inference_mode():
                        image = prepare_image(loader, image_path_from_id(args.data_path, image_id))
                        questions, base_kwargs = prompt_kwargs(
                            loader, template, args.prompt, image
                        )
                        vsv_args = SimpleNamespace()
                        neg_kwargs = loader.prepare_neg_prompt(
                            vsv_args, questions, template=template
                        )
                        pos_kwargs = loader.prepare_pos_prompt(vsv_args, base_kwargs)
                        visual_vector, _ = obtain_vsv(
                            vsv_args, model, [[neg_kwargs, pos_kwargs]], rank=1
                        )
                        with vsv_mode(model, visual_vector, "off", args.vsv_lambda):
                            prefix_tokens = greedy_prefix(
                                model, base_kwargs, 10, eos_id, pad_id
                            )
                        if prefix_tokens.shape[1] < 10:
                            raise RuntimeError(
                                f"M00 prefix has only {prefix_tokens.shape[1]} tokens"
                            )
                        status["prefix_token_ids"] = [
                            int(value) for value in prefix_tokens[0].cpu()
                        ]

                        for prefix_length in prefix_lengths:
                            full_kwargs = extend_prefix(
                                base_kwargs, prefix_tokens[:, :prefix_length]
                            )
                            modes = {}
                            for mode in ("off", "on"):
                                with vsv_mode(
                                    model, visual_vector, mode, args.vsv_lambda
                                ):
                                    components, _ = forward_components(
                                        model,
                                        full_kwargs,
                                        sla_indices,
                                        args.sla_alpha,
                                    )
                                modes[mode] = cpu_components(components)

                            for diagnostic_mode in ("off", "on"):
                                append_jsonl(
                                    handle,
                                    {
                                        "record_type": "component_diagnostics",
                                        "image_id": image_id,
                                        "cohort_class": cohort_class,
                                        "prefix_len": prefix_length,
                                        "vsv_mode": diagnostic_mode,
                                        "hidden_layers": modes[diagnostic_mode][
                                            "hidden_diagnostics"
                                        ],
                                    },
                                )

                            for precision in ("release_native", "fp32_projection"):
                                off = modes["off"][precision]
                                on = modes["on"][precision]
                                logits = {
                                    "M00": off["final"],
                                    "M01": off["mixed"],
                                    "M10": on["final"],
                                    "M11": on["mixed"],
                                }
                                method_metrics = {}
                                for method, values in logits.items():
                                    metrics = tensor_metrics(values, eos_id)[0]
                                    method_metrics[method] = metrics
                                    append_jsonl(
                                        handle,
                                        {
                                            "record_type": "fixed_prefix_factorial",
                                            "image_id": image_id,
                                            "cohort_class": cohort_class,
                                            "prefix_len": prefix_length,
                                            "precision_path": precision,
                                            "method": method,
                                            **metrics,
                                        },
                                    )
                                interaction = (
                                    method_metrics["M11"]["eos_margin"]
                                    - method_metrics["M10"]["eos_margin"]
                                    - method_metrics["M01"]["eos_margin"]
                                    + method_metrics["M00"]["eos_margin"]
                                )
                                append_jsonl(
                                    handle,
                                    {
                                        "record_type": "factorial_interaction",
                                        "image_id": image_id,
                                        "cohort_class": cohort_class,
                                        "prefix_len": prefix_length,
                                        "precision_path": precision,
                                        "interaction_eos_margin": interaction,
                                    },
                                )
                    completed += 1
                except Exception as exc:
                    exceptions += 1
                    status.update(
                        {
                            "record_status": "exception",
                            "exception_type": type(exc).__name__,
                            "exception_message": str(exc),
                            "traceback": traceback.format_exc(),
                        }
                    )
                append_jsonl(handle, status)
                print(
                    f"PROGRESS {completed + exceptions}/{len(selected)} "
                    f"ok={completed} exceptions={exceptions}",
                    flush=True,
                )
                torch.cuda.empty_cache()
        except Exception as exc:
            runtime_error = f"{type(exc).__name__}: {exc}"
        finally:
            if model is not None:
                ensure_clean_model_state(model)

    execution_done = runtime_error is None and exceptions == 0 and completed == len(selected)
    summary = {
        "run_id": config["run_id"],
        "target_images": len(selected),
        "completed_images": completed,
        "exception_images": exceptions,
        "runtime_error": runtime_error,
        "execution_status": "DONE" if execution_done else "FAILED",
        "metrics_path": str(metrics_path),
        "config_path": str(config_path),
    }
    write_json(summary_path, summary)
    print(json.dumps(summary, indent=2))
    if not execution_done:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
