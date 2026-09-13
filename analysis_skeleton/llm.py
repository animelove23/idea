"""Single-call few-shot JSON stage. Reuse authenticated transport; no repair/retry loops."""
import copy
import json
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlparse

from decomposition.config import load_api_config
from decomposition.semantic_decomposer import DeepSeekDecomposer
from .common import read_jsonl, sha

ROOT = Path(__file__).parent


class CallFailure(RuntimeError):
    def __init__(self, audit):
        super().__init__(audit["error"])
        self.audit = audit


class FewShotStage:
    def __init__(self, stage, config_path="decomposition/api_config.local.json", transport=None, model=None):
        self.stage = stage
        self.config = load_api_config(config_path, retries=0, model=model)
        if urlparse(self.config.base_url).hostname != "api.deepseek.com":
            raise ValueError("This experiment is restricted to the user's official DeepSeek configuration")
        self.transport = transport or DeepSeekDecomposer(self.config, prompt="unused")._request
        self.rules_path = ROOT / "prompts" / (stage + ".txt")
        self.shots_path = ROOT / "shots" / (stage + ".jsonl")
        self.rules = self.rules_path.read_text(encoding="utf-8")
        self.shots = read_jsonl(self.shots_path)
        expected = {"decompose": 8, "align": 8, "verify": 6}[stage]
        if len(self.shots) != expected:
            raise ValueError(f"Frozen {expected}-shot required")
        self.identity = {"model": self.config.model, "base_url": self.config.base_url,
                         "temperature": 0, "thinking": "disabled", "max_tokens": self.config.max_tokens,
                         "retries": 0, "shots": len(self.shots), "prompt_sha": sha(self.rules_path),
                         "shots_sha": sha(self.shots_path)}

    def messages(self, payload):
        messages = [{"role": "system", "content": self.rules}]
        for ex in self.shots:
            messages += [{"role": "user", "content": json.dumps(ex["input"], ensure_ascii=False)},
                         {"role": "assistant", "content": json.dumps(ex["output"], ensure_ascii=False)}]
        return messages + [{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}]

    def run(self, payload):
        body = {"model": self.config.model, "messages": self.messages(payload),
                "response_format": {"type": "json_object"}, "temperature": 0,
                "thinking": {"type": "disabled"}, "max_tokens": self.config.max_tokens}
        audit = {"stage": self.stage, "identity": self.identity, "api_calls": 1,
                 "input": copy.deepcopy(payload)}
        start = time.monotonic()
        try:
            response = self.transport(body)
            choice = response["choices"][0]
            audit.update(response_id=response.get("id"), response_model=response.get("model"),
                         usage=response.get("usage"), raw_content=choice["message"].get("content"),
                         finish_reason=choice.get("finish_reason"))
            if choice.get("finish_reason") != "stop":
                raise ValueError("incomplete_response")
            result = json.loads(audit["raw_content"])
            if not isinstance(result, dict):
                raise ValueError("json_object_required")
            audit["elapsed_seconds"] = time.monotonic() - start
            return result, audit
        except Exception as exc:
            # No HTTP body/header/credential serialization.
            audit["error"] = f"HTTP {exc.code}" if isinstance(exc, HTTPError) else type(exc).__name__
            audit["elapsed_seconds"] = time.monotonic() - start
            raise CallFailure(audit) from None
