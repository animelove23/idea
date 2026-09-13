import copy,tempfile,unittest
from pathlib import Path
from PIL import Image
from analysis_skeleton.common import sha,write_jsonl,read_jsonl
from analysis_skeleton.evidence_verifier_v1.roi import eligible,create_crop,ROIStage
from analysis_skeleton.evidence_verifier_v1.stage import EvidenceStage,make_evidence_shots

class ROITests(unittest.TestCase):
    def test_selector_depends_only_on_model_uncertainty_box_and_type(self):
        r={'semantic_type':'entity','prediction':{'label':'uncertain','evidence':{'bbox':[200,200,400,400],'limitation':'blur'}}}
        self.assertTrue(eligible(r));self.assertTrue(eligible({**r,'reference_label':'hallucinated'}))
        for change in ({'label':'supported'},{'evidence':{'bbox':[0,0,1000,1000],'limitation':'blur'}},{'evidence':{'bbox':[200,200,400,400],'limitation':'nonvisual_claim'}}):
            self.assertFalse(eligible({**r,'prediction':{**r['prediction'],**change}}))
        self.assertFalse(eligible({**r,'semantic_type':'attribute'}))
    def test_crop_preserves_original_pixels_and_stays_in_image(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);im=Image.new('RGB',(100,80));im.putdata([(i%256,i%151,i%97) for i in range(8000)]);im.save(p/'source.png')
            payload={'image_path':str(p/'source.png'),'image_sha256':sha(p/'source.png')}
            v=create_crop(payload,[0,0,200,250],p/'crop.png')
            self.assertEqual(v['pixel_box'],[0,0,25,25])
            with Image.open(p/'crop.png') as crop:self.assertEqual(crop.tobytes(),im.crop(v['pixel_box']).tobytes())
    def test_only_query_gets_one_extra_image_and_no_old_model_answer(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);shots=make_evidence_shots(read_jsonl('analysis_skeleton/shots/verify.jsonl'));write_jsonl(p/'shots.jsonl',shots)
            query={**shots[0]['input'],'claim_type':'entity'};query['roi_view']=create_crop(query,[100,500,300,800],p/'crop.png')
            original=EvidenceStage(p/'shots.jsonl').messages(query)
            augmented=ROIStage(p/'shots.jsonl','test_manifest').messages(query)
            self.assertEqual(original[:-1],augmented[:-1]);self.assertEqual(original[-1]['content'],augmented[-1]['content'][:2])
            self.assertEqual(sum(x['type']=='image_url' for x in augmented[-1]['content']),2)
            self.assertNotIn('visible_cues',augmented[-1]['content'][-2]['text'])

if __name__=='__main__':unittest.main()
