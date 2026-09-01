#!/usr/bin/env python3
"""Sanity-first fixed-prefix audit for VISTA termination instability.

Runs four images by default and checks:
1. VSV-off vs release wrapper(lambda=0) vs strict wrapper no-op.
2. batch=1 vs five identical rows.
3. cached vs non-cached teacher-forced prefixes.
4. the 2x2 VSV/SLA EOS-margin factorial at fixed prefixes.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator

import torch
import torch.nn as nn
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import myutils
from llava.utils import disable_torch_init
from llm_layers import (
    VSVLayer,
    add_vsv_layers,
    find_module,
    get_layers,
    remove_vsv_layers,
)
from model_loader import ModelLoader
from steering_vector import obtain_vsv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mechanism-manifest", type=Path, required=True)
    parser.add_argument("--data-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="llava-1.5")
    parser.add_argument("--num-pairs", type=int, default=2)
    parser.add_argument("--prefix-lengths", default="0,1,3")
    parser.add_argument("--max-prefix-tokens", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1994)
    parser.add_argument("--vsv-lambda", type=float, default=0.17)
    parser.add_argument("--sla-alpha", type=float, default=0.3)
    parser.add_argument("--sla-layers", default="26,30")
    parser.add_argument("--batch-repeat", type=int, default=5)
    parser.add_argument("--tolerance", type=float, default=2e-3)
    parser.add_argument(
        "--prompt", default="Please help me describe the image in detail"
    )
    return parser.parse_args()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_jsonl(handle, row: dict[str, Any]) -> None:
    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    handle.flush()


def load_selected_ids(path: Path, num_pairs: int) -> list[tuple[int, str]]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    pairs = manifest["pairs"]
    if num_pairs > len(pairs):
        raise ValueError(f"requested {num_pairs} pairs but manifest has {len(pairs)}")
    selected: list[tuple[int, str]] = []
    for pair in pairs[:num_pairs]:
        selected.append((int(pair["collapse_image_id"]), "collapse"))
        selected.append((int(pair["control_image_id"]), "control"))
    return selected


def image_path_from_id(data_path: Path, image_id: int) -> Path:
    path = data_path / f"COCO_val2014_000000{image_id:06d}.jpg"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def prepare_image(model_loader: ModelLoader, image_path: Path) -> dict[str, torch.Tensor]:
    image = Image.open(image_path).convert("RGB")
    processed = model_loader.image_processor(image, return_tensors="pt")
    # Match DataLoader(batch_size=1) around the processor's own batch dimension.
    return {"pixel_values": processed["pixel_values"].unsqueeze(0)}


def ensure_clean_model_state(model: nn.Module) -> None:
    for attr in ("logits_aug", "logits_layers", "logits_alpha"):
        if hasattr(model, attr):
            delattr(model, attr)
    remove_vsv_layers(model)


def install_strict_noop(model: nn.Module) -> None:
    """Install the same Sequential wrapper shape but return MLP output exactly."""
    for layer in get_layers(model):
        original_mlp = find_module(layer, ["mlp", "feedforward", "ffn"])
        layer.mlp = nn.Sequential(original_mlp, VSVLayer(None, [0.0]))


@contextlib.contextmanager
def vsv_mode(
    model: nn.Module,
    visual_vector: torch.Tensor,
    mode: str,
    lam: float,
) -> Iterator[None]:
    ensure_clean_model_state(model)
    try:
        if mode == "off":
            pass
        elif mode == "on":
            add_vsv_layers(
                model,
                torch.stack([visual_vector], dim=1).to("cuda"),
                [lam],
            )
        elif mode == "release_zero":
            add_vsv_layers(
                model,
                torch.stack([visual_vector], dim=1).to("cuda"),
                [0.0],
            )
        elif mode == "strict_zero":
            install_strict_noop(model)
        else:
            raise ValueError(f"unknown VSV mode: {mode}")
        yield
    finally:
        ensure_clean_model_state(model)


def layer_indices(spec: str) -> list[int]:
    start, end = (int(value) for value in spec.split(","))
    if start < 0 or end < start:
        raise ValueError(f"invalid SLA layer range: {spec}")
    return list(range(start, end + 1))


def components_from_output(
    model: nn.Module,
    output,
    sla_indices: list[int],
) -> tuple[torch.Tensor, torch.Tensor]:
    final = output.logits[:, -1, :].float()
    hidden_states = output.hidden_states[1:]
    if max(sla_indices) >= len(hidden_states):
        raise IndexError(
            f"SLA layer {max(sla_indices)} unavailable; got {len(hidden_states)} states"
        )
    augmented = torch.stack(
        [model.lm_head(hidden_states[index][:, -1, :]).float() for index in sla_indices]
    ).mean(dim=0)
    return final, augmented


def forward_components(
    model: nn.Module,
    model_kwargs: dict[str, torch.Tensor],
    sla_indices: list[int],
    use_cache: bool = False,
    past_key_values=None,
) -> tuple[torch.Tensor, torch.Tensor, Any]:
    kwargs = dict(model_kwargs)
    if past_key_values is not None:
        kwargs["past_key_values"] = past_key_values
    output = model(
        use_cache=use_cache,
        output_hidden_states=True,
        return_dict=True,
        **kwargs,
    )
    final, augmented = components_from_output(model, output, sla_indices)
    return final, augmented, output.past_key_values


def mixed_logits(final: torch.Tensor, augmented: torch.Tensor, alpha: float) -> torch.Tensor:
    return (1.0 - alpha) * final + alpha * augmented


def tensor_metrics(logits: torch.Tensor, eos_id: int) -> list[dict[str, Any]]:
    logits = logits.float()
    log_probs = torch.log_softmax(logits, dim=-1)
    probs = log_probs.exp()
    eos_logits = logits[:, eos_id]
    eos_probs = probs[:, eos_id]
    ranks = 1 + (logits > eos_logits[:, None]).sum(dim=-1)
    non_eos = logits.clone()
    non_eos[:, eos_id] = -torch.inf
    top_values, top_ids = non_eos.max(dim=-1)
    entropy = -(probs * log_probs).sum(dim=-1)
    topk_values, topk_ids = torch.topk(logits, k=5, dim=-1)
    rows: list[dict[str, Any]] = []
    for index in range(logits.shape[0]):
        rows.append(
            {
                "eos_logit": float(eos_logits[index]),
                "eos_prob": float(eos_probs[index]),
                "eos_rank": int(ranks[index]),
                "eos_margin": float(eos_logits[index] - top_values[index]),
                "top_non_eos_id": int(top_ids[index]),
                "top_non_eos_logit": float(top_values[index]),
                "entropy": float(entropy[index]),
                "logit_mean": float(logits[index].mean()),
                "logit_std": float(logits[index].std()),
                "logit_rms": float(logits[index].square().mean().sqrt()),
                "top5_ids": [int(value) for value in topk_ids[index].tolist()],
                "top5_logits": [float(value) for value in topk_values[index].tolist()],
            }
        )
    return rows


def max_abs_diff(left: torch.Tensor, right: torch.Tensor) -> float:
    return float((left.float() - right.float()).abs().max())


def prompt_kwargs(
    model_loader: ModelLoader,
    template: str,
    prompt: str,
    image: dict[str, torch.Tensor],
) -> tuple[list[str], dict[str, torch.Tensor]]:
    questions, kwargs = model_loader.prepare_inputs_for_model(
        template, [prompt], image
    )
    kwargs["attention_mask"] = torch.ones_like(kwargs["input_ids"])
    return questions, kwargs


def extend_prefix(
    base_kwargs: dict[str, torch.Tensor], prefix: torch.Tensor
) -> dict[str, torch.Tensor]:
    input_ids = torch.cat([base_kwargs["input_ids"], prefix], dim=1)
    return {
        "input_ids": input_ids,
        "attention_mask": torch.ones_like(input_ids),
        "images": base_kwargs["images"],
    }


def repeat_kwargs(model_kwargs: dict[str, torch.Tensor], count: int) -> dict[str, torch.Tensor]:
    return {
        "input_ids": model_kwargs["input_ids"].repeat(count, 1),
        "attention_mask": model_kwargs["attention_mask"].repeat(count, 1),
        "images": model_kwargs["images"].repeat(count, 1, 1, 1),
    }


def greedy_prefix(
    model: nn.Module,
    base_kwargs: dict[str, torch.Tensor],
    max_new_tokens: int,
    eos_id: int,
) -> torch.Tensor:
    input_length = base_kwargs["input_ids"].shape[1]
    output = model.generate(
        do_sample=False,
        num_beams=1,
        max_new_tokens=max_new_tokens,
        use_cache=True,
        return_dict_in_generate=False,
        **base_kwargs,
    )
    generated = output[:, input_length:]
    eos_positions = torch.where(generated[0] == eos_id)[0]
    if len(eos_positions):
        generated = generated[:, : int(eos_positions[0])]
    return generated


def cached_components(
    model: nn.Module,
    base_kwargs: dict[str, torch.Tensor],
    prefix: torch.Tensor,
    sla_indices: list[int],
) -> tuple[torch.Tensor, torch.Tensor]:
    final, augmented, past = forward_components(
        model, base_kwargs, sla_indices, use_cache=True
    )
    if prefix.shape[1] == 0:
        return final, augmented
    for token_index in range(prefix.shape[1]):
        token = prefix[:, token_index : token_index + 1]
        past_length = past[-1][-1].shape[-2]
        step_kwargs = {
            "input_ids": token,
            "attention_mask": torch.ones(
                (token.shape[0], past_length + 1),
                dtype=torch.long,
                device=token.device,
            ),
            "images": base_kwargs["images"],
        }
        final, augmented, past = forward_components(
            model,
            step_kwargs,
            sla_indices,
            use_cache=True,
            past_key_values=past,
        )
    return final, augmented


def main() -> None:
    args = parse_args()
    if args.model != "llava-1.5":
        raise ValueError("first sanity implementation currently supports llava-1.5 only")
    prefix_lengths = sorted({int(value) for value in args.prefix_lengths.split(",")})
    if not prefix_lengths or min(prefix_lengths) < 0:
        raise ValueError("prefix lengths must be non-negative")
    if max(prefix_lengths) > args.max_prefix_tokens:
        raise ValueError("max prefix length exceeds --max-prefix-tokens")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = args.output_dir / "sanity_metrics.jsonl"
    summary_path = args.output_dir / "sanity_summary.json"
    config_path = args.output_dir / "sanity_config.json"
    if metrics_path.exists() or summary_path.exists():
        raise FileExistsError(
            f"refusing to overwrite existing sanity output in {args.output_dir}"
        )

    myutils.seed_everything(args.seed)
    disable_torch_init()
    model_loader = ModelLoader(args.model)
    model = model_loader.llm_model
    model.eval()
    ensure_clean_model_state(model)
    template = myutils.prepare_template(SimpleNamespace(model=args.model))
    eos_id = int(model_loader.tokenizer.eos_token_id)
    sla_indices = layer_indices(args.sla_layers)
    selected = load_selected_ids(args.mechanism_manifest, args.num_pairs)

    config = {
        "model": args.model,
        "checkpoint": str(Path("/workspace/download_models/llava-v1.5-7b")),
        "mechanism_manifest": str(args.mechanism_manifest.resolve()),
        "data_path": str(args.data_path.resolve()),
        "selected": [
            {"image_id": image_id, "class": cohort_class}
            for image_id, cohort_class in selected
        ],
        "prompt": args.prompt,
        "prefix_lengths": prefix_lengths,
        "seed": args.seed,
        "vsv_lambda": args.vsv_lambda,
        "sla_alpha": args.sla_alpha,
        "sla_layers": sla_indices,
        "batch_repeat": args.batch_repeat,
        "tolerance": args.tolerance,
        "eos_id": eos_id,
    }
    write_json(config_path, config)

    no_op_diffs: list[dict[str, Any]] = []
    batch_diffs: list[dict[str, Any]] = []
    cache_diffs: list[dict[str, Any]] = []
    interaction_rows: list[dict[str, Any]] = []

    vsv_args = SimpleNamespace()
    with metrics_path.open("w", encoding="utf-8") as metrics_handle:
        for image_id, cohort_class in selected:
            image_path = image_path_from_id(args.data_path, image_id)
            image = prepare_image(model_loader, image_path)
            questions, base_kwargs = prompt_kwargs(
                model_loader, template, args.prompt, image
            )
            neg_kwargs = model_loader.prepare_neg_prompt(
                vsv_args, questions, template=template
            )
            pos_kwargs = model_loader.prepare_pos_prompt(vsv_args, base_kwargs)
            visual_vector, _ = obtain_vsv(
                vsv_args, model, [[neg_kwargs, pos_kwargs]], rank=1
            )

            with vsv_mode(model, visual_vector, "off", args.vsv_lambda):
                prefix_tokens = greedy_prefix(
                    model, base_kwargs, args.max_prefix_tokens, eos_id
                )
            if prefix_tokens.shape[1] < max(prefix_lengths):
                raise RuntimeError(
                    f"image {image_id}: baseline generated only {prefix_tokens.shape[1]} "
                    f"tokens, need {max(prefix_lengths)}"
                )

            # Strict no-op controls at prompt step.
            no_op_components: dict[str, tuple[torch.Tensor, torch.Tensor]] = {}
            for mode in ("off", "release_zero", "strict_zero"):
                with vsv_mode(model, visual_vector, mode, args.vsv_lambda):
                    final, augmented, _ = forward_components(
                        model, base_kwargs, sla_indices
                    )
                no_op_components[mode] = (final.cpu(), augmented.cpu())
            for component_index, component_name in enumerate(("final", "augmented")):
                reference = no_op_components["off"][component_index]
                for mode in ("release_zero", "strict_zero"):
                    diff = max_abs_diff(reference, no_op_components[mode][component_index])
                    row = {
                        "image_id": image_id,
                        "cohort_class": cohort_class,
                        "check": "strict_noop",
                        "component": component_name,
                        "mode": mode,
                        "max_abs_diff": diff,
                        "tolerance": args.tolerance,
                        "passed": diff <= args.tolerance,
                    }
                    no_op_diffs.append(row)
                    append_jsonl(metrics_handle, row)

            for prefix_length in prefix_lengths:
                prefix = prefix_tokens[:, :prefix_length]
                full_kwargs = extend_prefix(base_kwargs, prefix)
                components: dict[str, tuple[torch.Tensor, torch.Tensor]] = {}
                for mode in ("off", "on"):
                    with vsv_mode(model, visual_vector, mode, args.vsv_lambda):
                        final, augmented, _ = forward_components(
                            model, full_kwargs, sla_indices
                        )
                    components[mode] = (final.cpu(), augmented.cpu())

                final0, augmented0 = components["off"]
                final1, augmented1 = components["on"]
                method_logits = {
                    "M00": final0,
                    "M01": mixed_logits(final0, augmented0, args.sla_alpha),
                    "M10": final1,
                    "M11": mixed_logits(final1, augmented1, args.sla_alpha),
                }
                method_metrics: dict[str, dict[str, Any]] = {}
                for method, logits in method_logits.items():
                    values = tensor_metrics(logits, eos_id)[0]
                    method_metrics[method] = values
                    append_jsonl(
                        metrics_handle,
                        {
                            "image_id": image_id,
                            "cohort_class": cohort_class,
                            "check": "fixed_prefix_factorial",
                            "prefix_len": prefix_length,
                            "method": method,
                            **values,
                        },
                    )
                interaction = (
                    method_metrics["M11"]["eos_margin"]
                    - method_metrics["M10"]["eos_margin"]
                    - method_metrics["M01"]["eos_margin"]
                    + method_metrics["M00"]["eos_margin"]
                )
                interaction_row = {
                    "image_id": image_id,
                    "cohort_class": cohort_class,
                    "prefix_len": prefix_length,
                    "interaction_eos_margin": interaction,
                }
                interaction_rows.append(interaction_row)
                append_jsonl(
                    metrics_handle,
                    {"check": "factorial_interaction", **interaction_row},
                )

                # Batch repeat control at prompt step for both VSV states.
                if prefix_length == 0:
                    repeated_kwargs = repeat_kwargs(full_kwargs, args.batch_repeat)
                    for mode in ("off", "on"):
                        with vsv_mode(model, visual_vector, mode, args.vsv_lambda):
                            batch_final, batch_augmented, _ = forward_components(
                                model, repeated_kwargs, sla_indices
                            )
                        single_final, single_augmented = components[mode]
                        for component_name, single, repeated in (
                            ("final", single_final, batch_final.cpu()),
                            ("augmented", single_augmented, batch_augmented.cpu()),
                        ):
                            reference = single.repeat(args.batch_repeat, 1)
                            diff = max_abs_diff(reference, repeated)
                            row = {
                                "image_id": image_id,
                                "cohort_class": cohort_class,
                                "check": "batch_repeat",
                                "vsv_mode": mode,
                                "component": component_name,
                                "repeat": args.batch_repeat,
                                "max_abs_diff": diff,
                                "tolerance": args.tolerance,
                                "passed": diff <= args.tolerance,
                            }
                            batch_diffs.append(row)
                            append_jsonl(metrics_handle, row)

                # Cache consistency for non-empty fixed prefixes.
                if prefix_length > 0:
                    for mode in ("off", "on"):
                        with vsv_mode(model, visual_vector, mode, args.vsv_lambda):
                            cached_final, cached_augmented = cached_components(
                                model, base_kwargs, prefix, sla_indices
                            )
                        full_final, full_augmented = components[mode]
                        for component_name, full, cached in (
                            ("final", full_final, cached_final.cpu()),
                            ("augmented", full_augmented, cached_augmented.cpu()),
                        ):
                            diff = max_abs_diff(full, cached)
                            row = {
                                "image_id": image_id,
                                "cohort_class": cohort_class,
                                "check": "cache_consistency",
                                "vsv_mode": mode,
                                "component": component_name,
                                "prefix_len": prefix_length,
                                "max_abs_diff": diff,
                                "tolerance": args.tolerance,
                                "passed": diff <= args.tolerance,
                            }
                            cache_diffs.append(row)
                            append_jsonl(metrics_handle, row)

            torch.cuda.empty_cache()

    ensure_clean_model_state(model)
    all_checks = no_op_diffs + batch_diffs + cache_diffs
    failures = [row for row in all_checks if not row["passed"]]
    interactions = [row["interaction_eos_margin"] for row in interaction_rows]
    summary = {
        "status": "PASS" if not failures else "FAIL",
        "selected_images": len(selected),
        "metric_rows": sum(1 for _ in metrics_path.open(encoding="utf-8")),
        "hard_check_rows": len(all_checks),
        "hard_check_failures": len(failures),
        "max_noop_diff": max(row["max_abs_diff"] for row in no_op_diffs),
        "max_batch_repeat_diff": max(row["max_abs_diff"] for row in batch_diffs),
        "max_cache_diff": max(row["max_abs_diff"] for row in cache_diffs),
        "interaction_count": len(interactions),
        "interaction_mean": sum(interactions) / len(interactions),
        "interaction_min": min(interactions),
        "interaction_max": max(interactions),
        "failures": failures,
        "outputs": {
            "config": str(config_path),
            "metrics": str(metrics_path),
        },
    }
    if any(math.isnan(value) for value in interactions):
        summary["status"] = "FAIL"
        summary["nan_interaction"] = True
    write_json(summary_path, summary)
    print(json.dumps(summary, indent=2))
    if summary["status"] != "PASS":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
