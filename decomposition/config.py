"""Versioned protocol and API configuration."""

from dataclasses import dataclass, field
import json
import math
from pathlib import Path
from urllib.parse import urlparse

SCHEMA_VERSION = "entity-facts-v4"
CONTRACT_PATH = Path(__file__).parent / "prompts" / "entity_facts_v4_1_rules.txt"
SHOT_PATH = Path(__file__).parent / "prompts" / "entity_facts_v4_1_shots.jsonl"
PROMPT_VERSION = "entity-facts-v4.1-eight-shot-v1"
API_CONFIG_PATH = Path(__file__).parent / "api_config.local.json"
FACT_TYPES = ("object", "attribute", "action", "relation", "count")


def load_prompt(stage="extract", *, shots=8):
    if stage != "extract":
        raise ValueError("entity-facts-v4 uses one extraction prompt")
    if shots not in {0, 8}:
        raise ValueError("Only the frozen eight-shot prompt or its zero-shot control is supported")
    rules = CONTRACT_PATH.read_text(encoding="utf-8")
    if shots == 0:
        return rules
    from .schemas import validate_document
    examples = [json.loads(line) for line in SHOT_PATH.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(examples) != 8 or len({d['text'] for d in examples}) != 8:
        raise ValueError("Eight-shot file must contain exactly eight distinct caption examples")
    for i, document in enumerate(examples, 1):
        validate_document(document, expected_id="caption")
        rules += (f"\n\nEXAMPLE {i}\nINPUT JSON:\n" + json.dumps({"id":"caption", "text":document["text"]}, ensure_ascii=False)
                  + "\nOUTPUT JSON:\n" + json.dumps(document, ensure_ascii=False, separators=(",", ":")))
    return rules


@dataclass(frozen=True)
class APIConfig:
    model: str
    api_key: str = field(repr=False)
    base_url: str = "https://api.deepseek.com"
    timeout: float = 90.0
    max_tokens: int = 8192
    retries: int = 2
    thinking: str = "disabled"

    def __post_init__(self):
        if any(not isinstance(value, str) for value in (self.model, self.api_key, self.base_url)):
            raise ValueError("model, api_key and base_url must be strings")
        url = urlparse(self.base_url)
        if url.scheme != "https" or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise ValueError("API base URL must be HTTPS without credentials, query or fragment")
        if not self.model.strip() or not self.api_key.strip():
            raise ValueError("Fill api_key and model in decomposition/api_config.local.json (or --api-config FILE)")
        if type(self.timeout) not in (float, int) or not math.isfinite(self.timeout) or self.timeout <= 0:
            raise ValueError("timeout must be a finite positive number")
        if type(self.max_tokens) is not int or type(self.retries) is not int or self.max_tokens < 1 or self.retries < 0:
            raise ValueError("timeout/max_tokens must be positive; retries must be nonnegative")
        if self.thinking != "disabled":
            raise ValueError("Thinking mode is prohibited for this system; use disabled")


def load_api_config(path, **overrides):
    """Explicit local configuration; never silently reuse environment credentials."""
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"API configuration not found: {path}; copy api_config.example.json to api_config.local.json")
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    allowed = {"api_key", "model", "base_url", "timeout", "max_tokens", "retries", "thinking"}
    if not isinstance(data, dict) or set(data) - allowed:
        raise ValueError("API configuration must be an object containing only api_key, model, base_url, timeout, max_tokens, retries, thinking")
    data.update({key: value for key, value in overrides.items() if value is not None})
    data.setdefault("api_key", "")
    data.setdefault("model", "")
    return APIConfig(**data)
