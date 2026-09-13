"""Local noun-phrase coverage, with a deliberately small visual vocabulary.

Nouns are candidates, not facts. Only explicit, unqualified nominal mentions in
the supported vocabulary can receive a rule-based existence supplement.
"""
from functools import lru_cache
import re

from .normalizer import normalize_text

VISUAL_HEADS = set("horse person man woman child phone smartphone screen menu keyboard hand thumb fork knife tree wall surfboard cat dog car building table ground floor plate ball racquet uniform sweatshirt broccoli lettuce plant bicycle toast fries salad lemon cow hay grass field shirt jacket bowl cup bottle chair book bus bed window door shoe hat bird boat apple banana orange computer laptop flower".split())
ALIASES = {"smartphone": "phone", "cell phone": "phone", "mobile phone": "phone", "tennis racquet": "racquet",
           "tennis racket": "racquet", "racket": "racquet", "tennis player": "person", "player": "person",
           "people": "person", "potted plant": "plant", "hooded sweatshirt": "sweatshirt", "french toast": "toast",
           "slice of lemon": "lemon slice", "slices of lemon": "lemon slice", "bike": "bicycle"}
COMPOUNDS = ["palm treo smartphone", "tennis racquet", "tennis racket", "tennis player", "cell phone", "mobile phone",
             "potted plant", "hooded sweatshirt", "french toast", "lemon slice", "slice of lemon"]
AGGREGATES = re.compile(r"\b(?:meals?|food|displays?|settings?|piles?|groups?|scenes?|images?|frames?|foreground|background|markets?)\b")
OPERATORS = re.compile(r"\b(?:no|not|never|may|might|could|would|should|will|seems?|appears?|likely|possibly|perhaps|probably|if|unless|without|imagine|imagines?|imagining|wishes?|wants?|needs?|intends?|plans?)\b", re.I)


@lru_cache(maxsize=1)
def parser():
    import spacy
    return spacy.load("en_core_web_md", disable=["ner"])


def object_name(text):
    t = normalize_text("object", text)
    m = re.fullmatch(r"(?:a |an |the )?(.+?) exists?", t)
    return m[1] if m else None


def aggregate_object(text):
    name = object_name(text)
    return bool(name and AGGREGATES.search(name))


def concept(name):
    name = name.lower().strip()
    if name.startswith("palm treo "):
        return "phone"
    return ALIASES.get(name, name)


def _scope_reason(token, sent):
    # Possessor nouns do not assert visibility (a person's hand).
    if token.dep_ == "poss":
        return "possessor_only"
    chain = [token, *token.ancestors]
    for node in chain:
        if node.lower_ in {"without", "before", "after"}:
            return "negative_or_nonassertive"
        if any(c.dep_ == "neg" or c.lower_ in {"no", "neither", "without"} for c in node.children):
            return "negative_or_nonassertive"
        visible_passive = node.lemma_ == "see" and any(c.dep_ == "auxpass" and c.lemma_ == "be" for c in node.children)
        if any((c.tag_ == "MD" and not (c.lower_ == "can" and visible_passive))
               or c.lower_ in {"likely", "possibly", "probably", "perhaps"} for c in node.children):
            return "qualified_or_hypothetical"
        if node.lemma_.lower() in {"imagine", "want", "wish", "need", "intend", "plan", "seem", "appear"}:
            return "qualified_or_hypothetical"
    # Conditional scopes and coordination are not safely discharged locally.
    if re.search(r"\b(?:if|unless)\b", sent, re.I) or any(
            c.lower_ in {"either", "or"} for node in chain for c in node.children):
        return "ambiguous_scope"
    if token.pos_ not in {"NOUN", "PROPN"}:
        return "not_nominal"
    return None


def check_object_coverage(sentences, candidates):
    """Return mentions and warnings before any supplement; never call an LLM."""
    covered = {concept(n) for f in candidates if f["type"] == "object" and f["assertion"] == "assertive"
               for n in [object_name(f["fact"])] if n}
    mentions, warnings = [], []
    for s in sentences:
        doc = parser()(s["text"])
        chunks = list(doc.noun_chunks)
        for token in doc:
            if token.pos_ not in {"NOUN", "PROPN"}:
                continue
            lemma = token.lemma_.lower()
            chunk = next((c for c in chunks if c.start <= token.i < c.end), None)
            phrase = chunk.text if chunk is not None else token.text
            # Do not enumerate the components of a recognized compound noun.
            noun = lemma
            for compound in sorted(COMPOUNDS, key=len, reverse=True):
                words = " ".join(t.lemma_.lower() for t in chunk) if chunk is not None else lemma
                if compound in words:
                    if chunk.root != token:
                        noun = None
                    else:
                        noun = compound
                    break
            # "slice of lemon" crosses a noun-chunk boundary.
            if lemma == "slice" and re.search(r"\bslices? of lemon\b", s["text"], re.I):
                noun = "lemon slice"
            if lemma == "lemon" and token.head.lower_ == "of" and token.head.head.lemma_ == "slice":
                continue
            if noun is None:
                continue
            key = concept(noun)
            reason = _scope_reason(token, s["text"])
            eligible = key in VISUAL_HEADS or key == "lemon slice"
            if AGGREGATES.search(noun):
                reason = "aggregate_or_scene"
            elif not eligible:
                reason = reason or "outside_supported_vocabulary"
            state = "covered" if key in covered else "uncovered"
            item = {"sentence_id": s["sentence_id"], "quote": token.text, "noun_phrase": phrase,
                    "class": noun, "coverage_key": key, "state": state, "scope_reason": reason}
            mentions.append(item)
            if state == "uncovered" and eligible and reason != "aggregate_or_scene":
                warnings.append({**item, "warning": "object_coverage_warning", "resolution": "pending"})
    return {"parser": "en_core_web_md", "parser_version": parser().meta.get("version"),
            "mentions": mentions, "warnings": warnings}


def supplement_objects(sentences, candidates):
    coverage = check_object_coverage(sentences, candidates)
    result = [dict(f) for f in candidates]
    seen = {concept(n) for f in result if f["type"] == "object" and f["assertion"] == "assertive"
            for n in [object_name(f["fact"])] if n}
    for warning in coverage["warnings"]:
        if warning["scope_reason"]:
            warning["resolution"] = "not_added_scope_uncertain"
            continue
        key = warning["coverage_key"]
        if key not in seen:
            name = warning["class"]
            text = name + (" exist" if name == "fries" else " exists")
            result.append({"type": "object", "fact": text, "assertion": "assertive",
                           "source_sentences": [warning["sentence_id"]]})
            seen.add(key)
            warning.update(resolution="added_by_explicit_nominal_rule", added_fact=text)
        else:
            warning["resolution"] = "covered_by_local_supplement"
    return result, coverage
