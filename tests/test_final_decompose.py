import copy
import json
import unittest
from unittest.mock import patch

from decomposition.config import APIConfig
from analysis_skeleton.common import read_jsonl
from analysis_skeleton.framework_v2.contracts import normalize_document
from analysis_skeleton.final_v1.decompose import FinalDecomposeStage, final_shots, normalize_final


def attribute_document(text, value='wet', quote='wet', evidence=None, slot='state'):
    return {'entities': [{'id': 'e1', 'name': 'bench',
                         'mentions': [{'quote': 'bench', 'occurrence': 0}]}],
            'attributes': [{'id': 'a1', 'entity_id': 'e1', 'slot': slot, 'value': value,
                            'evidence': [{'quote': evidence or text, 'occurrence': 0}],
                            'value_quotes': [{'quote': quote, 'occurrence': 0}]}], 'excluded': []}


class FinalDecomposeTests(unittest.TestCase):
    def test_only_d7_changes_and_all_examples_remain_valid(self):
        old = read_jsonl('analysis_skeleton/shots/decompose.jsonl')
        frozen = copy.deepcopy(old)
        new = final_shots(old)
        self.assertEqual(old, frozen)
        self.assertEqual([i for i in range(8) if old[i] != new[i]], [6])
        for shot in new:
            self.assertFalse(normalize_document(shot['output'], shot['input']['text'])['issues'])

    def test_example_separates_people_clothing_and_part_properties(self):
        shot = final_shots(read_jsonl('analysis_skeleton/shots/decompose.jsonl'))[6]
        doc = normalize_final(shot['output'], shot['input']['text'])
        names = {e['id']: e['name'] for e in doc['entities']}
        attrs = [f for f in doc['facts'] if f['type'] == 'attribute']
        self.assertEqual(sum(v == 'person' for v in names.values()), 2)
        self.assertEqual(sum(v == 'coat' for v in names.values()), 2)
        self.assertEqual([(names[f['entity_id']], f['value']) for f in attrs],
                         [('coat', 'red'), ('coat', 'blue'), ('door', 'wood')])
        self.assertFalse(doc['issues'])

    def test_flash_single_call_uses_eight_shots_and_unchanged_query(self):
        sent = []
        def transport(body):
            sent.append(body)
            return {'id': 'fake', 'model': 'deepseek-flash', 'choices': [{
                'finish_reason': 'stop', 'message': {'content': '{"entities":[],"attributes":[],"excluded":[]}'}}]}
        with patch('analysis_skeleton.llm.load_api_config',
                   return_value=APIConfig(model='deepseek-flash', api_key='offline', retries=0)) as config:
            stage = FinalDecomposeStage(transport=transport)
            _, audit = stage.run({'text': 'A cup.'})
        self.assertEqual(config.call_args.kwargs['model'], 'deepseek-flash')
        self.assertEqual(len(sent), 1)
        self.assertEqual(sent[0]['model'], 'deepseek-flash')
        self.assertEqual(len(sent[0]['messages']), 18)
        self.assertEqual(json.loads(sent[0]['messages'][-1]['content']), {'text': 'A cup.'})
        self.assertEqual(audit['api_calls'], 1)

    def test_cloudy_to_wet_is_quarantined_with_original_raw(self):
        text = 'A bench under a cloudy sky.'
        raw = attribute_document(text, quote='cloudy')
        frozen = copy.deepcopy(raw)
        doc = normalize_final(raw, text)
        self.assertEqual(raw, frozen)
        self.assertEqual([f['type'] for f in doc['facts']], ['entity'])
        self.assertEqual(doc['state_support_audit']['quarantined'][0]['raw'], raw['attributes'][0])
        self.assertEqual(doc['status'], 'needs_review')

    def test_explicit_state_forms_are_supported(self):
        for value, form in [('wet', 'wet'), ('wet', 'wetter'), ('closed', 'closed'),
                            ('open', 'opened'), ('dry', 'dried'), ('broken', 'broken'), ('intact', 'intact')]:
            with self.subTest(value=value, form=form):
                text = f'A {form} bench.'
                doc = normalize_final(attribute_document(text, value=value, quote=form), text)
                self.assertFalse(doc['issues'])
                self.assertEqual(len(doc['facts']), 2)

    def test_close_does_not_support_closed(self):
        text = 'A bench close to the door.'
        doc = normalize_final(attribute_document(text, value='closed', quote='close'), text)
        self.assertEqual(len(doc['state_support_audit']['quarantined']), 1)

    def test_unique_repeated_value_anchor_is_repaired(self):
        text = 'A wet chair and a wet bench.'
        raw = attribute_document(text, evidence='wet bench')
        doc = normalize_final(raw, text)
        self.assertFalse(doc['issues'])
        self.assertEqual(doc['value_anchor_audit']['repairs'][0]['after']['occurrence'], 1)
        self.assertEqual(raw['attributes'][0]['value_quotes'][0]['occurrence'], 0)

    def test_ambiguous_value_anchor_is_not_repaired(self):
        text = 'A wet chair. A wet bench is wet.'
        doc = normalize_final(attribute_document(text, evidence='A wet bench is wet'), text)
        self.assertEqual(doc['value_anchor_audit']['repairs'], [])
        self.assertEqual(doc['value_anchor_audit']['ambiguous_not_repaired'][0]['candidate_count'], 2)
        self.assertTrue(doc['issues'])
        self.assertEqual(len(doc['facts']), 1)

    def test_postprocessors_can_be_replayed_independently(self):
        text = 'A bench under a cloudy sky.'
        raw = attribute_document(text, quote='cloudy')
        unguarded = normalize_final(raw, text, value_anchors=False, state_support=False)
        guarded = normalize_final(raw, text, value_anchors=False, state_support=True)
        self.assertEqual(len(unguarded['facts']), 2)
        self.assertEqual(len(guarded['facts']), 1)
        self.assertFalse(unguarded['state_support_audit']['enabled'])
        self.assertFalse(guarded['value_anchor_audit']['enabled'])

    def test_other_slots_are_not_semantically_expanded_or_filtered(self):
        text = 'A wooden bench.'
        doc = normalize_final(attribute_document(text, value='wood', quote='wooden', slot='material'), text)
        self.assertEqual(len(doc['facts']), 2)
        self.assertEqual(doc['state_support_audit']['quarantined'], [])


if __name__ == '__main__':
    unittest.main()
