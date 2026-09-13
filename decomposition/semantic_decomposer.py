"""Entity-anchored decomposition; verification remains pending."""
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from .config import SCHEMA_VERSION, load_prompt
from .entity_normalizer import normalize_document
from .quality import repetitive_caption
from .schemas import ValidationError, validate_document
from .source_document import source_sentences
from .storage import digest, write_json


def build_messages(caption, prompt, sentences=None):
    return [{"role": "system", "content": prompt},
            {"role": "user", "content": json.dumps({"id": "caption", "text": caption}, ensure_ascii=False)}]


class DecompositionError(RuntimeError):
    def __init__(self, message, attempts):
        super().__init__(message)
        self.attempts = attempts


class ReviewRequired(DecompositionError):
    def __init__(self, reason, audit):
        super().__init__(reason, audit.get("attempts", []))
        self.audit = audit


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class DeepSeekDecomposer:
    def __init__(self, config, prompt=None, transport=None, sleep=time.sleep,
                 cache_dir=None, bypass_cache=False):
        self.config = config
        self.prompt = prompt if prompt is not None else load_prompt("extract")
        self.transport = transport or self._request
        self.sleep = sleep
        self.cache_dir = Path(cache_dir) if cache_dir is not None else None
        self.bypass_cache = bypass_cache
        code = {p.name: digest(p.read_text(encoding="utf-8")) for p in sorted(Path(__file__).parent.glob("*.py"))}
        self.cache_protocol = {"schema": SCHEMA_VERSION, "code": code,
                               "extract": digest(self.prompt),
                               "model": config.model, "base_url": config.base_url,
                               "max_tokens": config.max_tokens, "thinking": "disabled", "temperature": 0}

    def _request(self, body):
        request = Request(self.config.base_url.rstrip("/") + "/chat/completions",
                          data=json.dumps(body).encode("utf-8"),
                          headers={"Content-Type": "application/json", "Authorization": "Bearer " + self.config.api_key})
        # Do not forward authorization to a redirect target.
        with build_opener(NoRedirect).open(request, timeout=self.config.timeout) as response:
            return json.load(response)

    def decompose(self, caption):
        if not caption.strip():
            return {"id": "caption", "text": caption, "entities": [], "facts": []}, {"attempts": [], "skipped_empty": True, "thinking": "disabled",
                                   "semantic_status": "empty", "cache_hit": False, "api_calls": 0}
        repetition = repetitive_caption(caption)
        if repetition:
            raise ReviewRequired("repetitive_caption", {"attempts": [], **repetition,
                                                       "semantic_status": "not_applicable", "api_calls": 0})
        key = digest({"caption": caption, "protocol": self.cache_protocol})
        path = self.cache_dir / (key + ".json") if self.cache_dir and not self.bypass_cache else None
        if path and path.exists():
            cached = json.loads(path.read_text(encoding="utf-8"))
            if cached.get("key") != key or cached.get("checksum") != digest([cached.get("payload"), cached.get("audit")]):
                raise ValueError("Decomposer cache checksum mismatch")
            validate_document(cached["payload"], expected_text=caption, expected_id="caption")
            return cached["payload"], {**cached["audit"], "cache_hit": True, "api_calls": 0}
        sentences = source_sentences(caption)
        audit = {"attempts": [], "sentences": sentences, "thinking": "disabled", "cache_hit": False,
                 "pipeline": "entity-anchored-extraction;reference-and-source-validation;exact-structured-dedup", "cache_key": key}
        try:
            initial, attempts = self._json_request("extract", build_messages(caption, self.prompt),
                lambda p: validate_document(p, expected_text=caption, expected_id="caption"))
            audit["attempts"].extend(attempts)
            payload, changes = normalize_document(initial)
            validate_document(payload, expected_text=caption, expected_id="caption")
            audit.update(initial=initial, normalization_log=changes, api_calls=len(audit["attempts"]),
                         semantic_status="ready" if payload["facts"] else "no_in_scope_facts",
                         speculative_fact_ids=[f["id"] for f in payload["facts"] if f["assertion"] == "speculative"],
                         no_in_scope_facts=not payload["facts"])
        except ReviewRequired as exc:
            if exc.audit is not audit:
                audit["attempts"].extend(exc.attempts)
                audit["failed_stage"] = exc.audit
            audit["api_calls"] = len(audit["attempts"])
            audit["semantic_status"] = "needs_review"
            raise ReviewRequired(str(exc), audit) from exc
        except DecompositionError as exc:
            exc.attempts = audit["attempts"] + exc.attempts
            exc.audit = {**audit, "attempts": exc.attempts, "api_calls": len(exc.attempts)}
            raise
        if path:
            path.parent.mkdir(parents=True, exist_ok=True)
            # Distinct temporary names make simultaneous same-caption saves atomic.
            from uuid import uuid4
            temporary = path.with_name(path.stem + "." + uuid4().hex + ".json")
            try:
                write_json(temporary, {"key": key, "payload": payload, "audit": audit,
                                       "checksum": digest([payload, audit])})
                temporary.replace(path)
            finally:
                temporary.unlink(missing_ok=True)
        return payload, audit

    def _json_request(self, stage, messages, validator):
        body = {"model": self.config.model, "messages": messages,
                "response_format": {"type": "json_object"}, "thinking": {"type": "disabled"},
                "temperature": 0, "max_tokens": self.config.max_tokens}
        attempts = []
        for number in range(self.config.retries + 1):
            started = time.monotonic()
            attempt = {"stage": stage, "attempt": number + 1,
                       "messages": json.loads(json.dumps(body["messages"])), "thinking": "disabled"}
            retryable = True
            try:
                response = self.transport(body)
                attempt.update(response_id=response.get("id"), model=response.get("model"), usage=response.get("usage"))
                choice = response["choices"][0]
                content = choice["message"]["content"]
                attempt.update(raw_content=content, finish_reason=choice.get("finish_reason"))
                if choice.get("finish_reason") != "stop":
                    raise ValidationError("Incomplete response (finish_reason is not stop)")
                if not isinstance(content, str) or not content.strip():
                    raise ValidationError("API returned empty content")
                try:
                    payload = json.loads(content)
                except ValueError as exc:
                    raise ValidationError("Response is not valid JSON") from exc
                validator(payload)
                attempt["elapsed_seconds"] = round(time.monotonic() - started, 3)
                attempts.append(attempt)
                return payload, attempts
            except HTTPError as exc:
                attempt["error"] = f"API HTTP {exc.code}"
                retryable = exc.code in {408, 429} or 500 <= exc.code < 600
                exc.close()
            except (URLError, TimeoutError, ConnectionError, OSError):
                attempt["error"] = "API network/timeout error"
            except ValidationError as exc:
                attempt.update(error=f"Invalid API response: {exc}", error_kind="protocol")
                # Only validator diagnostics, never another sample or image label.
                previous = [{"role": "assistant", "content": content}] if isinstance(content, str) and content.strip() else []
                body["messages"] = messages + previous + [{"role": "user", "content":
                    "Repair the JSON response above to the same task, changing only the reported problems. "
                    "Preserve the other caption-grounded facts. Validation error: " + str(exc)}]
            except (ValueError, KeyError, IndexError, TypeError, AttributeError):
                attempt.update(error="Invalid API response structure", error_kind="protocol")
            attempt["elapsed_seconds"] = round(time.monotonic() - started, 3)
            attempts.append(attempt)
            if not retryable or number == self.config.retries:
                break
            self.sleep(min(2 ** number, 8))
        if attempts[-1].get("error_kind") == "protocol":
            raise ReviewRequired("protocol_validation", {"stage": stage, "attempts": attempts})
        raise DecompositionError(attempts[-1]["error"], attempts)
