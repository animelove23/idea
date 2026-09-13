"""Coverage never alters the input; accepted additions have stable, disjoint IDs."""
import copy
from decomposition.storage import digest
from decomposition.v6.schema import fold_document
from .common import ContractError, StageFailure, document_context, require


def apply_coverage(document, response):
    document_context(document)
    require(isinstance(response, dict) and set(response) == {"added_elements"} and isinstance(response["added_elements"], list),
            "coverage may return added_elements only")
    original = copy.deepcopy(document)
    if not response["added_elements"]:
        return {"caption_id": document["id"], "status": "ready", "added_facts": [], "rejected_additions": [],
                "input_digest": digest(document), "augmented_document": original}
    parsed = fold_document({"elements": response["added_elements"]}, document["text"])
    additions, rejected = [], copy.deepcopy(parsed["invalid_elements"])
    existing_ids = {f["id"] for f in document["facts"]}
    # Only reject exact duplicates with the same grounding/qualifiers. Never rewrite an existing fact.
    def key(f):
        return tuple(f.get(k) for k in ("type", "fact", "source", "assertion", "polarity"))
    existing = {key(f) for f in document["facts"]}
    for fact in parsed["facts"]:
        if fact["source_status"] != "verified":
            rejected.append({"candidate": fact, "errors": ["source must be uniquely grounded; keep as rejected candidate"]})
            continue
        if key(fact) in existing:
            rejected.append({"candidate": fact, "errors": ["duplicate_existing_or_added_fact"]})
            continue
        i = len(additions) + 1
        while f"cov_f{i}" in existing_ids:
            i += 1
        addition = {**fact, "id": f"cov_f{i}", "added_by_coverage": True}
        existing_ids.add(addition["id"]); existing.add(key(addition)); additions.append(addition)
    original["facts"] = copy.deepcopy(document["facts"]) + additions
    require(original["facts"][:len(document["facts"])] == document["facts"], "existing facts changed")
    return {"caption_id": document["id"], "status": "needs_review" if rejected else "ready",
            "added_facts": additions, "rejected_additions": rejected,
            "input_digest": digest(document), "augmented_document": original,
            "local_repairs": parsed["local_repairs"]}


class CoverageAudit:
    def __init__(self, stage):
        self.stage = stage

    def run(self, document):
        payload = document_context(document)
        audit = {"api_calls": 0}
        try:
            if not document["text"].strip():
                response = {"added_elements": []}
            else:
                response, audit = self.stage.run("coverage", payload)
            result = apply_coverage(document, response)
            result["audit"] = audit
            return result
        except (ContractError, StageFailure) as exc:
            return {"caption_id": document["id"], "status": "failed", "added_facts": [],
                    "rejected_additions": [], "input_digest": digest(document),
                    "augmented_document": copy.deepcopy(document), "error": str(exc),
                    "audit": exc.audit if isinstance(exc, StageFailure) else audit}
