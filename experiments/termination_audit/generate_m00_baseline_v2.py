#!/usr/bin/env python3
"""Generate provenance-bound M00 (VSV off, SLA off) greedy captions."""

from __future__ import annotations

import argparse
import json
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
from experiments.termination_audit.provenance import (
    code_provenance,
    complete_checkpoint_provenance,
    source_record,
)
from llava.utils import disable_torch_init
from llm_layers import remove_vsv_layers
from model_loader import ModelLoader

PAPER_PROMPT = "Please help me describe the image in detail"
SUCCESS_STATUSES = {"ok", "short_nonempty", "eos_at_step1", "empty_after_decode"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-manifest", type=Path, required=True)
    parser.add_argument("--data-path", type=Path, required=True)
    parser.add_argument("--checkpoint-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default="llava-1.5")
    parser.add_argument("--seed", type=int, default=1994)
    parser.add_argument("--max-new-tokens", type=int, default=512)
    parser.add_argument("--short-output-words", type=int, default=10)
    parser.add_argument("--prompt", default=PAPER_PROMPT)
    return parser.parse_args()


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def image_path_from_id(data_path: Path, image_id: int) -> Path:
    path = data_path / f"COCO_val2014_000000{image_id:06d}.jpg"
    if not path.exists():
        raise FileNotFoundError(path)
    return path


def prepare_image(loader: ModelLoader, path: Path) -> dict[str, torch.Tensor]:
    with Image.open(path) as image:
        processed = loader.image_processor(image.convert("RGB"), return_tensors="pt")
    return {"pixel_values": processed["pixel_values"].unsqueeze(0)}


def clean_model(model: torch.nn.Module) -> None:
    remove_vsv_layers(model)
    for attr in ("logits_aug", "logits_layers", "logits_alpha"):
        if hasattr(model, attr):
            delattr(model, attr)


def classify_output(
    caption: str, generated: torch.Tensor, eos_id: int, short_words: int
) -> str:
    if generated.numel() == 1 and int(generated[0]) == eos_id:
        return "eos_at_step1"
    if not caption.strip():
        return "empty_after_decode"
    if len(caption.strip().split()) < short_words:
        return "short_nonempty"
    return "ok"


def main() -> None:
    args = parse_args()
    if args.model != "llava-1.5":
        raise ValueError("M00 v2 currently supports llava-1.5 only")
    if args.prompt != PAPER_PROMPT:
        raise ValueError("M00 matching baseline must use the paper prompt without punctuation")
    if args.short_output_words < 1:
        raise ValueError("--short-output-words must be positive")

    candidate = json.loads(args.candidate_manifest.read_text(encoding="utf-8"))
    image_ids = [int(value) for value in candidate["image_ids"]]
    if len(image_ids) != len(set(image_ids)):
        raise ValueError("candidate manifest contains duplicate image IDs")

    args.output_dir.mkdir(parents=True, exist_ok=True)
    result_path = args.output_dir / "m00_greedy_candidates_v2.jsonl"
    config_path = args.output_dir / "m00_greedy_candidates_v2_config.json"
    summary_path = args.output_dir / "m00_greedy_candidates_v2_summary.json"
    for path in (result_path, config_path, summary_path):
        if path.exists():
            raise FileExistsError(f"refusing to overwrite existing output: {path}")

    executed_code = [
        Path(__file__).resolve(),
        PROJECT_ROOT / "experiments/termination_audit/provenance.py",
        PROJECT_ROOT / "model_loader.py",
        PROJECT_ROOT / "llm_layers.py",
        PROJECT_ROOT / "llava/model/language_model/llava_llama.py",
        PROJECT_ROOT / "llava/model/llava_arch.py",
    ]
    config: dict[str, Any] = {
        "schema_version": 2,
        "run_id": "E1-M0-M00-candidate-baseline-v2",
        "model": args.model,
        "method": {"vsv": False, "sla": False},
        "candidate_manifest": source_record(args.candidate_manifest, "candidate_manifest"),
        "data_path": str(args.data_path.resolve()),
        "checkpoint_path": str(args.checkpoint_path.resolve()),
        "code": code_provenance(executed_code),
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
            "use_cache": True,
        },
        "record_status_taxonomy": {
            "ok": f"nonempty caption with at least {args.short_output_words} words",
            "short_nonempty": f"nonempty caption with fewer than {args.short_output_words} words",
            "eos_at_step1": "the sole generated token is EOS",
            "empty_after_decode": "decoded caption is empty",
            "exception": "per-image execution raised",
            "missing_record": "target ID has no JSONL row",
        },
        "dependencies": {"python": sys.version.split()[0], "torch": torch.__version__},
    }
    write_json(config_path, config)

    completed = 0
    exceptions = 0
    written_ids: list[int] = []
    status_counts: dict[str, int] = {}
    runtime_error: str | None = None
    model = None

    with result_path.open("w", encoding="utf-8") as handle:
        try:
            myutils.seed_everything(args.seed)
            disable_torch_init()
            loader = ModelLoader(args.model, str(args.checkpoint_path.resolve()))
            model = loader.llm_model
            model.eval()
            clean_model(model)
            template = myutils.prepare_template(SimpleNamespace(model=args.model))
            eos_id = int(loader.tokenizer.eos_token_id)
            pad_id = int(loader.tokenizer.pad_token_id)
            config["generation"].update({"eos_token_id": eos_id, "pad_token_id": pad_id})
            config["dependencies"]["transformers"] = __import__("transformers").__version__
            config["model_dtype"] = str(next(model.parameters()).dtype)
            write_json(config_path, config)

            for image_id in image_ids:
                row: dict[str, Any] = {
                    "image_id": image_id,
                    "record_status": "exception",
                    "caption": "",
                    "generated_token_count": 0,
                    "stop_reason": None,
                }
                try:
                    with torch.inference_mode():
                        image = prepare_image(loader, image_path_from_id(args.data_path, image_id))
                        _, kwargs = loader.prepare_inputs_for_model(template, [args.prompt], image)
                        kwargs["attention_mask"] = torch.ones_like(kwargs["input_ids"])
                        input_length = kwargs["input_ids"].shape[1]
                        output = model.generate(
                            do_sample=False,
                            num_beams=1,
                            max_new_tokens=args.max_new_tokens,
                            use_cache=True,
                            eos_token_id=eos_id,
                            pad_token_id=pad_id,
                            early_stopping=False,
                            length_penalty=1.0,
                            return_dict_in_generate=False,
                            **kwargs,
                        )
                        generated = output[0, input_length:]
                        caption = loader.decode(output)[0]
                        row.update(
                            {
                                "caption": caption,
                                "generated_token_count": int(generated.numel()),
                                "first_generated_token_id": (
                                    int(generated[0]) if generated.numel() else None
                                ),
                                "stop_reason": (
                                    "eos"
                                    if generated.numel() and int(generated[-1]) == eos_id
                                    else "max_new_tokens"
                                ),
                                "record_status": classify_output(
                                    caption, generated, eos_id, args.short_output_words
                                ),
                            }
                        )
                    completed += 1
                except Exception as exc:
                    exceptions += 1
                    row.update(
                        {
                            "exception_type": type(exc).__name__,
                            "exception_message": str(exc),
                            "traceback": traceback.format_exc(),
                        }
                    )
                handle.write(json.dumps(row, ensure_ascii=False) + "\n")
                handle.flush()
                written_ids.append(image_id)
                status = str(row["record_status"])
                status_counts[status] = status_counts.get(status, 0) + 1
        except Exception as exc:
            runtime_error = f"{type(exc).__name__}: {exc}"
        finally:
            if model is not None:
                clean_model(model)

    missing_ids = sorted(set(image_ids) - set(written_ids))
    execution_done = (
        runtime_error is None
        and exceptions == 0
        and completed == len(image_ids)
        and not missing_ids
        and set(status_counts).issubset(SUCCESS_STATUSES)
    )
    summary = {
        "schema_version": 2,
        "run_id": config["run_id"],
        "target_records": len(image_ids),
        "written_records": len(written_ids),
        "completed_records": completed,
        "exception_records": exceptions,
        "missing_record_count": len(missing_ids),
        "missing_image_ids": missing_ids,
        "record_status_counts": status_counts,
        "runtime_error": runtime_error,
        "execution_status": "DONE" if execution_done else "FAILED",
        "result_file": source_record(result_path, "m00_jsonl"),
        "config_file": source_record(config_path, "m00_config"),
    }
    write_json(summary_path, summary)
    print(json.dumps(summary, indent=2))
    if not execution_done:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
