#!/usr/bin/env python3
"""Generate M00 (VSV off, SLA off) greedy captions for frozen candidate IDs."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import torch
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import myutils
from llava.utils import disable_torch_init
from llm_layers import remove_vsv_layers
from model_loader import ModelLoader
from experiments.termination_audit.provenance import complete_checkpoint_provenance


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--data-path", type=Path, required=True)
    parser.add_argument("--checkpoint-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="llava-1.5")
    parser.add_argument("--seed", type=int, default=1994)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument(
        "--prompt", default="Please help me describe the image in detail"
    )
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path.resolve()),
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
    }


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


def image_path_from_id(data_path: Path, image_id: int) -> Path:
    path = data_path / f"COCO_val2014_000000{image_id:06d}.jpg"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def prepare_image(model_loader: ModelLoader, image_path: Path) -> dict[str, torch.Tensor]:
    image = Image.open(image_path).convert("RGB")
    processed = model_loader.image_processor(image, return_tensors="pt")
    return {"pixel_values": processed["pixel_values"].unsqueeze(0)}


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    if args.model != "llava-1.5":
        raise ValueError("M00 baseline generator currently supports llava-1.5 only")
    candidate_manifest = json.loads(args.candidate_manifest.read_text(encoding="utf-8"))
    image_ids = [int(value) for value in candidate_manifest["image_ids"]]
    if len(image_ids) != len(set(image_ids)):
        raise ValueError("candidate manifest contains duplicate image IDs")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    result_path = args.output_dir / "m00_greedy_candidates.jsonl"
    summary_path = args.output_dir / "m00_greedy_candidates_summary.json"
    config_path = args.output_dir / "m00_greedy_candidates_config.json"
    for path in (result_path, summary_path, config_path):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite existing output: {path}")

    config: dict[str, Any] = {
        "run_id": "E1-M0-M00-candidate-baseline",
        "model": args.model,
        "method": {"vsv": False, "sla": False},
        "candidate_manifest": source_record(args.candidate_manifest),
        "data_path": str(args.data_path.resolve()),
        "checkpoint_path": str(args.checkpoint_path.resolve()),
        "checkpoint_provenance": complete_checkpoint_provenance(args.checkpoint_path),
        "code": code_provenance(),
        "seed": args.seed,
        "prompt": args.prompt,
        "generation": {
            "do_sample": False,
            "num_beams": 1,
            "max_new_tokens": args.max_new_tokens,
            "temperature": 1.0,
            "early_stopping": False,
            "length_penalty": 1.0,
            "min_new_tokens": None,
        },
        "dependencies": {
            "python": sys.version.split()[0],
            "torch": torch.__version__,
        },
    }
    write_json(config_path, config)

    completed = 0
    exceptions = 0
    empty = 0
    runtime_error: str | None = None
    model = None
    with result_path.open("w", encoding="utf-8") as handle:
        try:
            myutils.seed_everything(args.seed)
            disable_torch_init()
            model_loader = ModelLoader(args.model, str(args.checkpoint_path.resolve()))
            model = model_loader.llm_model
            model.eval()
            remove_vsv_layers(model)
            for attr in ("logits_aug", "logits_layers", "logits_alpha"):
                if hasattr(model, attr):
                    delattr(model, attr)
            template = myutils.prepare_template(SimpleNamespace(model=args.model))
            eos_id = int(model_loader.tokenizer.eos_token_id)
            pad_id = int(model_loader.tokenizer.pad_token_id)
            config["generation"].update({"eos_token_id": eos_id, "pad_token_id": pad_id})
            config["dependencies"]["transformers"] = __import__("transformers").__version__
            config["model_dtype"] = str(next(model.parameters()).dtype)
            write_json(config_path, config)

            for image_id in image_ids:
                row: dict[str, Any] = {
                    "image_id": image_id,
                    "record_status": "ok",
                    "caption": "",
                    "generated_token_count": 0,
                    "stop_reason": None,
                }
                try:
                    with torch.inference_mode():
                        image = prepare_image(
                            model_loader, image_path_from_id(args.data_path, image_id)
                        )
                        _, kwargs = model_loader.prepare_inputs_for_model(
                            template, [args.prompt], image
                        )
                        kwargs["attention_mask"] = torch.ones_like(kwargs["input_ids"])
                        input_length = kwargs["input_ids"].shape[1]
                        output = model.generate(
                            do_sample=False,
                            num_beams=1,
                            max_new_tokens=args.max_new_tokens,
                            use_cache=True,
                            eos_token_id=eos_id,
                            pad_token_id=pad_id,
                            return_dict_in_generate=False,
                            **kwargs,
                        )
                        generated = output[0, input_length:]
                        row["generated_token_count"] = int(generated.numel())
                        row["first_generated_token_id"] = (
                            int(generated[0]) if generated.numel() else None
                        )
                        row["stop_reason"] = (
                            "eos"
                            if generated.numel() and int(generated[-1]) == eos_id
                            else "max_new_tokens"
                        )
                        row["caption"] = model_loader.decode(output)[0]
                    completed += 1
                    if not row["caption"].strip():
                        empty += 1
                except Exception as exc:
                    exceptions += 1
                    row.update(
                        {
                            "record_status": "exception",
                            "exception_type": type(exc).__name__,
                            "exception_message": str(exc),
                            "traceback": traceback.format_exc(),
                        }
                    )
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                handle.flush()
        except Exception as exc:
            runtime_error = f"{type(exc).__name__}: {exc}"
        finally:
            if model is not None:
                remove_vsv_layers(model)
                for attr in ("logits_aug", "logits_layers", "logits_alpha"):
                    if hasattr(model, attr):
                        delattr(model, attr)

    summary = {
        "run_id": config["run_id"],
        "target_records": len(image_ids),
        "written_records": completed + exceptions,
        "completed_records": completed,
        "exception_records": exceptions,
        "empty_records": empty,
        "runtime_error": runtime_error,
        "execution_status": (
            "DONE"
            if runtime_error is None and exceptions == 0 and completed == len(image_ids)
            else "FAILED"
        ),
        "result_path": str(result_path),
        "config_path": str(config_path),
    }
    write_json(summary_path, summary)
    print(json.dumps(summary, indent=2))
    if summary["execution_status"] != "DONE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
