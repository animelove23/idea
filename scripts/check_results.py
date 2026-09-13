"""Recompute published matrices from per-pair observations, without a model."""
import csv,json
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'results/coco400_revision_v2_guard'
def main():
    results={}
    for phase in ['A_scope_only','B_alignment','B2_local_and_rebinding','C_reviewed']:
        base=ROOT/phase
        rows=[json.loads(l) for l in (base/'observation_pairs.jsonl').read_text(encoding='utf-8').splitlines() if l.strip()]
        summary=json.loads((base/'summary.json').read_text(encoding='utf-8'))
        assert len(rows)==len({r['pair_id'] for r in rows})==summary['pairs']==400
        counts=Counter((r['length_group'],r['hallucination_change'],r['supported_change']) for r in rows if r['matrix_classifiable'])
        lengths=Counter(r['length_group'] for r in rows)
        assert sum(counts.values())==summary['matrix_classifiable']
        assert 400-sum(counts.values())==summary['matrix_unresolved']
        with (base/'matrix.csv').open(encoding='utf-8-sig',newline='') as f:
            exported=list(csv.DictReader(f))
        seen=set()
        for r in exported:
            key=(r['length_group'],r['H'],r['S']);n=int(r['count']);den=int(r['denominator'])
            assert key not in seen;seen.add(key)
            assert n==counts[key] and den==lengths[key[0]]
            assert abs(float(r['fraction'])-n/den)<1e-12
            ids=json.loads(r['pair_ids'])
            expected=[p['pair_id'] for p in rows if p['matrix_classifiable'] and (p['length_group'],p['hallucination_change'],p['supported_change'])==key]
            assert sorted(ids)==sorted(expected)
        assert all(key in seen for key in counts)
        results[phase]={'pairs':400,'classifiable':sum(counts.values()),'unresolved':400-sum(counts.values())}
    print(json.dumps({'verified':results,'upstream_semantic_accuracy_verified':False},indent=2))

if __name__=='__main__':main()
