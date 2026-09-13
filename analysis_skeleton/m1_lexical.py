"""M1: extend existing spaCy loader with inspectable token records; no LLM input features."""
import argparse
from collections import Counter
from pathlib import Path

from decomposition.pos_parser import SpacyParser
from decomposition.quality import repetitive_caption
from .common import new_run, read_jsonl, write_jsonl, write_csv, report, ratio, digest


class LexicalRecorder(SpacyParser):
    def record(self, caption_id, text):
        doc = self.nlp(text)
        sent_ids = {t.i: sid for sid, sent in enumerate(doc.sents) for t in sent}
        words = [t for t in doc if not t.is_space and not t.is_punct]
        positions = {t.i: i for i, t in enumerate(words)}
        tokens = [{"caption_id": caption_id, "token_id": t.i, "text": t.text,
                   "lemma": t.lemma_, "upos": t.pos_, "char_start": t.idx, "char_end": t.idx + len(t.text),
                   "is_punct": t.is_punct, "word_index": positions.get(t.i),
                   "relative_position": (positions[t.i] + .5) / len(words) if t.i in positions else None,
                   "sentence_id": sent_ids[t.i]} for t in doc if not t.is_space]
        counts = Counter(t.pos_ for t in words)
        row = {"caption_id": caption_id, "text": text, "word_len": len(words),
               "sentence_count": sum(any(not t.is_space for t in s) for s in doc.sents),
               "empty": not text.strip(), "degenerate_repetition": bool(repetitive_caption(text)),
               "pos_counts": dict(counts), "pos_per100": {k: 100*v/len(words) for k, v in counts.items()},
               "lemma_counts": dict(Counter(t.lemma_.casefold() for t in words)),
               "model_token_len": None, "stop_reason": "unknown"}
        return {"caption": row, "tokens": tokens}


def build(pairs_path, output):
    parser = LexicalRecorder()
    out = new_run(output, "M1", [pairs_path], {"nlp": parser.identity, "word_rule": "not_space_and_not_punct"},
                  [__file__, Path("decomposition/pos_parser.py"), Path("decomposition/quality.py")])
    results, valid, total, repeat_ok = [], 0, 0, 0
    for pair in read_jsonl(pairs_path):
        for side in ("original", "steer"):
            caption = pair[side]
            if caption is None:
                continue
            item = parser.record(caption["caption_id"], caption["text"])
            item["caption"].update(pair_id=pair["pair_id"], side=side)
            for t in item["tokens"]:
                total += 1
                valid += caption["text"][t["char_start"]:t["char_end"]] == t["text"]
            if len(results) < 20:
                other = parser.record(caption["caption_id"], caption["text"])
                repeat_ok += digest(item["tokens"]) == digest(other["tokens"])
            results.append(item)
    write_jsonl(out / "lexical.jsonl", results)
    rows = [r["caption"] for r in results]
    write_csv(out / "captions.csv", list(rows[0]) if rows else ["caption_id"], rows)
    metrics = {"captions": len(results), "tokens": total, "source_slice_correct": valid,
               "source_slice_accuracy": ratio(valid, total), "repeat_captions": min(20,len(results)),
               "repeat_identical": repeat_ok, "empty": sum(r["empty"] for r in rows),
               "repetition": sum(r["degenerate_repetition"] for r in rows),
               "pos_human_accuracy": None, "lemma_human_accuracy": None}
    report(out, "M1 粗粒度记录：真实数据完整性", metrics,
           ["复用既有SpacyParser模型加载和重复退化检测，未增加LLM。",
            "逐词偏移/统计通过不证明POS正确；尚无独立人工词性/lemma金标，准确率明确N/A。",
            "词数排除标点，不能与历史len(words)未经重算直接比较；模型token长度未知。"])
    return metrics


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--pairs", required=True)
    p.add_argument("--output", required=True)
    a = p.parse_args()
    print(build(a.pairs, a.output))
