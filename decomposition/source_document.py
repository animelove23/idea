"""Sentence provenance only. No semantic token indices or fact/POS alignment."""
from functools import lru_cache


@lru_cache(maxsize=1)
def _sentencizer():
    from spacy.lang.en import English
    nlp = English()
    nlp.add_pipe("sentencizer")
    return nlp


def source_sentences(caption):
    return [{"sentence_id": f"s{i}", "text": text}
            for i, text in enumerate((s.text.strip() for s in _sentencizer()(caption).sents
                                      if s.text.strip()), 1)]
