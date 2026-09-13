import json,tempfile,unittest
from pathlib import Path
from analysis_skeleton.common import read_jsonl,write_jsonl
from analysis_skeleton.evidence_verifier_v2.experiment import FlashStage,MODEL

class FlashSufficiencyTests(unittest.TestCase):
    def test_only_system_message_changes_and_model_is_explicit(self):
        shots='outputs/evidence_verifier_v1/shots.jsonl'
        query={**read_jsonl('outputs/evidence_verifier_v1/inputs.jsonl')[0]['input'],'claim_type':'entity'}
        a=FlashStage(shots,'control');b=FlashStage(shots,'sufficiency')
        self.assertEqual(a.messages(query)[1:],b.messages(query)[1:])
        self.assertNotEqual(a.messages(query)[0],b.messages(query)[0])
        self.assertEqual(a.config.model,MODEL);self.assertEqual(b.config.model,MODEL)
        self.assertEqual(len(b.messages(query)),14)
    def test_pro_config_cannot_override_actual_flash_request(self):
        captured=[]
        def transport(body):
            captured.append(body)
            return {'id':'offline','model':MODEL,'choices':[{'finish_reason':'stop','message':{'content':'{}'}}]}
        with tempfile.TemporaryDirectory() as d:
            config=Path(d)/'config.json';config.write_text(json.dumps({'api_key':'offline-test','model':'deepseek-v4-pro'}))
            s=FlashStage('outputs/evidence_verifier_v1/shots.jsonl','sufficiency',str(config),transport)
            s.run({**read_jsonl('outputs/evidence_verifier_v1/inputs.jsonl')[0]['input'],'claim_type':'entity'})
        self.assertEqual(captured[0]['model'],MODEL)
        self.assertEqual(captured[0]['thinking'],{'type':'disabled'})
    def test_modified_fewshot_is_rejected(self):
        rows=read_jsonl('outputs/evidence_verifier_v1/shots.jsonl');rows[0]['output']['scope']='changed'
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'shots.jsonl';write_jsonl(p,rows)
            with self.assertRaises(ValueError):FlashStage(p,'sufficiency')

if __name__=='__main__':unittest.main()
