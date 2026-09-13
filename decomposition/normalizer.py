"""Small explicit templates, never fuzzy entailment or implicit completion."""
import re
from .config import FACT_TYPES

EXISTENCE_PLURALS = {
    "people": "person", "men": "man", "women": "woman", "children": "child",
    "cats": "cat", "dogs": "dog", "cars": "car", "horses": "horse", "cows": "cow",
    "surfboards": "surfboard", "forks": "fork", "knives": "knife", "plates": "plate",
    "potted plants": "potted plant", "trees": "tree", "uniforms": "uniform",
}


def normalize_text(kind, text):
    text = " ".join(text.casefold().strip().rstrip(".").split())
    if kind == "object":
        if re.search(r"\b(no|not|never|may|might|could|appears?|seems?|likely|possibly|probably)\b", text):
            return text
        match = re.fullmatch(r"there (?:is|are) (?:a |an )?(.+)", text)
        if match:
            text = match[1] + " exists"
        match = re.fullmatch(r"(.+?) exists?", text)
        if match:
            noun = match[1]
            # Do not singularize numbers, negation, qualified or compound nouns.
            noun = EXISTENCE_PLURALS.get(noun, noun)
            text = noun + (" exist" if noun in {"fries", "clothes", "scissors", "trousers", "shorts"} else " exists")
    elif kind == "relation":
        # Static locative paraphrases only. Do not erase progressive actions,
        # an agent (placed BY...), orientation, negation or arrangement manner.
        text = re.sub(r"\b(is|are) (?:positioned|placed|arranged|located|situated) (on|in|beside|alongside|near|throughout|under|against)\b", r"\1 \2", text)
        text = re.sub(r"\b(on|in|throughout|beside|under|against) the (scene|frame|image|market setting|ground|wall|table|plate)\b", r"\1 \2", text)
        text = text.replace(" is alongside ", " is beside ")
        text = text.replace(" is leaning against ", " leans against ")
    return text


def normalize_candidates(candidates):
    unique, changes = {}, []
    for item in candidates:
        text = normalize_text(item["type"], item["fact"])
        key = (item["type"], text, item["assertion"])
        if text != item["fact"]:
            changes.append({"before": item["fact"], "after": text, "rule": "literal_or_fixed_template"})
        if key in unique:
            unique[key]["source_sentences"] = sorted(set(unique[key]["source_sentences"]) | set(item["source_sentences"]))
            changes.append({"before": item["fact"], "after": text, "rule": "exact_duplicate"})
        else:
            unique[key] = {**item, "fact": text, "source_sentences": sorted(set(item["source_sentences"]))}
    items = [unique[k] for k in sorted(unique, key=lambda k: (FACT_TYPES.index(k[0]), k[1], k[2]))]
    return [{**item, "id": f"f{i}"} for i, item in enumerate(items, 1)], changes
