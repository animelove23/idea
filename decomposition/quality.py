"""Repetition detection and literal deduplication only; no inferred facts."""
import re
from .config import FACT_TYPES

def repetitive_caption(caption):
    words = re.findall(r"\w+", caption.casefold())
    if len(words) < 12:
        return None
    for width in range(1, 4):
        motif = words[:width]
        if all(word == motif[i % width] for i, word in enumerate(words)):
            return {"reason": "repetitive_caption", "word_count": len(words), "motif": motif}
    return None

def normalized_text(text):
    return " ".join(text.casefold().strip().rstrip(".").split())

def semantic_signature(fact):
    return fact["type"], normalized_text(fact["fact"])

def canonical_payload(payload):
    # Never merge synonyms, infer counts, or collapse different relations.
    unique = {}
    for fact in payload["facts"]:
        unique.setdefault(semantic_signature(fact), fact)
    keys = sorted(unique, key=lambda k: (FACT_TYPES.index(k[0]), k[1]))
    return {"facts": [{"id": f"f{i}", "type": key[0], "fact": unique[key]["fact"].strip()}
                      for i, key in enumerate(keys, 1)]}
