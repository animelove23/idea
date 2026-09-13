import copy
import json
import tempfile
import unittest
from pathlib import Path

from analysis_skeleton.common import check_frozen, new_run, read_jsonl, write_json, write_jsonl
from analysis_skeleton.evidence_verifier_v1.stage import make_evidence_shots
from analysis_skeleton.final_v1.pipeline import make_stages, validate_profile
from analysis_skeleton.final_v1.routing import TypedVisualStage, routing_inputs, validate_typed
from analysis_skeleton.final_v1.visual import prepare_shots
from analysis_skeleton.llm import CallFailure


class FinalTypedVisualTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.context = self.root / 'context.jsonl'
        self.proposition = self.root / 'proposition.jsonl'
        self.manifest = self.root / 'routes.json'
        self.context_rows = make_evidence_shots(read_jsonl('analysis_skeleton/shots/verify.jsonl'))
        self.proposition_rows = prepare_shots()
        write_jsonl(self.context, self.context_rows)
        write_jsonl(self.proposition, self.proposition_rows)
        write_json(self.manifest, {'entity': str(self.context), 'attribute': str(self.proposition)})

    def test_actual_schema_and_audit_follow_type_with_one_call_each(self):
        bodies = []
        def transport(body):
            bodies.append(body)
            query = json.loads(body['messages'][-1]['content'][0]['text'])
            raw = self.context_rows[0]['output'] if query['claim_type'] == 'entity' else self.proposition_rows[3]['output']
            return {'id': 'fake-' + str(len(bodies)), 'model': 'deepseek-flash',
                    'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(raw)}}]}
        stage = TypedVisualStage(self.manifest, transport=transport)
        for kind, shot, contract in [('entity', self.context_rows[0], 'context'),
                                     ('attribute', self.proposition_rows[3], 'proposition')]:
            before = len(bodies)
            raw, audit = stage.run({**shot['input'], 'claim_type': kind})
            self.assertEqual(len(bodies) - before, 1)
            self.assertEqual(audit['api_calls'], 1)
            self.assertEqual(audit['typed_route'], {'claim_type': kind, 'contract': contract})
            self.assertEqual(audit['identity'], stage.stages[kind].identity)
            self.assertEqual(audit['router_identity'], stage.identity)
            self.assertEqual('proposition_status' in raw, kind == 'attribute')
            self.assertEqual(validate_typed(raw, kind)['label'], 'supported')
            self.assertEqual(bodies[-1]['model'], 'deepseek-flash')
            assistants = [m for m in bodies[-1]['messages'] if m['role'] == 'assistant']
            self.assertEqual(len(assistants), 6)
            self.assertTrue(all(('proposition_status' in m['content']) == (kind == 'attribute') for m in assistants))
        self.assertEqual(stage.identity['calls_per_claim'], 1)

    def test_unknown_type_is_rejected_without_transport(self):
        calls = []
        stage = TypedVisualStage(self.manifest, transport=lambda body: calls.append(body))
        for kind in ('object', 'relation', None, []):
            with self.subTest(kind=kind):
                with self.assertRaises(CallFailure) as error:
                    stage.run({'claim_type': kind})
                self.assertEqual(error.exception.audit['api_calls'], 0)
                self.assertEqual(error.exception.audit['phase'], 'input')
                with self.assertRaises(ValueError):
                    validate_typed({}, kind)
        self.assertEqual(calls, [])

    def test_manifest_nested_shots_and_images_are_frozen(self):
        files = routing_inputs(self.manifest)
        self.assertIn(self.context, files)
        self.assertIn(self.proposition, files)
        self.assertTrue(all(Path(row['input']['image_path']) in files for row in self.context_rows + self.proposition_rows))
        out = new_run(self.root / 'frozen', 'routing_test', files)
        check_frozen(out)
        for path in (self.manifest, self.context, self.proposition):
            before = path.read_bytes()
            try:
                path.write_bytes(before + b'\n')
                with self.assertRaisesRegex(ValueError, 'Frozen inputs changed'):
                    check_frozen(out)
            finally:
                path.write_bytes(before)
        check_frozen(out)

    def test_profile_factory_does_not_double_wrap_router(self):
        profile = {'decompose_candidate': 'control', 'visual_candidate': 'typed',
                   'value_anchors': False, 'state_support': True, 'visual_shots_path': str(self.manifest)}
        stages = make_stages(validate_profile(profile), 'decomposition/api_config.local.json')
        self.assertIsInstance(stages['verify'], TypedVisualStage)
        self.assertEqual(stages['verify'].identity['routes'], {'entity': 'context', 'attribute': 'proposition'})
        broken = copy.deepcopy(profile)
        broken['visual_shots_path'] = str(self.context)
        with self.assertRaises(ValueError):
            validate_profile(broken)


if __name__ == '__main__':
    unittest.main()
