"""Re-run current local processing with recorded responses, with zero API calls.

Every request's messages must exactly match the recorded request. New prompts or
changed repair requests cannot silently reuse old responses. Manifest records
source provenance; these are NOT new independent model runs.
"""
import argparse
import copy
import json
from pathlib import Path

from decomposition.caption_parser import normalize_caption
from decomposition.config import APIConfig, load_prompt
from decomposition.pos_parser import SpacyParser
from decomposition.run_decomposition import run_pipeline
from decomposition.semantic_decomposer import DeepSeekDecomposer, ReviewRequired
from decomposition.storage import digest
from tests.evaluate_minimal import load_run


def replay(source, output):
    old = json.loads((source / "run_manifest.json").read_text(encoding="utf-8"))
    protocol = copy.deepcopy(old["protocol"])
    assert protocol["prompt_sha256"] == digest(load_prompt()), "Prompt changed: cannot replay"
    code = Path(__file__).resolve().parents[1] / "decomposition"
    protocol["code_hashes"] = {p.name: digest(p.read_text(encoding="utf-8")) for p in sorted(code.glob("*.py"))}
    samples = load_run(source)
    records = [normalize_caption(d["caption"], source_file=d["caption"].get("source_file", ""), source_line=d["caption"].get("source_line", 0)) for d in samples.values()]
    manifest = {**old, "protocol": protocol, "replay_of": str(source.resolve()),
                "source_fingerprint": old["fingerprint"], "source_api_calls": sum(d.get("audit", {}).get("api_calls", 0) for d in samples.values()),
                "replay_zero_network": True}
    manifest["fingerprint"] = digest({"protocol": protocol, "records": records, "replay_of": manifest["replay_of"]})
    by_caption = {d["caption"]["caption"]: d for d in samples.values()}

    class Replayer:
        def decompose(self, caption):
            saved = by_caption[caption]
            attempts = iter(saved.get("audit", {}).get("attempts", []))
            def transport(body):
                attempt = next(attempts)
                assert body["messages"] == attempt["messages"], "Request changed; new API test required"
                assert "raw_content" in attempt, "Network failures cannot be replayed as model responses"
                return {"id": attempt.get("response_id"), "model": attempt.get("model"), "usage": attempt.get("usage"),
                        "choices": [{"message": {"content": attempt["raw_content"]}, "finish_reason": attempt["finish_reason"]}]}
            config = APIConfig(protocol["model"], "unused-offline", base_url=protocol["base_url"], max_tokens=protocol["max_tokens"])
            client = DeepSeekDecomposer(config, transport=transport, sleep=lambda _: None, bypass_cache=True)
            try:
                payload, audit = client.decompose(caption)
            except ReviewRequired as exc:
                audit = exc.audit
                audit.update(replayed_response_count=audit.get("api_calls", 0), api_calls=0, replay_of=manifest["replay_of"])
                raise
            audit.update(replayed_response_count=audit["api_calls"], api_calls=0, replay_of=manifest["replay_of"])
            return payload, audit

    return run_pipeline(records, [], SpacyParser("en_core_web_md"), Replayer(), output,
                        manifest=manifest, prompt=load_prompt())


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("source", type=Path)
    cli.add_argument("output", type=Path)
    args = cli.parse_args()
    print(json.dumps(replay(args.source, args.output)))
