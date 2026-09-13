"""Caption-level POS statistics independent of semantic facts."""
from collections import Counter
from .schemas import POS_TAGS

class SpacyParser:
    def __init__(self, model="en_core_web_md"):
        try:
            import spacy
            self.nlp = spacy.load(model, disable=["ner"])
        except (ImportError, OSError) as exc:
            raise RuntimeError(f"Install requirements and run: python -m spacy download {model}") from exc
        probe = self.nlp("A red car is beside a blue bus.")
        if not probe.has_annotation("POS") or not probe.has_annotation("SENT_START"):
            raise RuntimeError("spaCy pipeline must provide POS and sentence boundaries")
        self.identity = {"spacy_version": spacy.__version__, "model": model,
                         "model_version": self.nlp.meta.get("version"), "pipes": self.nlp.pipe_names}

    def parse(self, caption):
        doc = self.nlp(caption)
        counts = Counter(t.pos_ for t in doc if not t.is_space)
        sentences = sum(any(not t.is_space for t in sent) for sent in doc.sents)
        return {f"{tag}_count": counts[tag] for tag in POS_TAGS}, sentences
