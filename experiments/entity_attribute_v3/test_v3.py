import copy,json,socket,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from analysis_skeleton.common import read_jsonl,write_json,sha
from analysis_skeleton.final_v1.decompose import normalize_final
from .fixtures import probes,shots
from .m2 import NounCenteredStage
from .m3 import validate,project_v2
from .retention import rates,analyze
from .scoring import diagnostics
from experiments.coco400_revision_v2.fixtures import cases
from experiments.coco400_v1.test_observe import fixture

class ContractTests(unittest.TestCase):
    def test_shots_and_probes_valid_disjoint(self):
        self.assertEqual(len(shots()),8)
        self.assertFalse({s['input']['text'] for s in shots()}&{p['text'] for p in probes()})
        for p in probes():self.assertFalse(normalize_final(p['reference'],p['text'])['issues'])

    def test_all_m3_examples(self):
        for c in cases()+cases(True):
            raw,_=project_v2(c['output'],**c['input']);out=validate(raw,**c['input'])
            self.assertFalse(out['issues'],c['example_id'])
            self.assertEqual(out['derivation_audit']['model_entity_fact_decisions'],0)

    def test_generalization_not_equivalent(self):
        c=cases()[1];raw,_=project_v2(c['output'],**c['input']);out=validate(raw,**c['input'])
        self.assertEqual(out['alignments'][0]['status'],'modified')
        self.assertEqual(out['description_transitions'][0]['change'],'generalized')

    def test_missing_entity_never_means_removed(self):
        c=cases()[0];out=validate({'entities':[],'attributes':[]},**c['input'])
        self.assertTrue(all(e['status']=='unresolved' and e['reason'].startswith('technical') for e in out['alignments']))

    def test_duplicate_entity_poisoned_not_selected(self):
        c=cases()[0];raw,_=project_v2(c['output'],**c['input']);raw['entities']*=2
        out=validate(raw,**c['input']);self.assertTrue(out['issues'])
        self.assertFalse(any(e['status']=='matched' for e in out['entities']))

    def test_malformed_row_is_local(self):
        c=cases()[4];raw,_=project_v2(c['output'],**c['input']);raw['attributes']=[42]
        out=validate(raw,**c['input']);self.assertTrue(out['issues'])
        self.assertEqual(next(e for e in out['alignments'] if 'entity_e1' in e['original'])['status'],'retained')
        self.assertTrue(next(e for e in out['alignments'] if 'a1' in e['original'])['reason'].startswith('technical'))

    def test_entity_id_cannot_be_smuggled_in_attributes(self):
        c=cases()[0];raw,_=project_v2(c['output'],**c['input'])
        raw['attributes']=[{'original':['entity_e1'],'steer':[],'status':'removed'}]
        out=validate(raw,**c['input']);self.assertTrue(out['issues']);self.assertEqual(out['alignments'][0]['status'],'retained')

    def test_unresolved_parent_does_not_allow_attribute_removal(self):
        c=cases()[4];raw,_=project_v2(c['output'],**c['input'])
        raw['entities'][0].update(status='unresolved',description_change='unresolved')
        out=validate(raw,**c['input']);attr=next(e for e in out['alignments'] if 'a1' in e['original'])
        self.assertEqual(attr['status'],'unresolved');self.assertTrue(attr['reason'].startswith('technical'))

    def test_partial_bad_description_keeps_unrelated_refs(self):
        c=cases()[0];raw,_=project_v2(c['output'],**c['input']);raw['entities'][0]['description_change']='nonsense'
        out=validate(raw,**c['input']);self.assertTrue(out['issues']);self.assertEqual(out['alignments'][0]['status'],'unresolved')

    def test_unknown_id_quarantined(self):
        c=cases()[0];raw,_=project_v2(c['output'],**c['input']);raw['entities'][0]['steer']=['ghost']
        out=validate(raw,**c['input']);self.assertFalse(any(e['status']=='matched' for e in out['entities']))

    def test_lexical_support_is_not_owner_entailment(self):
        p=probes()[0];wrong=copy.deepcopy(p['reference']);wrong['attributes'][0]['entity_id']='e1'
        doc=normalize_final(wrong,p['text']);self.assertFalse(doc['issues'])
        class Scorer:
            name=staticmethod(lambda x:x)
            def score(self,a,b):
                from analysis_skeleton.metrics import score_documents
                return score_documents(a,b)
        d=diagnostics(doc,normalize_final(p['reference'],p['text']),Scorer())
        self.assertEqual(d['ownership_wrong'],1);self.assertIsNone(d['textual_entailment_accuracy'])

    def test_state_near_misses_and_no_new_synonyms(self):
        for text,word in [('The door is shut.','shut'),('The door is close to a chair.','close')]:
            p=probes()[5];raw=copy.deepcopy(p['reference']);raw['attributes'][0]['evidence']=[{'quote':text[:-1],'occurrence':0}];raw['attributes'][0]['value_quotes']=[{'quote':word,'occurrence':0}]
            doc=normalize_final(raw,text);self.assertEqual(sum(f['type']=='attribute' for f in doc['facts']),0)

    def test_uncertainty_not_one_minus_car(self):
        m=rates([{'outcome':x} for x in ['retained','removed','modified','unresolved']])
        self.assertEqual(m['retention_lower'],.25);self.assertEqual(m['retention_upper'],.5)
        self.assertEqual(m['loss_lower'],.5);self.assertNotEqual(1-m['retention_lower'],m['loss_lower'])

    def test_empty_denominator_none(self):self.assertIsNone(rates([])['retention_lower'])

    def test_same_llm_call_shape(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'dummy.json';write_json(path,{'model':'deepseek-flash','api_key':'offline-placeholder'})
            stage=NounCenteredStage(path,transport=lambda body:None)
            self.assertEqual(len(stage.messages({'text':'A car.'})),18)
            self.assertEqual(stage.config.retries,0)

class IntegrationTests(unittest.TestCase):
    def test_all_variants_offline_resume_and_profile_route(self):
        from tests import test_final_pipeline as helper
        from .end_to_end import run_full
        helper.FinalPipelineTests.setUpClass()
        for variant in ('baseline','m2_only','m3_only','combined','m3_failure'):
            with self.subTest(variant=variant):
                fail_alignment=variant=='m3_failure'
                if fail_alignment:variant='m3_only'
                f=helper.FinalPipelineTests();f.setUp();self.addCleanup(f.doCleanups)
                aligned=copy.deepcopy(f.f.aligned)
                for e in aligned['entities']:e['description_change']='equivalent' if e['status']=='matched' else 'absent'
                if variant in ('m3_only','combined'):
                    original=normalize_final(f.f.original,f.f.pair['original']['text'])
                    steer=normalize_final(f.f.steer,f.f.pair['steer']['text'])
                    aligned,_=project_v2(aligned,original,steer)
                if fail_alignment:aligned={'malformed_model_output':True}
                routes=f.root/'custom_routes.json';write_json(routes,{'entity':str(f.shots),'attribute':str(f.shots)})
                profile={**f.profile,'visual_candidate':'typed','visual_shots_path':str(routes)}
                class Typed(helper.Stub):
                    def run(self,payload):
                        self.proposition=payload['claim_type']=='attribute';return super().run(payload)
                stages={'decompose':helper.Stub('decompose',[f.f.original,f.f.steer]),'align':helper.Stub('align',[aligned]),'verify':Typed('verify',unresolved=True)}
                review=Typed('verify');out=f.root/'v3'
                with patch.object(socket.socket,'connect',side_effect=AssertionError('network_forbidden')):
                    r=run_full(f.source,out,profile=profile,stages=stages,review_stage=review,parser=f.parser,workers=1,variant=variant)
                    self.assertEqual(r['analyzed_pairs'],1);self.assertEqual(r['facts'],3)
                    before=sha(out/'retention.json')
                    r2=run_full(f.source,out,profile=profile,stages=stages,review_stage=review,parser=f.parser,workers=1,variant=variant,resume=True)
                    self.assertEqual(r2['review_new_calls'],0);self.assertEqual(sha(out/'retention.json'),before)
                # Config-selected route, not the old hardcoded default, is frozen for review.
                manifest=json.loads((out/'review/manifest.json').read_text(encoding='utf-8'))
                self.assertIn(str(routes.resolve()),manifest['inputs'])
                if fail_alignment:
                    bundle=read_jsonl(out/'first_pass/bundles.jsonl')[0]
                    self.assertTrue(all(e['reason'].startswith('technical') for e in bundle['alignment']['alignments']))
                    continue
                records=read_jsonl(out/'pairs.jsonl');summary,attrs,_,_=analyze(records)
                self.assertEqual(summary['conditional_attribute_retention']['denominator'],1)
                self.assertEqual(attrs[0]['outcome'],'removed')
                records[0]['bundle']['steer']['issues']=[{'kind':'attribute_invalid','raw':{'entity_id':attrs[0]['entity_id'],'slot':attrs[0]['slot']},'reason':'missing source'}]
                scoped=analyze(records)[0]['conditional_attribute_retention']
                self.assertEqual(scoped['unresolved'],1);self.assertEqual(scoped['removed'],0)

if __name__=='__main__':unittest.main()
