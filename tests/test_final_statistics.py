import copy
import json
import unittest
from unittest.mock import patch

from analysis_skeleton.final_v1.pipeline import execute
from analysis_skeleton.final_v1.statistics import strict_analysis
from analysis_skeleton.framework_v2.runtime import ResponseCache


def row(fid, kind='attribute', *, side='original', label='supported', parent='supported',
        strict=True, status='retained', conflict=False):
    return {'pair_id': 'pair', 'caption_id': side, 'side': side, 'fact_id': fid,
            'type': kind, 'visual_label': label, 'parent_visual_label': parent,
            'strict_parent_supported_eligible': strict, 'status': status, 'truth_conflict': conflict}


class FinalStrictStatisticsTests(unittest.TestCase):
    def test_original_denominators_and_transition_bounds_do_not_count_steer(self):
        records = [row('e1', 'entity'), row('e2', 'entity', status='removed'),
                   row('e3', 'entity', label='uncertain'),
                   row('a1'), row('a2', status='modified'), row('a3', status='unresolved'),
                   row('a4', label='hallucinated'), row('a5', side='steer', status='added')]
        result = strict_analysis(records)
        e, a = result['original_supported']['entity'], result['original_supported']['attribute']
        self.assertEqual(e['supported_denominator'], 2)
        self.assertEqual(e['by_transition'], {'retained': 1, 'removed': 1, 'modified': 0, 'unresolved': 0})
        self.assertEqual(a['supported_denominator'], 3)
        self.assertEqual(a['by_transition'], {'retained': 1, 'removed': 0, 'modified': 1, 'unresolved': 1})
        self.assertEqual(a['retention_lower'], 1/3)
        self.assertEqual(a['retention_upper'], 2/3)
        self.assertEqual(a['removal_upper'], 1/3)
        self.assertEqual(result['attribute_parent_consistency']['total_attribute_rows'], 5)

    def test_parent_exclusions_are_explicit_and_do_not_modify_labels(self):
        records = [row('good'), row('u', parent='uncertain', strict=False),
                   row('h', parent='hallucinated', strict=False, conflict=True),
                   row('pending', parent='pending', strict=False), row('missing', parent=None, strict=False),
                   row('flag_false', strict=False), row('flag_lies', parent='uncertain', strict=True),
                   row('steer_u', side='steer', parent='uncertain', strict=False)]
        before = copy.deepcopy(records)
        result = strict_analysis(records)
        self.assertEqual(result['original_supported']['attribute']['supported_denominator'], 1)
        consistency = result['attribute_parent_consistency']
        self.assertEqual(consistency['supported_with_parent_not_supported'], 6)
        self.assertEqual(consistency['parent_label_distribution'], {'uncertain': 3, 'hallucinated': 1, 'pending': 1, 'missing': 1})
        self.assertEqual(consistency['excluded_supported_attribute_count'], 7)
        self.assertEqual({r['fact_id'] for r in consistency['excluded_supported_attribute_records']},
                         {'u', 'h', 'pending', 'missing', 'flag_false', 'flag_lies', 'steer_u'})
        self.assertEqual(records, before)

    def test_zero_denominators_are_null_not_zero_accuracy(self):
        for records in ([], [row('unresolved', label='uncertain', parent='uncertain', strict=False)]):
            for summary in strict_analysis(records)['original_supported'].values():
                self.assertEqual(summary['supported_denominator'], 0)
                self.assertEqual(sum(summary['by_transition'].values()), 0)
                self.assertIsNone(summary['retention_lower'])
                self.assertIsNone(summary['retention_upper'])
                self.assertIsNone(summary['removal_lower'])
                self.assertIsNone(summary['removal_upper'])


class FinalCacheBoundaryTests(unittest.TestCase):
    def test_claim_type_cross_run_cache_risk_is_blocked_before_any_loading(self):
        class Stage:
            stage = 'verify'
            identity = {'model': 'deepseek-flash'}
        payload = {'image_sha256': 'same-image', 'statement': 'same-statement',
                   'entity_context': {}, 'claim_type': 'entity'}
        audit = {'identity': Stage.identity, 'input': payload, 'response_model': 'deepseek-flash',
                 'raw_content': json.dumps({'claim_type': 'entity'})}
        legacy = ResponseCache([{'task_key': 'same-task', 'audit': audit}])
        # Document the inherited risk without changing the frozen old runtime.
        self.assertIsNotNone(legacy.get('same-task', Stage(), {**payload, 'claim_type': 'attribute'}))
        with patch('analysis_skeleton.final_v1.pipeline.read_json') as read_json, \
             patch('analysis_skeleton.final_v1.pipeline.read_jsonl') as read_jsonl, \
             patch('analysis_skeleton.final_v1.pipeline.make_stages') as make_stages, \
             patch('analysis_skeleton.final_v1.pipeline.LexicalRecorder') as parser:
            for mode, path in [('reuse', None), ('replay', None), ('fresh', 'old_cache.jsonl')]:
                with self.subTest(mode=mode, path=path):
                    with self.assertRaisesRegex(ValueError, 'fresh_and_same_run_resume_only'):
                        execute('absent_pairs', 'unused_output', profile='absent_profile',
                                cache_mode=mode, cache_path=path, resume=True)
            for mocked in (read_json, read_jsonl, make_stages, parser):
                mocked.assert_not_called()


if __name__ == '__main__':
    unittest.main()
