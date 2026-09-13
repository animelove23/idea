"""Narrow guards for the published protocol. They reject; never invent facts."""
import re
from .normalizer import normalize_text
from .schemas import ValidationError

MODAL = re.compile(r"\b(no|not|never|may|might|could|seems?|appears?|likely|possibly|probably|or|if|before|after)\b")


def policy_issues(facts, sentences, coverage=False):
    lookup = {s["sentence_id"]: s["text"] for s in sentences}
    issues = []
    for f in facts:
        t, kind = normalize_text(f["type"], f["fact"]), f["type"]
        if re.search(r"\b(?:belongs? to|owned by|part of)\b", t):
            issues.append("ownership/part-of facts are outside v2; remove them, do not rename them")
        if kind != "relation" and re.search(r"\b(?:holds?|wears?|is holding|are holding|is wearing|are wearing)\b", t):
            issues.append("holding and wearing MUST be relation, with the held/worn object retained")
        if kind == "relation" and re.search(r"\bwears? (?:(?:a|an|the) )?(?:red|white|blue|black|green|yellow|small|large)\b", t):
            issues.append("split clothing property from wearing: wears uniform + uniform worn by wearer is white")
        if kind == "action" and re.search(r"\b(?:is holding|are holding|is displaying|are displaying)$", t):
            issues.append("bare holding/displaying without its object is not an independent assertion")
        if kind == "action" and re.match(r"(?:a |the |another |one )?(?:surfboard|board|wall|building|table)\b.*\b(?:leans?|leaning|lies?|lying)\b", t):
            issues.append("inanimate leaning/lying is spatial relation; do not add a separate action")
        if kind == "action" and re.match(r"(?:a |the )?(?:phone|smartphone|screen)\b.*\b(?:displays?|displaying)\b", t):
            issues.append("a phone/screen displaying content is relation; retain the displayed content")
        if kind == "action" and re.search(r"\b(?:is|are) (?:placed|positioned|arranged|displayed|located|situated)\b", t):
            issues.append("static placement/display is relation, not action; retain location separately from count; omit a bare redundant display claim")
        if kind == "object" and re.fullmatch(r"(?:a |the )?(?:image|frame|scene|foreground|background) exists?", t):
            issues.append("image/frame/scene/foreground/background are not object classes in this protocol")
        if kind == "object" and t == "person exists":
            source = " ".join(lookup[s] for s in f["source_sentences"]).lower()
            without_possessives = re.sub(r"\bperson['’]s\b", "", source)
            if re.search(r"\bperson['’]s\b", source) and not re.search(r"\b(?:person|people)\b", without_possessives):
                issues.append("a person's hand/thumb alone does not explicitly describe a whole visible person")
        if re.search(r"\b(?:in focus|out of focus)\b", t) or re.search(r"(?:scene|image|photo).*\bblurred\b", t):
            issues.append("photographic focus/scene blur is excluded from v2")
        if kind == "object" and f["assertion"] == "qualified":
            source = " ".join(lookup[s] for s in f["source_sentences"]).lower()
            if re.search(r"\b(?:may|might|could) exist\b", t) and not re.search(r"\b(?:exist|exists|present|visible)\b", source):
                issues.append("do not infer possible existence from a qualified activity; preserve the activity's scope")
    return sorted(set(issues))


def enforce_policy(facts, sentences, coverage=False):
    issues = policy_issues(facts, sentences, coverage)
    if issues:
        raise ValidationError("; ".join(issues))
