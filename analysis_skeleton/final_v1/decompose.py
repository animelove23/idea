"""One-call Flash candidate with separately replayable local evidence checks."""
import copy
import re
from pathlib import Path

from analysis_skeleton.common import digest, sha
from analysis_skeleton.decompose_iteration_v1.value_anchor import normalize_with_value_anchors
from analysis_skeleton.framework_v2.contracts import normalize_document
from analysis_skeleton.llm import FewShotStage


ROOT = Path(__file__).parent
MODEL = 'deepseek-flash'
# A conservative lexical check, not a model of world knowledge or entailment.
# In particular, cloudy must never be promoted to wet and close to closed.
STATE_FORMS = {
    'open': {'open', 'opened'},
    'closed': {'closed'},
    'wet': {'wet', 'wetter', 'wettest'},
    'dry': {'dry', 'dried', 'drier', 'driest'},
    'broken': {'broken'},
    'intact': {'intact'},
}


def final_shots(original):
    """Replace d7 only; teach referents and explicit property ownership together."""
    result = copy.deepcopy(original)
    if len(result) != 8 or result[6]['example_id'] != 'd7':
        raise ValueError('frozen_eight_shot_d7_required')

    def q(quote, occurrence=0):
        return {'quote': quote, 'occurrence': occurrence}

    text = ('Two people stand beside a beautiful car. One person wears a red coat '
            'and the other wears a blue coat. The car has a wooden door.')
    result[6]['input'] = {'text': text}
    result[6]['output'] = {
        'entities': [
            {'id': 'e1', 'name': 'person', 'mentions': [q('One person')]},
            {'id': 'e2', 'name': 'person', 'mentions': [q('the other')]},
            {'id': 'e3', 'name': 'car', 'mentions': [q('car'), q('car', 1)]},
            {'id': 'e4', 'name': 'coat', 'mentions': [q('red coat')]},
            {'id': 'e5', 'name': 'coat', 'mentions': [q('blue coat')]},
            {'id': 'e6', 'name': 'door', 'mentions': [q('wooden door')]},
        ],
        'attributes': [
            {'id': 'a1', 'entity_id': 'e4', 'slot': 'color', 'value': 'red',
             'evidence': [q('red coat')], 'value_quotes': [q('red')]},
            {'id': 'a2', 'entity_id': 'e5', 'slot': 'color', 'value': 'blue',
             'evidence': [q('blue coat')], 'value_quotes': [q('blue')]},
            {'id': 'a3', 'entity_id': 'e6', 'slot': 'material', 'value': 'wood',
             'evidence': [q('wooden door')], 'value_quotes': [q('wooden')]},
        ],
        'excluded': [
            {'source': q('Two'), 'reason': 'count'},
            {'source': q('stand'), 'reason': 'action'},
            {'source': q('beside a beautiful car'), 'reason': 'relation'},
            {'source': q('beautiful'), 'reason': 'subjective'},
            {'source': q('wears a red coat'), 'reason': 'action'},
            {'source': q('wears a blue coat'), 'reason': 'action'},
            {'source': q('has a wooden door'), 'reason': 'relation'},
        ],
    }
    if normalize_document(result[6]['output'], text)['issues']:
        raise ValueError('final_d7_must_pass_original_contract')
    return result


class FinalDecomposeStage(FewShotStage):
    def __init__(self, config_path='decomposition/api_config.local.json', transport=None):
        super().__init__('decompose', config_path, transport=transport, model=MODEL)
        self.rules = self.rules.rstrip() + '\n\n' + (ROOT / 'decompose_rules.txt').read_text(encoding='utf-8')
        self.shots = final_shots(self.shots)
        self.identity.update(
            prompt_sha=digest(self.rules), shots_sha=digest(self.shots),
            condition='final_v1_coverage_ownership', final_code_sha=sha(__file__),
            added_rules_sha=sha(ROOT / 'decompose_rules.txt'),
        )


def normalize_final(raw, text, caption_id='caption', *, value_anchors=True, state_support=True):
    """Keep model output immutable; replay either postprocessor independently.

    This checks lexical support only for the six frozen state values. It cannot
    prove attribute ownership, negation scope or a visual fact's truth. Rejected
    facts remain visible in issues and state_support_audit for denominator use.
    """
    doc = (normalize_with_value_anchors(raw, text, caption_id) if value_anchors
           else normalize_document(raw, text, caption_id))
    if not value_anchors:
        doc['value_anchor_audit'] = {'enabled': False, 'repairs': [],
                                     'ambiguous_not_repaired': [], 'new_model_calls': 0}
    else:
        doc['value_anchor_audit']['enabled'] = True
    quarantined = []
    kept = []
    for fact in doc['facts']:
        if state_support and fact['type'] == 'attribute' and fact['slot'] == 'state':
            allowed = STATE_FORMS[fact['value']]
            unsupported = [span for span in fact['value_spans']
                           if not allowed.intersection(re.findall(r"[a-z]+", span['quote'].casefold()))]
            if unsupported:
                original = next((row for row in raw.get('attributes', [])
                                 if isinstance(row, dict) and row.get('id') == fact['id']), None)
                record = {'attribute_id': fact['id'], 'reason': 'state_without_explicit_lexical_support',
                          'raw': copy.deepcopy(original), 'normalized_fact': copy.deepcopy(fact),
                          'unsupported_value_spans': copy.deepcopy(unsupported)}
                quarantined.append(record)
                doc['issues'].append({'kind': 'attribute_state_unsupported', **copy.deepcopy(record)})
                continue
        kept.append(fact)
    doc['facts'] = kept
    doc['state_support_audit'] = {'enabled': state_support, 'quarantined': quarantined,
                                  'new_model_calls': 0, 'rule': 'state_forms_v1_only',
                                  'does_not_validate_semantic_owner_or_truth': True}
    doc['status'] = 'needs_review' if doc['issues'] else 'ready'
    return doc
