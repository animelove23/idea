"""One semantic call, at most one retry; existing API config with thinking disabled."""
import json
from pathlib import Path
from urllib.error import HTTPError, URLError

from decomposition.semantic_decomposer import DeepSeekDecomposer
from .schema import CATEGORY_MAP, ProtocolError, fold_document

ROOT = Path(__file__).parent


def load_shots():
    shots = json.loads((ROOT / "shots.json").read_text(encoding="utf-8"))
    if len(shots) != 8 or len({s["text"] for s in shots}) != 8:
        raise ValueError("Expected eight distinct examples")
    for shot in shots:
        doc = fold_document(shot["output"], shot["text"])
        if doc["status"] != "ready":
            raise ValueError("Example has invalid fields or source: " + shot["text"])
    return shots


def prompt(shots=8):
    if shots not in (0, 8):
        raise ValueError("shots must be 0 or 8")
    rules = (ROOT / "rules.txt").read_text(encoding="utf-8")
    rules += "\nCATEGORY_MAP: " + json.dumps(CATEGORY_MAP)
    if shots:
        for example in load_shots():
            rules += "\nINPUT: " + json.dumps({"text": example["text"]})
            rules += "\nOUTPUT: " + json.dumps(example["output"], separators=(",", ":"))
    return rules


class V6Failure(RuntimeError):
    def __init__(self, message, audit):
        super().__init__(message)
        self.audit = audit


class DecomposerV6:
    def __init__(self, config, shots=8, transport=None, frozen_prompt=None):
        self.config = config
        self.prompt = prompt(shots) if frozen_prompt is None else frozen_prompt
        self.transport = transport or DeepSeekDecomposer(config, prompt="unused")._request

    def decompose(self, text):
        audit = {"attempts": [], "thinking": "disabled", "cache_hit": False, "api_calls": 0}
        if not text.strip():
            return fold_document({"elements": []}, text), audit
        messages = [{"role": "system", "content": self.prompt},
                    {"role": "user", "content": json.dumps({"text": text}, ensure_ascii=False)}]
        for attempt in range(2):
            body = {"model": self.config.model, "messages": messages,
                    "response_format": {"type": "json_object"}, "thinking": {"type": "disabled"},
                    "temperature": 0, "max_tokens": self.config.max_tokens}
            record = {"attempt": attempt + 1}
            audit["attempts"].append(record)
            audit["api_calls"] += 1
            try:
                response = self.transport(body)
                choice = response["choices"][0]
                raw = choice["message"]["content"]
                record.update(raw_content=raw, finish_reason=choice.get("finish_reason"),
                              model=response.get("model"), usage=response.get("usage"))
                if choice.get("finish_reason") != "stop":
                    raise ProtocolError("Incomplete model response")
                doc = fold_document(json.loads(raw), text)
                record["status"] = doc["status"]
                # Local row/source problems stay reviewable; no second semantic rewrite.
                return doc, audit
            except HTTPError as exc:
                record["error"] = f"HTTP {exc.code}"
                if exc.code not in {408, 429, 500, 502, 503, 504} or attempt:
                    raise V6Failure(record["error"], audit) from exc
            except (ProtocolError, json.JSONDecodeError, URLError, TimeoutError, OSError, KeyError, IndexError, TypeError) as exc:
                record["error"] = str(exc) if isinstance(exc, (ProtocolError, json.JSONDecodeError)) else type(exc).__name__
                if attempt:
                    raise V6Failure(record["error"], audit) from exc
        raise V6Failure("No complete response", audit)
