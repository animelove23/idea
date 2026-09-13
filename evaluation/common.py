import copy
import json
from pathlib import Path
from urllib.error import HTTPError

from decomposition.semantic_decomposer import DeepSeekDecomposer
from decomposition.v6.schema import source_matches


class ContractError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise ContractError(message)


def document_context(document):
    """Allowlist caption semantics only: no image, method, verification or evaluation label."""
    require(isinstance(document, dict) and isinstance(document.get("text"), str), "v6 document text required")
    require(isinstance(document.get("facts"), list), "v6 facts array required")
    fields = ("id", "type", "category", "fact", "source", "assertion", "polarity", "reason")
    facts = []
    ids = set()
    for f in document["facts"]:
        require(isinstance(f, dict) and isinstance(f.get("id"), str) and f["id"] not in ids, "unique fact IDs required")
        require(f.get("type") in {"entity", "attribute", "relation", "other"}, "expected v6 four-class facts")
        require(all(isinstance(f.get(k), str) for k in ["fact", "source", "assertion", "polarity"]), "v6 fact fields required")
        ids.add(f["id"])
        facts.append({k: copy.deepcopy(f[k]) for k in fields if k in f})
    return {"text": document["text"], "facts": facts}


def valid_quote(text, quote):
    if not isinstance(quote, str) or not quote.strip():
        return False
    matches, repair = source_matches(text, quote)
    return bool(matches) and repair is None


class StageFailure(RuntimeError):
    def __init__(self, message, audit):
        super().__init__(message)
        self.audit = audit


class JsonStage:
    """Exactly one request per stage; persist errors instead of rewriting prompts/results."""
    def __init__(self, config=None, transport=None, examples=None):
        self.config = config
        self.transport = transport or DeepSeekDecomposer(config, prompt="unused")._request
        self.examples = examples or {}

    def run(self, stage, payload):
        rules = (Path(__file__).parent / "prompts" / (stage + ".txt")).read_text(encoding="utf-8")
        messages = [{"role": "system", "content": "Return exactly one JSON object.\n\n" + rules}]
        for example in self.examples.get(stage, []):
            messages.extend([{"role": "user", "content": json.dumps(example["input"], ensure_ascii=False)},
                             {"role": "assistant", "content": json.dumps(example["output"], ensure_ascii=False)}])
        messages.append({"role": "user", "content": json.dumps(payload, ensure_ascii=False)})
        body = {"model": self.config.model, "messages": messages,
                "response_format": {"type": "json_object"}, "temperature": 0,
                "thinking": {"type": "disabled"}, "max_tokens": self.config.max_tokens}
        audit = {"stage": stage, "request": copy.deepcopy(body), "api_calls": 1}
        try:
            response = self.transport(body)
            choice = response["choices"][0]
            audit.update(raw_content=choice["message"]["content"], finish_reason=choice.get("finish_reason"),
                         model=response.get("model"), usage=response.get("usage"))
            require(choice.get("finish_reason") == "stop", "incomplete response")
            payload = json.loads(choice["message"]["content"])
            require(isinstance(payload, dict), "JSON object required")
            return payload, audit
        except Exception as exc:
            # Never serialize HTTP bodies/headers that might contain credentials.
            error = str(exc) if isinstance(exc, (ContractError, json.JSONDecodeError)) else type(exc).__name__
            if isinstance(exc, HTTPError):
                audit["http_status"] = exc.code
                error = f"HTTP {exc.code}"
            audit["error"] = error
            raise StageFailure(error, audit) from exc
