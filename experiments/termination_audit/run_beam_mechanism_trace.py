#!/usr/bin/env python3
"""Trace real beam decoding under the paper's VSV x SLA configurations."""

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
from transformers import LogitsProcessor, LogitsProcessorList

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import myutils
from llava.utils import disable_torch_init
from llm_layers import add_vsv_layers, remove_vsv_layers
from model_loader import ModelLoader
from steering_vector import add_logits_flag, obtain_vsv, remove_logits_flag

PROMPT = "Please help me describe the image in detail."


def args_parser() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--mechanism-manifest", type=Path, required=True)
    p.add_argument("--data-path", type=Path, required=True)
    p.add_argument("--checkpoint-path", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--num-pairs", type=int, default=32)
    p.add_argument("--image-ids", type=int, nargs="+", default=None,
                   help="Optional manifest image IDs to run; preserves their frozen cohort labels.")
    p.add_argument("--methods", nargs="+", default=None,
                   choices=["M00_beam5", "M10_beam5", "M01_beam5", "M11_beam5",
                            "M00_greedy", "M10_greedy", "M01_greedy", "M11_greedy"],
                   help="Optional subset of pre-registered methods for a resume run.")
    p.add_argument("--resume", action="store_true",
                   help="Append only missing or previously exceptional image/method records to an existing output directory.")
    p.add_argument("--seed", type=int, default=1994)
    p.add_argument("--max-new-tokens", type=int, default=512)
    return p.parse_args()


def selected(manifest: Path, pairs: int) -> list[tuple[int, str]]:
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if len(data["pairs"]) < pairs:
        raise ValueError("manifest has fewer pairs than requested")
    out: list[tuple[int, str]] = []
    for pair in data["pairs"][:pairs]:
        out += [(int(pair["collapse_image_id"]), "collapse"), (int(pair["control_image_id"]), "control")]
    return out


def prepare_image(loader: ModelLoader, data_path: Path, image_id: int) -> dict[str, torch.Tensor]:
    path = data_path / f"COCO_val2014_000000{image_id:06d}.jpg"
    with Image.open(path) as im:
        batch = loader.image_processor(im.convert("RGB"), return_tensors="pt")
    return {"pixel_values": batch["pixel_values"].unsqueeze(0)}


def clean(model: torch.nn.Module) -> None:
    remove_vsv_layers(model)
    for name in ("logits_aug", "logits_layers", "logits_alpha"):
        if hasattr(model, name):
            delattr(model, name)


def summarize_scores(scores: tuple[torch.Tensor, ...], eos_id: int, beams: int) -> list[dict[str, Any]]:
    trace: list[dict[str, Any]] = []
    for step, score in enumerate(scores):
        # score is log-softmaxed vocab scores for each active beam in HF beam search.
        rows = []
        for beam in range(min(beams, score.shape[0])):
            values, ids = torch.topk(score[beam], k=5)
            rows.append({
                "beam_slot": beam,
                "eos_score": float(score[beam, eos_id].float().cpu()),
                "top5_token_ids": [int(x) for x in ids.cpu()],
                "top5_scores": [float(x) for x in values.float().cpu()],
            })
        trace.append({"step": step + 1, "active_beams": rows})
    return trace


class CompactBeamTrace(LogitsProcessor):
    """Keep trace-sized score summaries off GPU during generation."""

    def __init__(self, eos_id: int, beams: int) -> None:
        self.eos_id = eos_id
        self.beams = beams
        self.trace: list[dict[str, Any]] = []

    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor) -> torch.FloatTensor:
        # ``output_scores=True`` retains one full vocabulary tensor per step.
        # Store only audit-relevant log-probabilities on CPU instead.
        log_probs = torch.log_softmax(scores.float(), dim=-1)
        rows = []
        for beam in range(min(self.beams, log_probs.shape[0])):
            values, ids = torch.topk(log_probs[beam], k=5)
            rows.append({
                "beam_slot": beam,
                "eos_score": float(log_probs[beam, self.eos_id].cpu()),
                "top5_token_ids": [int(x) for x in ids.cpu()],
                "top5_scores": [float(x) for x in values.cpu()],
            })
        self.trace.append({"step": len(self.trace) + 1, "active_beams": rows})
        return scores


def classify(caption: str, sequence: torch.Tensor, input_length: int, eos_id: int) -> str:
    generated = sequence[input_length:]
    if generated.numel() == 1 and int(generated[0]) == eos_id:
        return "eos_at_step1"
    return "empty_after_decode" if not caption.strip() else "nonempty"


def run_one(model, loader, template, image, method: str, max_new_tokens: int) -> dict[str, Any]:
    use_vsv, use_sla, beams = {
        "M00_beam5": (False, False, 5),
        "M10_beam5": (True, False, 5),
        "M01_beam5": (False, True, 5),
        "M00_greedy": (False, False, 1),
        "M10_greedy": (True, False, 1),
        "M01_greedy": (False, True, 1),
        "M11_greedy": (True, True, 1),
        "M11_beam5": (True, True, 5),
    }[method]
    questions, kwargs = loader.prepare_inputs_for_model(template, [PROMPT], image)
    input_length = int(kwargs["input_ids"].shape[1])
    helper = SimpleNamespace(vsv_lambda=0.17, layers=None, logits_aug=use_sla,
                             logits_layers="25,30", logits_alpha=0.3)
    vector = None
    if use_vsv:
        neg = loader.prepare_neg_prompt(helper, questions, template=template)
        pos = loader.prepare_pos_prompt(helper, kwargs)
        vector, _ = obtain_vsv(helper, model, [[neg, pos]], rank=1)
        add_vsv_layers(model, torch.stack([vector], dim=1).cuda(), [helper.vsv_lambda], None)
    add_logits_flag(model, helper)
    try:
        eos_id = int(loader.tokenizer.eos_token_id)
        compact_trace = CompactBeamTrace(eos_id, beams)
        output = model.generate(
            do_sample=False, num_beams=beams, max_new_tokens=max_new_tokens,
            use_cache=True, early_stopping=False, length_penalty=1.0,
            # Keeping a generation return dict makes Transformers retain every
            # step's hidden states when SLA requests them.  SLA needs each
            # step's hidden states inside the forward pass, not their history;
            # return only the final sequence and stream the compact audit trace.
            return_dict_in_generate=False, output_scores=False, output_attentions=False,
            output_hidden_states=use_sla, **kwargs,
            logits_processor=LogitsProcessorList([compact_trace]),
        )
        sequence = output[0]
        caption = loader.decode(output)[0]
        result = {
            "caption": caption,
            "record_status": classify(caption, sequence, input_length, eos_id),
            "generated_token_ids": [int(x) for x in sequence[input_length:].cpu()],
            "generated_token_count": int(sequence.numel() - input_length),
            "sequence_score": None,
            "step_trace": compact_trace.trace,
            "trace_storage": "compact_cpu_logits_processor",
        }
        return result
    finally:
        clean(model)


def main() -> None:
    a = args_parser()
    ids = selected(a.mechanism_manifest, a.num_pairs)
    if a.image_ids is not None:
        cohort_by_id = dict(ids)
        missing = sorted(set(a.image_ids) - set(cohort_by_id))
        if missing:
            raise ValueError(f"image IDs absent from selected frozen manifest: {missing}")
        ids = [(image_id, cohort_by_id[image_id]) for image_id in a.image_ids]
    rows_path = a.output_dir / "beam_mechanism_trace.jsonl"
    config_path = a.output_dir / "config.json"
    summary_path = a.output_dir / "summary.json"
    config = {"run_id": "E2-beam-mechanism-trace-64", "prompt": PROMPT, "seed": a.seed,
              "images": [{"image_id": i, "cohort_class": c} for i,c in ids],
              "methods": a.methods or ["M00_beam5", "M10_beam5", "M01_beam5", "M11_greedy", "M11_beam5"],
              "paper_settings": {"vsv_lambda": .17, "sla_layers": "25,30", "sla_alpha": .3,
                                 "max_new_tokens": a.max_new_tokens, "do_sample": False, "use_cache": True}}
    existing_rows: list[dict[str, Any]] = []
    if a.resume:
        if not rows_path.is_file() or not config_path.is_file():
            raise FileNotFoundError("--resume requires existing config.json and beam_mechanism_trace.jsonl")
        existing = json.loads(config_path.read_text(encoding="utf-8"))
        if existing.get("images") != config["images"] or existing.get("methods") != config["methods"]:
            raise ValueError("resume configuration differs from existing output directory")
        existing_rows = [json.loads(line) for line in rows_path.read_text(encoding="utf-8").splitlines() if line]
    else:
        a.output_dir.mkdir(parents=True, exist_ok=False)
        config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    completed_keys = {(int(row["image_id"]), row["method"]) for row in existing_rows if row.get("record_status") != "exception"}
    completed = sum(row.get("record_status") != "exception" for row in existing_rows)
    exceptions = sum(row.get("record_status") == "exception" for row in existing_rows)
    model = None
    with rows_path.open("a" if a.resume else "w", encoding="utf-8") as fh:
        try:
            myutils.seed_everything(a.seed); disable_torch_init()
            loader = ModelLoader("llava-1.5", str(a.checkpoint_path.resolve()))
            model = loader.llm_model; model.eval(); clean(model)
            template = myutils.prepare_template(SimpleNamespace(model="llava-1.5"))
            for n, (image_id, cohort) in enumerate(ids, 1):
                image = prepare_image(loader, a.data_path, image_id)
                for method in config["methods"]:
                    if (image_id, method) in completed_keys:
                        continue
                    row: dict[str, Any] = {"image_id": image_id, "cohort_class": cohort, "method": method}
                    try:
                        with torch.inference_mode(): row.update(run_one(model, loader, template, image, method, a.max_new_tokens))
                        completed += 1
                    except Exception as exc:
                        clean(model); exceptions += 1
                        row.update({"record_status": "exception", "exception_type": type(exc).__name__, "exception_message": str(exc), "traceback": traceback.format_exc()})
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n"); fh.flush()
                print(f"PROGRESS images={n}/{len(ids)} records={completed + exceptions} ok={completed} exceptions={exceptions}", flush=True)
                torch.cuda.empty_cache()
        finally:
            if model is not None: clean(model)
    summary = {"target_images": len(ids), "target_records": len(ids)*len(config["methods"]), "completed_records": completed,
               "exception_records": exceptions, "execution_status": "DONE" if not exceptions and completed == len(ids)*len(config["methods"]) else "FAILED"}
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    main()
