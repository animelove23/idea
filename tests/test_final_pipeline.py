import copy
import json
import tempfile
import unittest
from pathlib import Path

from analysis_skeleton.common import read_json, read_jsonl, write_jsonl
from analysis_skeleton.final_v1.pipeline import execute, enrich_queue, make_stages, validate_profile
from analysis_skeleton.final_v1.visual import prepare_shots
from analysis_skeleton.evidence_verifier_v1.stage import make_evidence_shots
from analysis_skeleton.framework_v2.runtime import CheckpointIntegrityError
from analysis_skeleton.m1_lexical import LexicalRecorder
import tests.test_skeleton_pipeline as fixtures


def evidence(kind, *, unresolved=False, proposition=True):
    raw = {'claim_type': kind, 'candidate_status': 'unresolved' if unresolved else 'matches',
           'region_status': 'limited' if unresolved else 'inspectable', 'bbox': [10, 10, 200, 200],
           'observed_category': 'car', 'scope': 'the foreground vehicle',
           'visible_cues': 'The vehicle is indistinct.' if unresolved else 'Four wheels and a red body are visible.',
           'limitation': 'blur' if unresolved else 'none',
           'attribute_status': 'supported' if kind == 'attribute' else 'not_applicable'}
    if proposition:
        raw['proposition_status'] = 'supported'
    return raw


class Stub:
    identity = {'model': 'offline_final_pipeline_fixture'}

    def __init__(self, stage, responses=None, *, invalid_first=False, unresolved=False, proposition=True):
        self.stage = stage
        self.responses = iter(responses or [])
        self.inputs = []
        self.invalid_first = invalid_first
        self.unresolved = unresolved
        self.proposition = proposition

    def run(self, payload):
        self.inputs.append(copy.deepcopy(payload))
        if self.stage == 'verify':
            raw = ({'invalid': True} if self.invalid_first and len(self.inputs) == 1
                   else evidence(payload['claim_type'], unresolved=self.unresolved, proposition=self.proposition))
        else:
            raw = next(self.responses)
        return copy.deepcopy(raw), {'api_calls': 0, 'stage': self.stage, 'identity': self.identity,
                                    'input': copy.deepcopy(payload), 'raw_content': json.dumps(raw)}


class FinalPipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parser = LexicalRecorder()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source, self.out = self.root/'pairs.jsonl', self.root/'run'
        f = fixtures.PipelineTests(); f.setUp(); self.f = f
        self.f.pair['original']['text'] = 'A car rests. A sign hangs nearby. The red car is wet.'
        self.f.original['entities'][0]['mentions'].append({'quote': 'car', 'occurrence': 1})
        inp = read_jsonl('analysis_skeleton/fixtures/verify_cases.jsonl')[0]['input']
        self.f.pair.update(image_path=inp['image_path'], image_sha256=inp['image_sha256'])
        write_jsonl(self.source, [self.f.pair])
        self.shots = self.root/'shots.jsonl'; write_jsonl(self.shots, [])
        self.profile = {'decompose_candidate': 'control', 'visual_candidate': 'proposition',
                        'value_anchors': False, 'state_support': True, 'visual_shots_path': str(self.shots)}

    def stages(self, **verify_options):
        return {'decompose': Stub('decompose', [self.f.original, self.f.steer]),
                'align': Stub('align', [self.f.aligned]), 'verify': Stub('verify', **verify_options)}

    def run_pipeline(self, stages, **kwargs):
        return execute(self.source, self.out, stages=stages, parser=self.parser, profile=self.profile, **kwargs)

    def test_attribute_uses_later_fact_window_and_claim_type(self):
        stages = self.stages(); metrics = self.run_pipeline(stages)
        self.assertEqual((metrics['analyzed_pairs'], metrics['facts'], metrics['claims']), (1, 3, 2))
        self.assertEqual({p['claim_type'] for p in stages['verify'].inputs}, {'entity', 'attribute'})
        attribute = next(p for p in stages['verify'].inputs if p['claim_type'] == 'attribute')
        self.assertIn('The red car is wet.', attribute['entity_context']['source_window'])
        self.assertNotIn('A car rests.', attribute['entity_context']['source_window'])
        self.assertEqual(attribute['final_context_audit']['by_ref'][0]['audit']['source_selection'], 'attribute_fact')
        saved = read_jsonl(self.out/'verification.jsonl')
        self.assertTrue(all('evidence' in r and 'decision_rule' in r and 'audit' in r for r in saved))

    def test_subject_uncertainty_blocks_attribute_support(self):
        for candidate in ['proposition', 'context']:
            with self.subTest(candidate=candidate):
                self.out = self.root / candidate
                self.profile['visual_candidate'] = candidate
                stages = self.stages(unresolved=True, proposition=candidate == 'proposition')
                metrics = self.run_pipeline(stages)
                self.assertEqual(metrics['pending_claims'], 0)
                results = read_jsonl(self.out/'verification.jsonl')
                self.assertTrue(all(r['label'] == 'uncertain' for r in results))
                attribute = next(r for r in results if r['evidence']['claim_type'] == 'attribute')
                self.assertTrue(attribute['attribute_support_blocked_by_referent'])

    def test_resume_never_repeats_stage_calls(self):
        stages = self.stages(); self.run_pipeline(stages)
        before = {name: len(stage.inputs) for name, stage in stages.items()}
        metrics = self.run_pipeline(stages, resume=True)
        self.assertEqual(before, {name: len(stage.inputs) for name, stage in stages.items()})
        self.assertEqual(metrics['resumed_checkpoints'], 5)
        self.assertEqual(metrics['new_api_calls_this_invocation'], 0)

    def test_invalid_claim_does_not_drop_pair_or_next_claim(self):
        metrics = self.run_pipeline(self.stages(invalid_first=True))
        self.assertEqual(metrics['analyzed_pairs'], 1)
        self.assertEqual(metrics['facts'], 3)
        self.assertEqual(metrics['pending_claims'], 1)
        self.assertEqual(metrics['call_status_counts']['technical_failure'], 1)
        rows = read_jsonl(self.out/'verification.jsonl')
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum(r['label'] == 'supported' for r in rows), 1)

    def test_profile_change_invalidates_resume(self):
        stages = self.stages(); self.run_pipeline(stages)
        self.profile['value_anchors'] = True
        with self.assertRaises(CheckpointIntegrityError):
            self.run_pipeline(stages, resume=True)

    def test_no_profile_no_implicit_promotion_or_credentials(self):
        with self.assertRaises(ValueError): validate_profile(None)
        with self.assertRaises(ValueError): validate_profile({**self.profile, 'api_key': 'forbidden'})

    def test_stage_factory_explicit_flash_and_selected_six_shots(self):
        for candidate in ['context', 'proposition']:
            original = read_jsonl('analysis_skeleton/shots/verify.jsonl')
            write_jsonl(self.shots, prepare_shots() if candidate == 'proposition' else make_evidence_shots(original))
            profile = {**self.profile, 'visual_candidate': candidate, 'decompose_candidate': 'owner'}
            stages = make_stages(profile, 'decomposition/api_config.local.json')
            self.assertTrue(all(s.source.config.model == 'deepseek-flash' for s in stages.values()))
            self.assertEqual(len(stages['verify'].source.shots), 6)
            self.assertEqual(len(stages['decompose'].source.shots), 8)


if __name__ == '__main__':
    unittest.main()
