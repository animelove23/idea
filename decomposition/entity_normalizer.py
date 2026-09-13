"""Exact dedup by local identity; same canonical NEVER merges instances."""
import copy
import json

def normalize_document(payload):
    result = copy.deepcopy(payload)
    seen, facts, changes = {}, [], []
    for fact in result["facts"]:
        identity = {k: v for k, v in fact.items() if k not in {"id", "source", "verification"}}
        if isinstance(identity.get("target"), list): identity["target"] = sorted(identity["target"])
        key = json.dumps(identity, sort_keys=True, ensure_ascii=False)
        if key in seen:
            changes.append({"rule": "same_entity_structured_duplicate", "removed_id": fact["id"], "kept_id": seen[key], "source": fact["source"]})
        else:
            seen[key] = fact["id"]
            facts.append(fact)
    result["facts"] = facts
    return result, changes
