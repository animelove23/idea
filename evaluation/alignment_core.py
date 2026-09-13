"""v1.3 public fact statuses; reuse the validated legacy grouping implementation."""
import copy
import json
from pathlib import Path

from .alignment import PairAligner as LegacyAligner, align_facts, fallback_alignments as legacy_fallback
from .alignment_policy import semantic_review
from .common import ContractError, StageFailure, document_context, require

STATUSES = {'retained', 'removed', 'added', 'modified', 'other'}
POSITION = {'above', 'below', 'near', 'next_to', 'beside', 'in_front_of', 'behind', 'on', 'under', 'relative_position', 'location'}


def review_core(status, facts, participants, slots):
    if status == 'modified' and len(facts) == 2 and {f['type'] for f in facts} == {'relation'}:
        # A new relation target is a changed value, provided the subject and relation
        # dimension are still known. Unknown identity is never rescued here.
        known = all(p and all(g is not None for g in p) for p in participants)
        same_subject = known and participants[0][0] == participants[1][0]
        categories = {f.get('category') for f in facts}
        if 'action' in categories and categories & {'spatial', 'location'}:
            return ('granularity', 'different_relation_dimensions'), []
        same_dimension = len(set(slots)) == 1 or all(s in POSITION for s in slots)
        if same_subject and same_dimension:
            return None, [{'rule': 'same_subject_relation_change', 'note': 'Model asserts a change in the same relation/event dimension; targets may change. Not an independent semantic judgment.'}]
    return semantic_review(status, facts, participants, slots)


def public_result(result):
    """Convert legacy internal uncertainty only at this explicit protocol boundary."""
    result = copy.deepcopy(result)
    for field in ('fact_alignment', 'related_correspondences'):
        for row in result.get(field, []):
            if row['status'] == 'ambiguous':
                row['status'] = 'other'
            if 'other' in row.get('types', []):
                row.update(status='other', reason='other_scope')
            row['in_main'] = row['status'] != 'other' and 'other' not in row.get('types', [])
            if not row['in_main']:
                row['exclusion_reason'] = row['reason']
    for review in result.get('semantic_reviews', []):
        if review.get('result') == 'ambiguous': review['result'] = 'other'
    result['alignment_protocol'] = 'core-change-v1.3'
    return result


def align_core(payload, original, steer, sidecar):
    internal = copy.deepcopy(payload)
    require(isinstance(internal.get('fact_alignment'), list), 'fact alignment array required')
    for row in internal['fact_alignment']:
        require(isinstance(row, dict) and row.get('status') in STATUSES, 'v1.3 fact status required; ambiguous is entity-only')
        if row['status'] == 'other': row['status'] = 'ambiguous'
    return public_result(align_facts(internal, original, steer, sidecar, review_policy=review_core))


def fallback_alignments(original, steer, reason='stage_failed'):
    return public_result({'fact_alignment': legacy_fallback(original, steer, reason)})['fact_alignment']


class PairAligner(LegacyAligner):
    def __init__(self, stage):
        super().__init__(stage)
        # Preserve zero-shot operation; load the matching v1.3 demonstrations only
        # when the caller requested alignment demonstrations.
        if getattr(stage, 'examples', {}).get('alignment') and 'alignment_core' not in stage.examples:
            path = Path(__file__).parent / 'examples/alignment_core.jsonl'
            stage.examples['alignment_core'] = [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines()]

    def facts(self, pair_id, original, steer, sidecar):
        payload = {'original': document_context(original), 'steer': document_context(steer),
                   'entity_sidecar': {k: v for k, v in sidecar.items() if k not in {'audit', 'status'}}}
        raw, audit = self.stage.run('alignment_core', payload)
        try:
            return dict(pair_id=pair_id, **align_core(raw, original, steer, sidecar), audit=audit,
                        entity_alignment=sidecar['entity_alignment'])
        except (ContractError, TypeError, KeyError) as exc:
            raise StageFailure(str(exc), audit) from exc
