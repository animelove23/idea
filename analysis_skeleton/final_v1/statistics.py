"""Deterministic strict-parent summaries of the unchanged production ledger.

Only original-side supported facts define retention/removal denominators. This
does not establish model accuracy or reconstruct facts omitted by decompose.
"""
from collections import Counter


TRANSITIONS = ('retained', 'removed', 'modified', 'unresolved')


def _attribute_eligible(row):
    return (row.get('strict_parent_supported_eligible') is True
            and row.get('visual_label') == 'supported'
            and row.get('parent_visual_label') == 'supported'
            and not row.get('truth_conflict', False))


def _supported_summary(rows, kind):
    if kind == 'attribute':
        supported = [row for row in rows if _attribute_eligible(row)]
    else:
        supported = [row for row in rows if row.get('visual_label') == 'supported'
                     and not row.get('truth_conflict', False)]
    counts = Counter(row['status'] for row in supported)
    denominator = len(supported)
    rate = lambda numerator: numerator / denominator if denominator else None
    return {'input_rows': len(rows), 'supported_denominator': denominator,
            'by_transition': {name: counts[name] for name in TRANSITIONS},
            'other_transitions': {key: value for key, value in sorted(counts.items()) if key not in TRANSITIONS},
            'retention_lower': rate(counts['retained']),
            'retention_upper': rate(counts['retained'] + counts['unresolved']),
            'removal_lower': rate(counts['removed']),
            'removal_upper': rate(counts['removed'] + counts['unresolved'])}


def strict_analysis(ledger):
    """Read only: retain exclusion IDs instead of rewriting visual labels."""
    original = [row for row in ledger if row['side'] == 'original']
    attributes = [row for row in ledger if row['type'] == 'attribute']
    supported = [row for row in attributes if row.get('visual_label') == 'supported']
    parent_unconfirmed = [row for row in supported if row.get('parent_visual_label') != 'supported']
    excluded = []
    for row in supported:
        if _attribute_eligible(row):
            continue
        reasons = []
        if row.get('parent_visual_label') != 'supported':
            reasons.append('parent_not_supported')
        if row.get('strict_parent_supported_eligible') is not True:
            reasons.append('strict_parent_supported_eligible_not_true')
        if row.get('truth_conflict', False):
            reasons.append('truth_conflict')
        excluded.append({key: row.get(key) for key in ('pair_id', 'caption_id', 'side', 'fact_id', 'parent_visual_label')})
        excluded[-1]['reasons'] = reasons
    return {'version': 'final_v1_strict_parent_statistics_v1',
            'denominator_scope': 'original_side_accepted_supported_facts; attributes_require_supported_parent_and_strict_flag',
            'attribute_consistency_scope': 'all_accepted_attribute_rows_both_sides',
            'fact_rows': len(ledger), 'original_fact_rows': len(original),
            'original_supported': {kind: _supported_summary([row for row in original if row['type'] == kind], kind)
                                   for kind in ('entity', 'attribute')},
            'attribute_parent_consistency': {
                'total_attribute_rows': len(attributes),
                'original_attribute_rows': sum(row['side'] == 'original' for row in attributes),
                'supported_attribute_rows': len(supported),
                'supported_with_parent_not_supported': len(parent_unconfirmed),
                'parent_label_distribution': dict(sorted(Counter(
                    row.get('parent_visual_label') or 'missing' for row in parent_unconfirmed).items())),
                'excluded_supported_attribute_count': len(excluded),
                'excluded_supported_attribute_records': excluded},
            'changes_visual_labels': False, 'new_model_calls': 0,
            'research_accuracy_validated': False,
            'extraction_omissions_require_reference_ledger': True}
