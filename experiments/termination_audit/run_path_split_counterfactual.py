#!/usr/bin/env python3
"""B2 fixed-prefix final/SLA-path counterfactual decomposition."""
from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path
from types import SimpleNamespace

import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import myutils
from experiments.termination_audit.fixed_prefix_sanity import (
    ensure_clean_model_state, extend_prefix, forward_components, image_path_from_id,
    load_selected_ids, parse_layer_indices, prepare_image, prompt_kwargs, tensor_metrics,
    vsv_mode,
)
from llava.utils import disable_torch_init
from model_loader import ModelLoader
from steering_vector import obtain_vsv


def args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--mechanism-manifest", type=Path, required=True)
    p.add_argument("--b1-jsonl", type=Path, required=True)
    p.add_argument("--data-path", type=Path, required=True)
    p.add_argument("--checkpoint-path", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--num-pairs", type=int, default=32)
    p.add_argument("--prefix-lengths", default="0,1,3,5,10")
    p.add_argument("--seed", type=int, default=1994)
    p.add_argument("--vsv-lambda", type=float, default=.17)
    p.add_argument("--sla-alpha", type=float, default=.3)
    p.add_argument("--sla-layers", default="26,30")
    p.add_argument("--prompt", default="Please help me describe the image in detail")
    return p.parse_args()


def frozen_prefixes(path: Path) -> dict[int, list[int]]:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("record_type") == "image_status" and row.get("record_status") == "ok":
            out[int(row["image_id"])] = row["prefix_token_ids"]
    return out


def main() -> None:
    a = args()
    prefixes = frozen_prefixes(a.b1_jsonl)
    selected = load_selected_ids(a.mechanism_manifest, a.num_pairs)
    missing = [i for i, _ in selected if len(prefixes.get(i, [])) < 10]
    if missing:
        raise ValueError(f"B1 frozen prefixes missing or short: {missing}")
    lens = sorted({int(x) for x in a.prefix_lengths.split(",")})
    if lens != [0, 1, 3, 5, 10]:
        raise ValueError("required fixed prefixes are 0,1,3,5,10")
    a.output_dir.mkdir(parents=True, exist_ok=False)
    cache_dir = a.output_dir / "tensor_cache"; cache_dir.mkdir()
    out = a.output_dir / "path_split_metrics.jsonl"
    config = {"run_id":"E1-B2-path-split-fixed-prefix", "selected_images":[{"image_id":i,"cohort_class":c} for i,c in selected],
              "b1_prefix_source":str(a.b1_jsonl.resolve()), "prefix_lengths":lens,
              "vsv_lambda":a.vsv_lambda,"sla_alpha":a.sla_alpha,"sla_layers":a.sla_layers,
              "counterfactuals":{"C00":".7F0+.3A0","C10":".7F1+.3A0","C01":".7F0+.3A1","C11":".7F1+.3A1"}}
    (a.output_dir / "config.json").write_text(json.dumps(config, indent=2)+"\n")
    done = failed = 0; model = None
    with out.open("w", encoding="utf-8") as f:
        try:
            myutils.seed_everything(a.seed); disable_torch_init()
            loader = ModelLoader("llava-1.5", str(a.checkpoint_path.resolve()))
            model = loader.llm_model; model.eval(); ensure_clean_model_state(model)
            template = myutils.prepare_template(SimpleNamespace(model="llava-1.5"))
            eos = int(loader.tokenizer.eos_token_id); layers = parse_layer_indices(a.sla_layers)
            for image_id, cohort in selected:
                row = {"record_type":"image_status","image_id":image_id,"cohort_class":cohort,"record_status":"ok"}
                try:
                    with torch.inference_mode():
                        image = prepare_image(loader, image_path_from_id(a.data_path, image_id))
                        questions, base = prompt_kwargs(loader, template, a.prompt, image)
                        helper = SimpleNamespace(); neg = loader.prepare_neg_prompt(helper, questions, template=template)
                        pos = loader.prepare_pos_prompt(helper, base)
                        vector, _ = obtain_vsv(helper, model, [[neg, pos]], rank=1)
                        image_cache = {}
                        for k in lens:
                            prefix = torch.tensor(
                                prefixes[image_id][:k], dtype=torch.long,
                                device=base["input_ids"].device,
                            ).unsqueeze(0)
                            kwargs = extend_prefix(base, prefix)
                            with vsv_mode(model, vector, "off", a.vsv_lambda):
                                off, _ = forward_components(model, kwargs, layers, a.sla_alpha)
                            with vsv_mode(model, vector, "on", a.vsv_lambda):
                                on, _ = forward_components(model, kwargs, layers, a.sla_alpha)
                            F0,A0 = off["release_native"]["final"], off["release_native"]["augmented"]
                            F1,A1 = on["release_native"]["final"], on["release_native"]["augmented"]
                            cf = {"C00":.7*F0+.3*A0,"C10":.7*F1+.3*A0,"C01":.7*F0+.3*A1,"C11":.7*F1+.3*A1}
                            image_cache[str(k)] = {"F0":F0.cpu(),"F1":F1.cpu(),"A0":A0.cpu(),"A1":A1.cpu()}
                            for name, logits in cf.items():
                                f.write(json.dumps({"record_type":"counterfactual","image_id":image_id,"cohort_class":cohort,"prefix_len":k,"counterfactual":name,**tensor_metrics(logits,eos)[0]})+"\n"); f.flush()
                        torch.save(image_cache, cache_dir / f"{image_id}.pt")
                    done += 1
                except Exception as exc:
                    failed += 1; row.update({"record_status":"exception","exception_type":type(exc).__name__,"exception_message":str(exc),"traceback":traceback.format_exc()})
                f.write(json.dumps(row)+"\n"); f.flush(); torch.cuda.empty_cache()
                print(f"PROGRESS {done+failed}/{len(selected)} ok={done} exceptions={failed}", flush=True)
        finally:
            if model is not None: ensure_clean_model_state(model)
    summary={"target_images":len(selected),"completed_images":done,"exception_images":failed,"execution_status":"DONE" if done==len(selected) and not failed else "FAILED"}
    (a.output_dir/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary),flush=True)

if __name__ == "__main__": main()
