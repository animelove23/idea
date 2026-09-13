"""Future visual verifier contract; this release deliberately performs no model/image work."""
from typing import Any, Literal, Protocol, TypedDict


class VerificationResult(TypedDict):
    claim_id: str
    fact_ids: list[str]
    label: Literal["pending", "supported", "hallucinated", "uncertain"]
    evidence: Any


class VisualVerifier(Protocol):
    def verify_claim(self, image: Any, fact: dict, entity_context: dict) -> VerificationResult: ...


class PendingVerifier:
    def verify_claim(self, image, fact, entity_context):
        # No image read, network access or hallucination decision.
        return {"claim_id": entity_context["claim_id"], "fact_ids": list(entity_context["fact_ids"]),
                "label": "pending", "evidence": None}


def pending_claims(pair_id, original, steer):
    verifier = PendingVerifier()
    result = []
    for side, document in [("original", original), ("steer", steer)]:
        for fact in document["facts"]:
            qualified = f"{side}:{fact['id']}"
            value = verifier.verify_claim(None, fact, {"claim_id": f"{pair_id}:{qualified}", "fact_ids": [qualified]})
            result.append({"pair_id": pair_id, "side": side, "fact": fact["fact"],
                           "in_main": fact["type"] != "other", **value})
    return result
