"""M0: pair the full input roster and audit image readability without dropping rows."""
import argparse
import re
from pathlib import Path

from PIL import Image
from .common import new_run, read_jsonl, write_jsonl, report, ratio, sha


def index(path):
    result = {}
    for row in read_jsonl(path):
        image_id = str(row["image_id"])
        if not re.fullmatch(r"[0-9]+", image_id) or image_id in result:
            raise ValueError("Invalid or duplicate image_id")
        if not isinstance(row.get("caption"), str):
            raise ValueError("caption must be a string")
        result[image_id] = row["caption"]
    return result


def build(original, steer, image_dir, output):
    a, b = index(original), index(steer)
    out = new_run(output, "M0", [original, steer],
                  {"decode": "greedy", "configuration_evidence": "filename_only",
                   "split": "exploratory_existing_data", "stop_reason": "unknown"}, [__file__])
    pairs, image_ok = [], 0
    directories = [Path(p).resolve() for p in (image_dir if isinstance(image_dir, list) else [image_dir])]
    for iid in sorted(a.keys() | b.keys(), key=int):
        candidates = [d / name for d in directories for name in (f"COCO_val2014_{int(iid):012d}.jpg", f"{int(iid)}.jpg")]
        existing = [p for p in candidates if p.is_file()]
        image_path = existing[0] if existing else candidates[0]
        image_status, image_sha = "missing", None
        if len({sha(p) for p in existing}) > 1:
            image_status = "conflicting_files"
        elif image_path.exists():
            try:
                with Image.open(image_path) as img:
                    img.verify()
                image_status, image_sha = "readable", sha(image_path)
                image_ok += 1
            except (OSError, ValueError):
                image_status = "unreadable"
        pairs.append({"pair_id": iid, "image_id": iid, "image_path": str(image_path),
                      "image_sha256": image_sha, "image_status": image_status,
                      "pair_status": "paired" if iid in a and iid in b else "unpaired",
                      "original": {"caption_id": iid + "_original", "text": a[iid]} if iid in a else None,
                      "steer": {"caption_id": iid + "_steer", "text": b[iid]} if iid in b else None,
                      "stop_reason": "unknown", "split": "exploratory_existing_data"})
    write_jsonl(out / "pairs.jsonl", pairs)
    metrics = {"original_rows": len(a), "steer_rows": len(b), "roster_rows": len(pairs),
               "paired": len(a.keys() & b.keys()), "pair_coverage": ratio(len(a.keys() & b.keys()), len(pairs)),
               "image_readable": image_ok, "image_readable_rate": ratio(image_ok, len(pairs)),
               "unpaired": sum(p["pair_status"] != "paired" for p in pairs),
               "empty_original": sum(not s.strip() for s in a.values()),
               "empty_steer": sum(not s.strip() for s in b.values()), "silent_drops": 0}
    report(out, "M0 数据配对与图像审计", metrics,
           ["未调用LLM；读取并校验原图，缺图/坏图保留在名册。", "既有500图是探索数据，不冒称未见测试集。",
            "解码设置仅有文件名线索；没有真实EOS/生成trace，停止原因统一unknown。"])
    return metrics


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    for key in ("original", "steer", "output"):
        p.add_argument("--" + key, required=True)
    p.add_argument("--image-dir", required=True, action="append")
    args = p.parse_args()
    print(build(args.original, args.steer, args.image_dir, args.output))
