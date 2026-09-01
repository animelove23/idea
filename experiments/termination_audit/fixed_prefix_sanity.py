#!/usr/bin/env python3
"""Four-image fixed-prefix sanity gate for the VISTA termination audit."""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Iterator

import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import myutils
from llava.utils import disable_torch_init
from llm_layers import VSVLayer, add_vsv_layers, find_module, get_layers, remove_vsv_layers
from model_loader import ModelLoader
from experiments.termination_audit.provenance import complete_checkpoint_provenance
from steering_vector import obtain_vsv


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mechanism-manifest", type=Path, required=True)
    parser.add_argument("--data-path", type=Path, required=True)
    parser.add_argument("--checkpoint-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="llava-1.5")
    parser.add_argument("--num-pairs", type=int, default=2)
    parser.add_argument("--prefix-lengths", default="0,1,3,5,10")
    parser.add_argument("--max-prefix-tokens", type=int, default=10)
    parser.add_argument("--seed", type=int, default=1994)
    parser.add_argument("--vsv-lambda", type=float, default=0.17)
    parser.add_argument("--sla-alpha", type=float, default=0.3)
    parser.add_argument("--sla-layers", default="26,30")
    parser.add_argument("--batch-repeat", type=int, default=5)
    parser.add_argument("--tolerance", type=float, default=2e-3)
    parser.add_argument("--prompt", default="Please help me describe the image in detail")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_record(path: Path) -> dict[str, Any]:
    return {"path": str(path.resolve()), "size": path.stat().st_size, "sha256": sha256_file(path)}


def checkpoint_records(checkpoint_path: Path) -> list[dict[str, Any]]:
    patterns = ("*.json", "*.safetensors", "*.bin")
    files = sorted({path for pattern in patterns for path in checkpoint_path.glob(pattern)})
    if not files:
        raise FileNotFoundError(f"no checkpoint/config files under {checkpoint_path}")
    return [source_record(path) for path in files]


def code_provenance() -> dict[str, Any]:
    tracked = [
        Path(__file__).resolve(),
        PROJECT_ROOT / "model_loader.py",
        PROJECT_ROOT / "llm_layers.py",
        PROJECT_ROOT / "steering_vector.py",
        PROJECT_ROOT / "llava/model/language_model/llava_llama.py",
        PROJECT_ROOT / "llava/model/llava_arch.py",
        PROJECT_ROOT / "experiments/termination_audit/provenance.py",
    ]
    commit = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "rev-parse", "HEAD"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "status", "--porcelain"],
        check=True,
        text=True,
        capture_output=True,
    ).stdout.splitlines()
    return {
        "git_commit": commit,
        "git_dirty": bool(dirty),
        "git_status": dirty,
        "files": [source_record(path) for path in tracked],
    }


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def append_jsonl(handle, row: dict[str, Any]) -> None:
    handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    handle.flush()


def load_selected_ids(path: Path, num_pairs: int) -> list[tuple[int, str]]:
    manifest = json.loads(path.read_text(encoding="utf-8"))
    pairs = manifest["pairs"]
    if num_pairs < 1 or num_pairs > len(pairs):
        raise ValueError(f"requested {num_pairs} pairs but manifest has {len(pairs)}")
    selected: list[tuple[int, str]] = []
    for pair in pairs[:num_pairs]:
        selected.extend(
            [
                (int(pair["collapse_image_id"]), "collapse"),
                (int(pair["control_image_id"]), "control"),
            ]
        )
    return selected


def image_path_from_id(data_path: Path, image_id: int) -> Path:
    path = data_path / f"COCO_val2014_000000{image_id:06d}.jpg"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def prepare_image(model_loader: ModelLoader, image_path: Path) -> dict[str, torch.Tensor]:
    with Image.open(image_path) as image:
        processed = model_loader.image_processor(image.convert("RGB"), return_tensors="pt")
    return {"pixel_values": processed["pixel_values"].unsqueeze(0)}


def ensure_clean_model_state(model: nn.Module) -> None:
    for attr in ("logits_aug", "logits_layers", "logits_alpha"):
        if hasattr(model, attr):
            delattr(model, attr)
    remove_vsv_layers(model)


def install_strict_noop(model: nn.Module) -> None:
    for layer in get_layers(model):
        original_mlp = find_module(layer, ["mlp", "feedforward", "ffn"])
        layer.mlp = nn.Sequential(original_mlp, VSVLayer(None, [0.0]))


@contextlib.contextmanager
def vsv_mode(model: nn.Module, visual_vector: torch.Tensor, mode: str, lam: float) -> Iterator[None]:
    ensure_clean_model_state(model)
    try:
        if mode == "off":
            pass
        elif mode == "on":
            add_vsv_layers(model, torch.stack([visual_vector], dim=1).to("cuda"), [lam])
        elif mode == "release_zero":
            add_vsv_layers(model, torch.stack([visual_vector], dim=1).to("cuda"), [0.0])
        elif mode == "strict_zero":
            install_strict_noop(model)
        else:
            raise ValueError(f"unknown VSV mode: {mode}")
        yield
    finally:
        ensure_clean_model_state(model)


def parse_layer_indices(spec: str) -> list[int]:
    parts = [int(value) for value in spec.split(",")]
    if len(parts) != 2 or parts[0] < 0 or parts[1] < parts[0]:
        raise ValueError(f"invalid inclusive SLA layer range: {spec}")
    return list(range(parts[0], parts[1] + 1))


def projection_components(
    model: nn.Module, output: Any, sla_indices: list[int], sla_alpha: float
) -> dict[str, dict[str, Any]]:
    hidden_states = output.hidden_states[1:]
    if not hidden_states or max(sla_indices) >= len(hidden_states):
        raise IndexError(
            f"SLA layer {max(sla_indices)} unavailable; got {len(hidden_states)} decoder states"
        )

    final_native = output.logits[:, -1, :]
    layer_native = [model.lm_head(hidden_states[index][:, -1, :]) for index in sla_indices]
    augmented_native = torch.stack(layer_native, dim=0).mean(dim=0)
    mixed_native = sla_alpha * augmented_native + (1.0 - sla_alpha) * final_native

    weight = model.lm_head.weight.float()
    bias = model.lm_head.bias.float() if model.lm_head.bias is not None else None
    final_fp32 = F.linear(output.hidden_states[-1][:, -1, :].float(), weight, bias)
    layer_fp32 = [
        F.linear(hidden_states[index][:, -1, :].float(), weight, bias)
        for index in sla_indices
    ]
    augmented_fp32 = torch.stack(layer_fp32, dim=0).mean(dim=0)
    mixed_fp32 = sla_alpha * augmented_fp32 + (1.0 - sla_alpha) * final_fp32

    hidden_diagnostics = []
    for index in sla_indices:
        hidden = hidden_states[index][:, -1, :].float()
        hidden_diagnostics.append(
            {
                "layer_index": index,
                "hidden_l2": [float(value) for value in hidden.norm(dim=-1).cpu()],
                "hidden_rms": [float(value) for value in hidden.square().mean(dim=-1).sqrt().cpu()],
                "native_logits": logit_scale(layer_native[sla_indices.index(index)]),
                "fp32_logits": logit_scale(layer_fp32[sla_indices.index(index)]),
            }
        )

    return {
        "release_native": {
            "final": final_native,
            "augmented": augmented_native,
            "mixed": mixed_native,
            "layers": layer_native,
            "dtype": str(final_native.dtype),
        },
        "fp32_projection": {
            "final": final_fp32,
            "augmented": augmented_fp32,
            "mixed": mixed_fp32,
            "layers": layer_fp32,
            "dtype": str(final_fp32.dtype),
        },
        "hidden_diagnostics": hidden_diagnostics,
    }


def logit_scale(logits: torch.Tensor) -> dict[str, list[float]]:
    values = logits.float()
    return {
        "mean": [float(value) for value in values.mean(dim=-1).cpu()],
        "std": [float(value) for value in values.std(dim=-1).cpu()],
        "rms": [float(value) for value in values.square().mean(dim=-1).sqrt().cpu()],
    }


def forward_components(
    model: nn.Module,
    model_kwargs: dict[str, torch.Tensor],
    sla_indices: list[int],
    sla_alpha: float,
    use_cache: bool = False,
    past_key_values: Any = None,
) -> tuple[dict[str, dict[str, Any]], Any]:
    kwargs = dict(model_kwargs)
    if past_key_values is not None:
        kwargs["past_key_values"] = past_key_values
    output = model(
        use_cache=use_cache,
        output_hidden_states=True,
        return_dict=True,
        **kwargs,
    )
    return projection_components(model, output, sla_indices, sla_alpha), output.past_key_values


def mixed_logits(final: torch.Tensor, augmented: torch.Tensor, alpha: float) -> torch.Tensor:
    return (1.0 - alpha) * final + alpha * augmented


def tensor_metrics(logits: torch.Tensor, eos_id: int) -> list[dict[str, Any]]:
    values = logits.float()
    log_probs = torch.log_softmax(values, dim=-1)
    probs = log_probs.exp()
    eos_logits = values[:, eos_id]
    eos_probs = probs[:, eos_id]
    ranks = 1 + (values > eos_logits[:, None]).sum(dim=-1)
    non_eos = values.clone()
    non_eos[:, eos_id] = -torch.inf
    top_values, top_ids = non_eos.max(dim=-1)
    entropy = -(probs * log_probs).sum(dim=-1)
    topk_values, topk_ids = torch.topk(values, k=5, dim=-1)
    rows = []
    for index in range(values.shape[0]):
        rows.append(
            {
                "eos_logit": float(eos_logits[index]),
                "eos_prob": float(eos_probs[index]),
                "eos_rank": int(ranks[index]),
                "eos_margin": float(eos_logits[index] - top_values[index]),
                "top_non_eos_id": int(top_ids[index]),
                "top_non_eos_logit": float(top_values[index]),
                "entropy": float(entropy[index]),
                "logit_mean": float(values[index].mean()),
                "logit_std": float(values[index].std()),
                "logit_rms": float(values[index].square().mean().sqrt()),
                "top5_ids": [int(value) for value in topk_ids[index].tolist()],
                "top5_logits": [float(value) for value in topk_values[index].tolist()],
            }
        )
    return rows


def max_abs_diff(left: torch.Tensor, right: torch.Tensor) -> float:
    return float((left.float() - right.float()).abs().max())


def decision_stability(left: torch.Tensor, right: torch.Tensor, eos_id: int) -> dict[str, Any]:
    """Report whether numeric drift changes EOS-relevant decoding decisions.

    This is diagnostic only: the original all-vocabulary tolerance remains
    reported separately rather than being relaxed post hoc.
    """
    left_metrics = tensor_metrics(left, eos_id)
    right_metrics = tensor_metrics(right, eos_id)
    return {
        "max_eos_logit_diff": max(abs(a["eos_logit"] - b["eos_logit"]) for a, b in zip(left_metrics, right_metrics)),
        "max_eos_margin_diff": max(abs(a["eos_margin"] - b["eos_margin"]) for a, b in zip(left_metrics, right_metrics)),
        "max_eos_rank_diff": max(abs(a["eos_rank"] - b["eos_rank"]) for a, b in zip(left_metrics, right_metrics)),
        "all_eos_rank_equal": all(a["eos_rank"] == b["eos_rank"] for a, b in zip(left_metrics, right_metrics)),
        "all_top_non_eos_equal": all(a["top_non_eos_id"] == b["top_non_eos_id"] for a, b in zip(left_metrics, right_metrics)),
        "all_top5_ids_equal": all(a["top5_ids"] == b["top5_ids"] for a, b in zip(left_metrics, right_metrics)),
    }


def prompt_kwargs(
    model_loader: ModelLoader, template: str, prompt: str, image: dict[str, torch.Tensor]
) -> tuple[list[str], dict[str, torch.Tensor]]:
    questions, kwargs = model_loader.prepare_inputs_for_model(template, [prompt], image)
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
    pad_id: int,
) -> torch.Tensor:
    input_length = base_kwargs["input_ids"].shape[1]
    output = model.generate(
        do_sample=False,
        num_beams=1,
        max_new_tokens=max_new_tokens,
        use_cache=True,
        eos_token_id=eos_id,
        pad_token_id=pad_id,
        early_stopping=False,
        length_penalty=1.0,
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
    sla_alpha: float,
) -> dict[str, dict[str, Any]]:
    components, past = forward_components(model, base_kwargs, sla_indices, sla_alpha, use_cache=True)
    if prefix.shape[1] == 0:
        return components
    for token_index in range(prefix.shape[1]):
        token = prefix[:, token_index : token_index + 1]
        past_length = past[-1][-1].shape[-2]
        step_kwargs = {
            "input_ids": token,
            "attention_mask": torch.ones(
                (token.shape[0], past_length + 1), dtype=torch.long, device=token.device
            ),
            "images": base_kwargs["images"],
        }
        components, past = forward_components(
            model, step_kwargs, sla_indices, sla_alpha, use_cache=True, past_key_values=past
        )
    return components


def cpu_components(components: dict[str, dict[str, Any]]) -> dict[str, dict[str, Any]]:
    copied: dict[str, dict[str, Any]] = {}
    for precision in ("release_native", "fp32_projection"):
        copied[precision] = {
            "final": components[precision]["final"].cpu(),
            "augmented": components[precision]["augmented"].cpu(),
            "mixed": components[precision]["mixed"].cpu(),
            "layers": [value.cpu() for value in components[precision]["layers"]],
            "dtype": components[precision]["dtype"],
        }
    copied["hidden_diagnostics"] = components["hidden_diagnostics"]
    return copied


def component_pairs(components: dict[str, dict[str, Any]]):
    for precision in ("release_native", "fp32_projection"):
        yield precision, "final", components[precision]["final"]
        yield precision, "augmented", components[precision]["augmented"]
        yield precision, "mixed", components[precision]["mixed"]


def main() -> None:
    args = parse_args()
    if args.model != "llava-1.5":
        raise ValueError("fixed-prefix sanity currently supports llava-1.5 only")
    prefix_lengths = sorted({int(value) for value in args.prefix_lengths.split(",")})
    required_prefixes = {0, 1, 3, 5, 10}
    if set(prefix_lengths) != required_prefixes:
        raise ValueError(f"sanity gate requires prefix lengths {sorted(required_prefixes)}")
    if max(prefix_lengths) > args.max_prefix_tokens:
        raise ValueError("max prefix length exceeds --max-prefix-tokens")
    if args.batch_repeat < 2:
        raise ValueError("--batch-repeat must be at least 2")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_id = f"E1-B1-sanity-{run_stamp}"
    metrics_path = args.output_dir / f"{run_id}_metrics.jsonl"
    summary_path = args.output_dir / f"{run_id}_summary.json"
    config_path = args.output_dir / f"{run_id}_config.json"
    for path in (metrics_path, summary_path, config_path):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite existing output: {path}")

    selected = load_selected_ids(args.mechanism_manifest, args.num_pairs)
    sla_indices = parse_layer_indices(args.sla_layers)
    config: dict[str, Any] = {
        "run_id": run_id,
        "model": args.model,
        "mechanism_manifest": source_record(args.mechanism_manifest),
        "data_path": str(args.data_path.resolve()),
        "checkpoint_path": str(args.checkpoint_path.resolve()),
        "code": code_provenance(),
        "selected": [
            {"image_id": image_id, "cohort_class": cohort_class}
            for image_id, cohort_class in selected
        ],
        "prompt": args.prompt,
        "prefix_source": "M00 greedy, VSV off, SLA off",
        "prefix_lengths": prefix_lengths,
        "seed": args.seed,
        "vsv_lambda": args.vsv_lambda,
        "sla_alpha": args.sla_alpha,
        "sla_layers_inclusive": sla_indices,
        "batch_repeat": args.batch_repeat,
        "tolerance": args.tolerance,
        "precision_paths": {
            "release_native": "model lm_head and arithmetic in release-native dtype",
            "fp32_projection": "hidden states and lm_head weights explicitly cast to FP32",
        },
        "generation": {
            "do_sample": False,
            "num_beams": 1,
            "max_new_tokens": args.max_prefix_tokens,
            "early_stopping": False,
            "length_penalty": 1.0,
            "min_new_tokens": None,
            "use_cache": True,
        },
        "dependencies": {"python": sys.version.split()[0], "torch": torch.__version__},
    }
    write_json(config_path, config)

    no_op_rows: list[dict[str, Any]] = []
    batch_rows: list[dict[str, Any]] = []
    cache_rows: list[dict[str, Any]] = []
    interaction_rows: list[dict[str, Any]] = []
    image_statuses: list[dict[str, Any]] = []
    runtime_error: str | None = None
    model = None

    with metrics_path.open("w", encoding="utf-8") as metrics_handle:
        try:
            myutils.seed_everything(args.seed)
            disable_torch_init()
            model_loader = ModelLoader(args.model, str(args.checkpoint_path.resolve()))
            model = model_loader.llm_model
            model.eval()
            ensure_clean_model_state(model)
            template = myutils.prepare_template(SimpleNamespace(model=args.model))
            eos_id = int(model_loader.tokenizer.eos_token_id)
            pad_id = int(model_loader.tokenizer.pad_token_id)
            config["generation"].update({"eos_token_id": eos_id, "pad_token_id": pad_id})
            config["dependencies"]["transformers"] = __import__("transformers").__version__
            config["model_dtype"] = str(next(model.parameters()).dtype)
            write_json(config_path, config)

            for image_id, cohort_class in selected:
                status: dict[str, Any] = {
                    "image_id": image_id,
                    "cohort_class": cohort_class,
                    "record_status": "ok",
                }
                try:
                    with torch.inference_mode():
                        image = prepare_image(model_loader, image_path_from_id(args.data_path, image_id))
                        questions, base_kwargs = prompt_kwargs(
                            model_loader, template, args.prompt, image
                        )
                        vsv_args = SimpleNamespace()
                        neg_kwargs = model_loader.prepare_neg_prompt(
                            vsv_args, questions, template=template
                        )
                        pos_kwargs = model_loader.prepare_pos_prompt(vsv_args, base_kwargs)
                        visual_vector, _ = obtain_vsv(
                            vsv_args, model, [[neg_kwargs, pos_kwargs]], rank=1
                        )
                        with vsv_mode(model, visual_vector, "off", args.vsv_lambda):
                            prefix_tokens = greedy_prefix(
                                model,
                                base_kwargs,
                                args.max_prefix_tokens,
                                eos_id,
                                pad_id,
                            )
                        status["available_prefix_tokens"] = int(prefix_tokens.shape[1])
                        status["prefix_token_ids"] = [int(value) for value in prefix_tokens[0].cpu()]
                        if prefix_tokens.shape[1] < max(prefix_lengths):
                            status.update(
                                {
                                    "record_status": "early_eos_before_required_prefix",
                                    "required_prefix_tokens": max(prefix_lengths),
                                }
                            )
                            append_jsonl(metrics_handle, {"check": "image_status", **status})
                            image_statuses.append(status)
                            continue

                        for prefix_length in prefix_lengths:
                            prefix = prefix_tokens[:, :prefix_length]
                            full_kwargs = extend_prefix(base_kwargs, prefix)

                            modes: dict[str, dict[str, dict[str, Any]]] = {}
                            for mode in ("off", "on", "release_zero", "strict_zero"):
                                with vsv_mode(model, visual_vector, mode, args.vsv_lambda):
                                    components, _ = forward_components(
                                        model, full_kwargs, sla_indices, args.sla_alpha
                                    )
                                modes[mode] = cpu_components(components)

                            for zero_mode in ("release_zero", "strict_zero"):
                                reference = modes["off"]
                                candidate = modes[zero_mode]
                                for precision, component, ref_value in component_pairs(reference):
                                    diff = max_abs_diff(
                                        ref_value, candidate[precision][component]
                                    )
                                    row = {
                                        "image_id": image_id,
                                        "cohort_class": cohort_class,
                                        "check": "strict_noop",
                                        "prefix_len": prefix_length,
                                        "precision_path": precision,
                                        "component": component,
                                        "mode": zero_mode,
                                        "max_abs_diff": diff,
                                        "tolerance": args.tolerance,
                                        "passed": diff <= args.tolerance,
                                    }
                                    no_op_rows.append(row)
                                    append_jsonl(metrics_handle, row)

                            for diagnostic_mode in ("off", "on"):
                                append_jsonl(
                                    metrics_handle,
                                    {
                                        "image_id": image_id,
                                        "cohort_class": cohort_class,
                                        "check": "component_diagnostics",
                                        "prefix_len": prefix_length,
                                        "vsv_mode": diagnostic_mode,
                                        "hidden_layers": modes[diagnostic_mode]["hidden_diagnostics"],
                                        "release_final_scale": logit_scale(
                                            modes[diagnostic_mode]["release_native"]["final"]
                                        ),
                                        "release_augmented_scale": logit_scale(
                                            modes[diagnostic_mode]["release_native"]["augmented"]
                                        ),
                                        "fp32_final_scale": logit_scale(
                                            modes[diagnostic_mode]["fp32_projection"]["final"]
                                        ),
                                        "fp32_augmented_scale": logit_scale(
                                            modes[diagnostic_mode]["fp32_projection"]["augmented"]
                                        ),
                                    },
                                )

                            for precision in ("release_native", "fp32_projection"):
                                off = modes["off"][precision]
                                on = modes["on"][precision]
                                method_logits = {
                                    "M00": off["final"],
                                    "M01": off["mixed"],
                                    "M10": on["final"],
                                    "M11": on["mixed"],
                                }
                                method_metrics: dict[str, dict[str, Any]] = {}
                                for method, logits in method_logits.items():
                                    metrics = tensor_metrics(logits, eos_id)[0]
                                    method_metrics[method] = metrics
                                    append_jsonl(
                                        metrics_handle,
                                        {
                                            "image_id": image_id,
                                            "cohort_class": cohort_class,
                                            "check": "fixed_prefix_factorial",
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
                                interaction_row = {
                                    "image_id": image_id,
                                    "cohort_class": cohort_class,
                                    "prefix_len": prefix_length,
                                    "precision_path": precision,
                                    "interaction_eos_margin": interaction,
                                }
                                interaction_rows.append(interaction_row)
                                append_jsonl(
                                    metrics_handle,
                                    {"check": "factorial_interaction", **interaction_row},
                                )

                            repeated_kwargs = repeat_kwargs(full_kwargs, args.batch_repeat)
                            for mode in ("off", "on"):
                                with vsv_mode(model, visual_vector, mode, args.vsv_lambda):
                                    repeated, _ = forward_components(
                                        model, repeated_kwargs, sla_indices, args.sla_alpha
                                    )
                                repeated_cpu = cpu_components(repeated)
                                single = modes[mode]
                                for precision, component, single_value in component_pairs(single):
                                    expected = single_value.repeat(args.batch_repeat, 1)
                                    diff = max_abs_diff(
                                        expected, repeated_cpu[precision][component]
                                    )
                                    row = {
                                        "image_id": image_id,
                                        "cohort_class": cohort_class,
                                        "check": "batch_repeat",
                                        "prefix_len": prefix_length,
                                        "vsv_mode": mode,
                                        "precision_path": precision,
                                        "component": component,
                                        "repeat": args.batch_repeat,
                                        "max_abs_diff": diff,
                                        "tolerance": args.tolerance,
                                        "passed": diff <= args.tolerance,
                                        "decision_stability": decision_stability(
                                            expected, repeated_cpu[precision][component], eos_id
                                        ),
                                    }
                                    batch_rows.append(row)
                                    append_jsonl(metrics_handle, row)

                            if prefix_length >= 0:
                                for mode in ("off", "on"):
                                    with vsv_mode(model, visual_vector, mode, args.vsv_lambda):
                                        cached = cached_components(
                                            model, base_kwargs, prefix, sla_indices, args.sla_alpha
                                        )
                                    cached_cpu = cpu_components(cached)
                                    full = modes[mode]
                                    for precision, component, full_value in component_pairs(full):
                                        diff = max_abs_diff(
                                            full_value, cached_cpu[precision][component]
                                        )
                                        row = {
                                            "image_id": image_id,
                                            "cohort_class": cohort_class,
                                            "check": "cache_consistency",
                                            "prefix_len": prefix_length,
                                            "vsv_mode": mode,
                                            "precision_path": precision,
                                            "component": component,
                                            "max_abs_diff": diff,
                                            "tolerance": args.tolerance,
                                            "passed": diff <= args.tolerance,
                                            "decision_stability": decision_stability(
                                                full_value, cached_cpu[precision][component], eos_id
                                            ),
                                        }
                                        cache_rows.append(row)
                                        append_jsonl(metrics_handle, row)

                        append_jsonl(metrics_handle, {"check": "image_status", **status})
                except Exception as exc:
                    status.update(
                        {
                            "record_status": "exception",
                            "exception_type": type(exc).__name__,
                            "exception_message": str(exc),
                            "traceback": traceback.format_exc(),
                        }
                    )
                    append_jsonl(metrics_handle, {"check": "image_status", **status})
                image_statuses.append(status)
                torch.cuda.empty_cache()
        except Exception as exc:
            runtime_error = f"{type(exc).__name__}: {exc}"
        finally:
            if model is not None:
                ensure_clean_model_state(model)

    all_checks = no_op_rows + batch_rows + cache_rows
    failures = [row for row in all_checks if not row["passed"]]
    image_failures = [row for row in image_statuses if row["record_status"] != "ok"]
    interactions = [row["interaction_eos_margin"] for row in interaction_rows]
    nan_interactions = any(not math.isfinite(value) for value in interactions)
    execution_done = (
        runtime_error is None
        and len(image_statuses) == len(selected)
        and not image_failures
    )
    hard_checks_pass = execution_done and not failures and not nan_interactions

    summary = {
        "run_id": run_id,
        "execution_status": "DONE" if execution_done else "FAILED",
        "hard_checks_status": "PASS" if hard_checks_pass else "FAIL",
        "selected_images": len(selected),
        "processed_images": len(image_statuses),
        "image_failures": image_failures,
        "runtime_error": runtime_error,
        "metric_rows": sum(1 for _ in metrics_path.open(encoding="utf-8")),
        "hard_check_rows": len(all_checks),
        "hard_check_failures": len(failures),
        "max_noop_diff": max((row["max_abs_diff"] for row in no_op_rows), default=None),
        "max_batch_repeat_diff": max(
            (row["max_abs_diff"] for row in batch_rows), default=None
        ),
        "max_cache_diff": max((row["max_abs_diff"] for row in cache_rows), default=None),
        "interaction_count": len(interactions),
        "interaction_summary_descriptive_only": {
            "mean": sum(interactions) / len(interactions) if interactions else None,
            "min": min(interactions) if interactions else None,
            "max": max(interactions) if interactions else None,
            "contains_nonfinite": nan_interactions,
        },
        "failures": failures,
        "config_file": source_record(config_path),
        "metrics_file": source_record(metrics_path),
        "outputs": {
            "config": str(config_path),
            "metrics": str(metrics_path),
            "summary": str(summary_path),
        },
        "interpretation_guard": (
            "This four-image run validates implementation only; it does not establish the "
            "mechanism or estimate prevalence."
        ),
    }
    write_json(summary_path, summary)
    print(json.dumps(summary, indent=2))
    if not hard_checks_pass:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
