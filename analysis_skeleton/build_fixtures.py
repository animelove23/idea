"""Author-maintained candidate examples, NOT independent human gold. Never called by runners."""
from pathlib import Path
from .common import write_jsonl, read_jsonl
from .contracts import normalize_document

ROOT = Path(__file__).parent


def q(text, occurrence=0):
    return {"quote": text, "occurrence": occurrence}


def E(i, name, *mentions):
    return {"id": i, "name": name, "mentions": [q(m) if isinstance(m, str) else m for m in mentions]}


def A(i, e, slot, value, evidence, value_quote):
    return {"id": i, "entity_id": e, "slot": slot, "value": value,
            "evidence": [q(evidence)], "value_quotes": [q(value_quote)]}


def D(entities, attributes=(), excluded=()):
    return {"entities": list(entities), "attributes": list(attributes),
            "excluded": [{"source": q(s), "reason": r} for s, r in excluded]}


def build():
    examples = [
        ("A car.", D([E("e1", "car", "car")])),
        ("A small red car.", D([E("e1", "car", "car")], [A("a1","e1","size","small","small red car","small"), A("a2","e1","color","red","red car","red")])),
        ("A wooden table.", D([E("e1","table","table")], [A("a1","e1","material","wood","wooden table","wooden")])),
        ("A round table made of wood.", D([E("e1","table","table")], [A("a1","e1","shape","round","round table","round"), A("a2","e1","material","wood","table made of wood","wood")])),
        ("An open door beside a chair.", D([E("e1","door","door"),E("e2","chair","chair")], [A("a1","e1","state","open","open door","open")], [("beside a chair","relation")])),
        ("A dog is running beside a wet bench.", D([E("e1","dog","dog"),E("e2","bench","bench")], [A("a1","e2","state","wet","wet bench","wet")], [("running","action"),("beside a wet bench","relation")])),
        ("Two dogs stand beside a beautiful car.", D([E("e1","dog","dogs"),E("e2","car","car")], [], [("Two","count"),("stand","action"),("beside a beautiful car","relation"),("beautiful","subjective")])),
        ("A red car is parked. The car is red. It may be blue. It is not green.", D([E("e1","car",q("car",0),q("car",1))],
             [{"id":"a1","entity_id":"e1","slot":"color","value":"red","evidence":[q("red car"),q("The car is red")],"value_quotes":[q("red",0),q("red",1)]}],
             [("parked","action"),("It may be blue","nonasserted"),("It is not green","nonasserted")]))]
    shots = []
    for i, (text, raw) in enumerate(examples):
        assert not normalize_document(raw, text)["issues"], text
        shots.append({"example_id": f"d{i+1}", "reference_status": "assistant_authored_candidate",
                      "input": {"text": text}, "output": raw})
    (ROOT / "shots").mkdir(exist_ok=True)
    write_jsonl(ROOT / "shots/decompose.jsonl", shots)
    # Controlled boundary checks use distinct surface sentences; not natural-distribution validation.
    cases = [
        ("boundary_01", "A blue ceramic bowl is broken.", D([E("e1","bowl","bowl")], [A("a1","e1","color","blue","blue ceramic bowl","blue"), A("a2","e1","material","ceramic","ceramic bowl","ceramic"),A("a3","e1","state","broken","bowl is broken","broken")])),
        ("boundary_02", "Three cats are sleeping near a square box.", D([E("e1","cat","cats"),E("e2","box","box")], [A("a1","e2","shape","square","square box","square")], [("Three","count"),("sleeping","action"),("near a square box","relation")])),
        ("boundary_03", "The bag is not black. It might be green.", D([E("e1","bag","bag")], [], [("The bag is not black","nonasserted"),("It might be green","nonasserted")])),
        ("boundary_04", "An intact glass bottle is near a large basket.", D([E("e1","bottle","bottle"),E("e2","basket","basket")], [A("a1","e1","state","intact","intact glass bottle","intact"),A("a2","e1","material","glass","glass bottle","glass"),A("a3","e2","size","large","large basket","large")], [("near a large basket","relation")]))]
    rows = []
    for cid, text, raw in cases:
        assert not normalize_document(raw,text)["issues"]
        rows.append({"case_id":cid,"text":text,"reference":raw,"reference_status":"assistant_candidate",
                     "split":"synthetic_boundary_development","family":"not_generalization_evidence"})
    (ROOT / "fixtures").mkdir(exist_ok=True)
    write_jsonl(ROOT / "fixtures/decompose_cases.jsonl", rows)
    roster = {p["pair_id"]:p for p in read_jsonl("outputs/skeleton_v1/m0_resolved/pairs.jsonl")}
    real = [
        ("150639","steer",D([E("e1","man","man"),E("e2","glasses","glasses"),E("e3","phone","phone"),E("e4","car","car"),E("e5","people","people")],
                              [A("a1","e3","color","red","red phone","red")])),
        ("337055","steer",D([E("e1","woman","woman"),E("e2","tattoo","tattoos"),E("e3","glasses","glasses"),E("e4","suitcase","suitcase")])),
        ("397351","steer",D([E("e1","man","man"),E("e2","table","table"),E("e3","vegetable","vegetables"),E("e4","carrot","carrots"),E("e5","radish","radishes"),E("e6","apron","apron")],
                              [A("a1","e6","color","green","green apron","green")])),
        ("360487","original",D([E("e1","vase","vase"),E("e2","flower","flowers"),E("e3","table","table")],
                                 [A("a1","e1","color","green","green glass vase","green"),A("a2","e1","material","glass","glass vase","glass"),
                                  A("a3","e2","color","white","white flowers","white"),A("a4","e3","material","wood","wooden table","wooden")]))]
    for iid,side,raw in real:
        text=roster[iid][side]["text"]
        assert not normalize_document(raw,text)["issues"]
        rows.append({"case_id":iid+"_"+side,"text":text,"reference":raw,"reference_status":"assistant_candidate",
                     "split":"real_development","family":iid})
    write_jsonl(ROOT / "fixtures/decompose_pilot.jsonl",rows)


if __name__ == "__main__":
    build()
