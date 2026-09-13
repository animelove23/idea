import copy,tempfile,unittest
from pathlib import Path
from PIL import Image
from analysis_skeleton.common import sha
from analysis_skeleton.visual_localization_v1.views import boxes,prepare_views,validate_views,MultiViewStage
from analysis_skeleton.m5_verify import VisualStage

class ViewTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.path=self.root/'source.png'
        im=Image.new('RGB',(17,13));im.putdata([(x%256,(x*3)%256,(x*7)%256) for x in range(221)]);im.save(self.path)
        self.payload={'image_path':str(self.path),'image_sha256':sha(self.path),'statement':'An entity is present.','entity_context':{}}
        self.record=prepare_views(self.payload,self.root/'views')
    def test_views_preserve_pixels_and_cover_entire_source(self):
        validate_views(self.payload,self.record)
        covered={(x,y) for l,t,r,b in boxes(17,13) for x in range(l,r) for y in range(t,b)}
        self.assertEqual(len(covered),17*13)
        self.assertEqual(sha(self.path),self.payload['image_sha256'])
    def test_repeated_preparation_is_identical(self):
        self.assertEqual(self.record,prepare_views(self.payload,self.root/'views'))
    def test_pixel_tamper_detected_even_after_hash_updated(self):
        altered=copy.deepcopy(self.record);entry=altered['views'][0]
        with Image.open(entry['image_path']) as im:
            im=im.copy();im.putpixel((0,0),(255,255,255));im.save(entry['image_path'])
        entry['image_sha256']=sha(entry['image_path'])
        with self.assertRaisesRegex(ValueError,'view_pixels_changed'):validate_views(self.payload,altered)
    def test_geometry_and_source_tamper_rejected(self):
        bad=copy.deepcopy(self.record);bad['views'][0]['box'][0]=1
        with self.assertRaisesRegex(ValueError,'geometry'):validate_views(self.payload,bad)
        Image.new('RGB',(17,13)).save(self.path)
        with self.assertRaisesRegex(ValueError,'source_image_changed'):validate_views(self.payload,self.record)
    def test_only_query_views_change_fewshot_and_original_query_preserved(self):
        baseline=VisualStage();candidate=MultiViewStage(view_records={self.payload['image_sha256']:self.record})
        before=baseline.messages(self.payload);after=candidate.messages(self.payload)
        self.assertEqual(before[:-1],after[:-1])
        self.assertEqual(before[-1]['content'],after[-1]['content'][:2])
        self.assertEqual(sum(p['type']=='image_url' for p in after[-1]['content']),5)
        self.assertEqual(baseline.identity['shots_sha'],candidate.identity['shots_sha'])
        self.assertEqual(baseline.identity['prompt_sha'],candidate.identity['prompt_sha'])

if __name__=='__main__':unittest.main()
