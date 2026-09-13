"""Frozen deterministic candidate-reference scoring; no LLM judge or substring fact credit."""
from collections import Counter
from .common import ratio


def prf(tp, predicted, reference):
    p, r = ratio(tp, predicted), ratio(tp, reference)
    return {"tp":tp,"predicted":predicted,"reference":reference,"precision":p,"recall":r,
            "f1": ratio(2*tp,predicted+reference)}


def matching(pred, ref, equal):
    assigned = {}
    def visit(i, seen):
        for j, gold in enumerate(ref):
            if j in seen or not equal(pred[i],gold):
                continue
            seen.add(j)
            if j not in assigned or visit(assigned[j], seen):
                assigned[j] = i
                return True
        return False
    for i in range(len(pred)):
        visit(i,set())
    return [(i,j) for j,i in assigned.items()]


def overlap(a,b):
    return any(x["start"] < y["end"] and y["start"] < x["end"] for x in a for y in b)


ALIASES = {"flowers":"flower","glasses":"glasses","carrots":"carrot","radishes":"radish",
           "vegetables":"vegetable","tattoos":"tattoo","wooden":"wood"}


def normal(value):
    value = value.lower().strip()
    return ALIASES.get(value,value)


def score_documents(pred, ref):
    ematches = matching(pred["entities"],ref["entities"],
                        lambda a,b: normal(a["name"]) == normal(b["name"]) and overlap(a["mentions"],b["mentions"]))
    entity_map = {pred["entities"][i]["id"]:ref["entities"][j]["id"] for i,j in ematches}
    def same(a,b):
        return (a["type"] == b["type"] and a["slot"] == b["slot"] and normal(a["value"]) == normal(b["value"])
                and entity_map.get(a["entity_id"]) == b["entity_id"])
    pairs = matching(pred["facts"],ref["facts"],same)
    per_type = {}
    for kind in ("entity","attribute"):
        per_type[kind] = prf(sum(pred["facts"][i]["type"] == kind for i,j in pairs),
                            sum(f["type"] == kind for f in pred["facts"]),sum(f["type"] == kind for f in ref["facts"]))
    return {"joint":prf(len(pairs),len(pred["facts"]),len(ref["facts"])),"by_type":per_type,
            "unmatched_prediction":[f for i,f in enumerate(pred["facts"]) if i not in {a for a,b in pairs}],
            "unmatched_reference":[f for j,f in enumerate(ref["facts"]) if j not in {b for a,b in pairs}],
            "issues":len(pred["issues"])}


def aggregate_documents(scores):
    out = {}
    for kind in ("joint","entity","attribute"):
        rows = [s["joint"] if kind == "joint" else s["by_type"][kind] for s in scores]
        out[kind] = prf(sum(x["tp"] for x in rows),sum(x["predicted"] for x in rows),sum(x["reference"] for x in rows))
    return out
