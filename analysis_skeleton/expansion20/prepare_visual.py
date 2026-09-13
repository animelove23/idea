"""60 caption-derived fixed visual candidates after direct image inspection, before M5 calls."""
from analysis_skeleton.common import read_jsonl,write_jsonl
from analysis_skeleton.contracts import normalize_document
from analysis_skeleton.m4_queue import statement
from .reference_specs import SPECS
from .prepare import ROOT

# side, author entity key, fact type/slot, label, image-only candidate rationale.
CHOICES={
'326667':[
 ('original','bird','existence','supported','A long-legged bird is clearly visible.'),
 ('original','rock','existence','supported','Numerous rocks are visible along the water.'),
 ('original','bird','size','uncertain','No stable size threshold or scale is supplied.')],
'352377':[
 ('steer','apple_green','existence','uncertain','Foreground fruits look pear-shaped; blurred background prevents excluding every apple.'),
 ('original','orange','existence','supported','Orange citrus fruits are visible behind the foreground fruit.'),
 ('steer','banana_yellow','existence','uncertain','The heavily defocused yellow background fruit cannot be identified confidently.')],
'195269':[
 ('original','kite','existence','supported','A kite and its tail are clearly visible in the sky.'),
 ('steer','hoodie','existence','supported','The foreground child wears a striped hooded top.'),
 ('original','car','existence','uncertain','Distant background structures are too small to identify a car reliably.')],
'69584':[
 ('original','airplane','existence','supported','An airplane is visible against the sky.'),
 ('original','cloud','existence','supported','Cloud patches are visible around the airplane.'),
 ('original','airplane','size','uncertain','Apparent image size does not supply a fixed physical size threshold.')],
'317188':[
 ('original','glasses','existence','supported','Eyeglasses are visible on the woman.'),
 ('original','sweater','color','supported','The sweater has a pink/coral hue.'),
 ('steer','cell_phone','color','supported','The flip phone has a purple casing.')],
'373677':[
 ('original','clock','existence','supported','A clock face is visible on the tower.'),
 ('steer','person_left','existence','hallucinated','The full scene shows a tower with decorative figures, not actual people standing beside it.'),
 ('original','roof','color','uncertain','Roof tiles appear brownish while trim is reddish; the boundary of the claimed red roof is ambiguous.')],
'279634':[
 ('original','snowboard','existence','supported','The child holds a snowboard.'),
 ('original','car_left','existence','hallucinated','The visible left area is a stone entrance and contains no car.'),
 ('steer','helmet','existence','supported','The child wears a blue helmet.')],
'45094':[
 ('original','wine','color','supported','Dark red wine is visible in the foreground glass.'),
 ('steer','shirt','color','supported','The foreground man wears a white collared shirt.'),
 ('original','glass2','existence','supported','The second person also holds a stemmed glass.')],
'381925':[
 ('original','dog','existence','supported','A small dog is held on the girl’s lap.'),
 ('steer','remote_control','existence','uncertain','The small blue handheld item is not detailed enough to identify confidently as a remote or leash handle.'),
 ('original','bench','material','supported','The bench consists of weathered wooden planks.')],
'54264':[
 ('original','lion_statue','color','supported','The lion statue is white/pale stone colored.'),
 ('original','car','existence','uncertain','The tightly cropped street edge does not establish whether the claimed car is visible.'),
 ('steer','lion_statue','material','uncertain','The photo cannot reliably discriminate marble from other pale stone or cast materials.')],
'256003':[
 ('steer','train','existence','supported','A miniature train is clearly visible on model tracks.'),
 ('original','person_middle','existence','hallucinated','The middle of the model scene shows buildings, fencing and objects but no person.'),
 ('original','tractor','size','supported','The tractor is a small miniature within the model set.')],
'462687':[
 ('original','pizza','existence','hallucinated','The people hold sandwiches and an apple; no pizza is visible.'),
 ('original','clock','existence','hallucinated','The visible wall and doorway contain no clock.'),
 ('original','apple_left','existence','supported','The left foreground man holds a green apple.')],
'450500':[
 ('original','stool','existence','supported','The man at the left stands on a small white stool.'),
 ('original','shirt','color','supported','The foreground girl wears a bright pink top.'),
 ('original','backpack','existence','uncertain','Overlapping people and dark items obscure any confidently identifiable backpack.')],
'69946':[
 ('original','boat','existence','supported','Several small boats are moored in the water.'),
 ('original','car','existence','uncertain','Distant shore details are insufficient to resolve a car confidently.'),
 ('steer','grassy_area','existence','supported','A grassy bank occupies the foreground left.')],
'265462':[
 ('steer','shirt','color','supported','The skateboarder appearances wear black shirts.'),
 ('steer','jeans','existence','supported','Blue denim jeans are visible.'),
 ('original','stairs','existence','supported','Concrete stairs are clearly visible.')],
'303499':[
 ('original','coat','color','supported','The riders wear bright red coats.'),
 ('steer','horse_black','color','supported','A foreground horse has a black coat.'),
 ('steer','public_area','existence','uncertain','A courtyard is visible, but public access cannot be established from the image.')],
'316617':[
 ('steer','frisbee','existence','supported','Flying discs are visible with the people.'),
 ('steer','shirt_red','color','supported','The person on the right wears a red shirt.'),
 ('original','handbag_left','existence','supported','A blue shoulder bag is visible on the central person’s left side.')],
'519838':[
 ('original','dog','existence','supported','A dog is visible on the left path.'),
 ('original','backpack','existence','hallucinated','No backpack is visible on the ground or the clearly shown park foreground.'),
 ('original','car','existence','supported','Parked vehicles are visible along the distant road at upper right.')],
'565761':[
 ('original','room','size','supported','The room is visibly spacious with high ceilings and a large audience.'),
 ('original','tie','existence','supported','A tie is visible on the seated speaker.'),
 ('steer','bowl','existence','uncertain','The partially cropped foreground tableware cannot be confidently identified as a bowl.')],
'483723':[
 ('original','umbrella','size','hallucinated','The shade comes from a fixed thatched shelter, not a large umbrella.'),
 ('steer','hammock','existence','supported','A red hammock holds one of the men.'),
 ('steer','clothing','color','supported','The visible clothing on both men is blue/dark blue.')],
}


def build():
    target=ROOT/'verify_cases.jsonl'
    if target.exists():raise ValueError('Do not overwrite visual candidates')
    pairs=read_jsonl(ROOT/'pairs.jsonl')
    refs={c['case_id']:c for c in read_jsonl(ROOT/'decompose_cases.jsonl')}
    cases=[]
    for p in pairs:
        for j,(side,key,slot,label,reason) in enumerate(CHOICES[p['pair_id']]):
            c=refs[p[side]['caption_id']];doc=normalize_document(c['reference'],c['text'],c['case_id'])
            index=[e[0] for e in SPECS[p['pair_id']][side][0]].index(key)
            e=doc['entities'][index];f=next(f for f in doc['facts'] if f['entity_id']==e['id'] and f['slot']==slot)
            cases.append({'case_id':p['pair_id']+f'_v{j+1}','image_id':p['pair_id'],'semantic_type':f['type'],
                          'reference_label':label,'reference_reason':reason,
                          'reference_status':'assistant_image_inspected_candidate_pre_m5_prediction',
                          'source_caption_id':c['case_id'],'source_fact_id':f['id'],
                          'input':{'image_path':p['image_path'],'image_sha256':p['image_sha256'],
                                   'statement':statement(f,e),
                                   'entity_context':{'name':e['name'],'source_mentions':[m['quote'] for m in e['mentions']]}}})
    assert len(cases)==60
    write_jsonl(target,cases)


if __name__=='__main__':build()
