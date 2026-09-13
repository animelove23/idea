"""Fixed-reference core metrics: abstaining on an evaluable fact remains a miss."""
import copy
from collections import Counter
from .reference_metrics import compute, prf, rowkey, TECHNICAL

CORE = ('retained', 'removed', 'added', 'modified')


def score(reference, predictions):
    full, errors, frr = compute(reference, predictions, states=CORE + ('other',))
    gold_edges = set(); predicted_edges = set(); gold_joint = set(); predicted_joint = set()
    gm = {}; pm = {}; excluded_reasons = Counter()
    for pair in reference:
        for r in pair['fact_alignment']:
            if r['status'] in CORE:
                gold_edges.add(rowkey(pair['pair_id'], r)); gold_joint.add(rowkey(pair['pair_id'], r, True))
            for side in ('original', 'steer'):
                for fid in r[side + '_fact_ids']: gm[pair['pair_id'], side, fid] = r
    for pair in predictions:
        for r in pair['fact_alignment']:
            if r['status'] in CORE and r['reason'] not in TECHNICAL:
                # Includes confident predictions on gold-other items as false positives.
                predicted_edges.add(rowkey(pair['pair_id'], r)); predicted_joint.add(rowkey(pair['pair_id'], r, True))
            for side in ('original', 'steer'):
                for fid in r[side + '_fact_ids']:
                    pm[pair['pair_id'], side, fid] = r
                    if r['status'] == 'other': excluded_reasons[r['reason']] += 1
    false_exclusions = sum(g['status'] in CORE and (k not in pm or pm[k]['status'] == 'other') for k, g in gm.items())
    core_gold = sum(r['status'] in CORE for r in gm.values())
    other_count = sum(r['status'] == 'other' for r in pm.values())
    reference_other = sum(r['status'] == 'other' for r in gm.values())
    excluded_nonfailure = sum(r['status'] == 'other' and r['reason'] not in TECHNICAL for r in pm.values())
    full.update(
        core_edge=prf(len(gold_edges & predicted_edges), len(predicted_edges), len(gold_edges)),
        core_joint=prf(len(gold_joint & predicted_joint), len(predicted_joint), len(gold_joint)),
        core_status_macro_f1=sum(full['status_per_class'][s]['f1'] or 0 for s in CORE)/len(CORE),
        exclusions={'reference_other': reference_other, 'predicted_other': other_count,
                    'predicted_other_rate': other_count / len(gm) if gm else None,
                    'semantic_other': excluded_nonfailure, 'technical_other': other_count-excluded_nonfailure,
                    'reference_core': core_gold, 'false_exclusions': false_exclusions,
                    'false_exclusion_rate_on_reference_core': false_exclusions/core_gold if core_gold else None,
                    'reasons': dict(excluded_reasons)},
        metrics_policy='Fixed reference enrollment: predicted other/technical failures on core gold remain false negatives. Confident core predictions on gold other remain false positives. Never filter both sides by model acceptance.')
    return full, errors, frr


def legacy_predictions(rows):
    """Only rename old uncertainty to other; do not repair old model decisions."""
    result = copy.deepcopy(rows)
    for pair in result:
        for r in pair['fact_alignment']:
            if r['status'] == 'ambiguous': r['status'] = 'other'
    return result
