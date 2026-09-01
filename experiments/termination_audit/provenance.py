"""Shared immutable provenance helpers for the termination-audit experiments."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def source_record(path: Path, role: str | None = None) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": str(path.resolve()),
        "size": path.stat().st_size,
        "sha256": sha256_file(path),
    }
    if role is not None:
        record["role"] = role
    return record


def _unique_files(paths: Iterable[Path]) -> list[Path]:
    return sorted({path.resolve() for path in paths if path.exists() and path.is_file()})


def main_checkpoint_records(checkpoint_path: Path) -> list[dict[str, Any]]:
    patterns = ("*.json", "*.safetensors", "*.bin", "tokenizer.model")
    files = _unique_files(
        path for pattern in patterns for path in checkpoint_path.glob(pattern)
    )
    if not files:
        raise FileNotFoundError(f"no checkpoint/config/tokenizer files under {checkpoint_path}")
    return [source_record(path, "llava_checkpoint_or_tokenizer") for path in files]


def vision_tower_records(checkpoint_path: Path) -> dict[str, Any]:
    config = json.loads((checkpoint_path / "config.json").read_text(encoding="utf-8"))
    tower_name = str(config.get("mm_vision_tower", ""))
    if not tower_name:
        raise ValueError("checkpoint config does not declare mm_vision_tower")

    direct_path = Path(tower_name).expanduser()
    revision = None
    if direct_path.is_dir():
        snapshot_path = direct_path.resolve()
    else:
        hf_home = Path(
            os.environ.get("HF_HOME", str(Path.home() / ".cache" / "huggingface"))
        ).expanduser()
        repository = hf_home / "hub" / f"models--{tower_name.replace('/', '--')}"
        ref_path = repository / "refs" / "main"
        if not ref_path.exists():
            raise FileNotFoundError(
                f"cannot resolve local vision tower {tower_name}; missing {ref_path}"
            )
        revision = ref_path.read_text(encoding="utf-8").strip()
        snapshot_path = repository / "snapshots" / revision

    names = (
        "config.json",
        "preprocessor_config.json",
        "pytorch_model.bin",
        "model.safetensors",
    )
    files = _unique_files(snapshot_path / name for name in names)
    if not files:
        raise FileNotFoundError(f"no vision-tower files found under {snapshot_path}")
    return {
        "declared_name": tower_name,
        "revision": revision,
        "snapshot_path": str(snapshot_path.resolve()),
        "files": [source_record(path, "vision_tower") for path in files],
    }


def complete_checkpoint_provenance(checkpoint_path: Path) -> dict[str, Any]:
    checkpoint_path = checkpoint_path.resolve()
    return {
        "checkpoint_path": str(checkpoint_path),
        "llava_files": main_checkpoint_records(checkpoint_path),
        "vision_tower": vision_tower_records(checkpoint_path),
    }


def code_provenance(files: Iterable[Path]) -> dict[str, Any]:
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
        "files": [source_record(path.resolve(), "executed_code") for path in files],
    }
