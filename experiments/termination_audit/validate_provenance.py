"""Deterministically validate recorded local checkpoint provenance."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from experiments.termination_audit.provenance import source_record


def validate_recorded_checkpoint(record: dict[str, Any]) -> None:
    checkpoint_path = Path(str(record.get("checkpoint_path", ""))).resolve()
    if not checkpoint_path.is_dir():
        raise FileNotFoundError(f"recorded checkpoint path is unavailable: {checkpoint_path}")

    llava_files = record.get("llava_files", [])
    vision = record.get("vision_tower", {})
    vision_files = vision.get("files", [])
    if not llava_files or not vision_files:
        raise ValueError("recorded checkpoint provenance is incomplete")

    for item in [*llava_files, *vision_files]:
        path = Path(str(item.get("path", "")))
        if not path.exists():
            raise FileNotFoundError(f"recorded model file is unavailable: {path}")
        actual = source_record(path)
        if actual["size"] != item.get("size") or actual["sha256"] != item.get("sha256"):
            raise ValueError(f"recorded model file changed: {path}")

    tokenizer = [item for item in llava_files if Path(item["path"]).name == "tokenizer.model"]
    if len(tokenizer) != 1:
        raise ValueError("checkpoint provenance must contain exactly one tokenizer.model")
    snapshot_path = Path(str(vision.get("snapshot_path", ""))).resolve()
    if not snapshot_path.is_dir():
        raise FileNotFoundError(f"recorded vision snapshot is unavailable: {snapshot_path}")
