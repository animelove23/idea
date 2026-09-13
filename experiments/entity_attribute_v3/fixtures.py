"""Candidate references authored before predictions; distinct shots and probes."""
import copy
from pathlib import Path
from analysis_skeleton.common import write_jsonl
from analysis_skeleton.final_v1.decompose import normalize_final,final_shots
from analysis_skeleton.common import read_jsonl
from experiments.coco400_revision_v2.fixtures import cases as align_cases
from .m3 import project_v2,validate

ROOT=Path(__file__).parent
def q(value):
    text,occ=value if isinstance(value,tuple) else (value,0)
    return {'quote':text,'occurrence':occ}

def case(cid,text,entities,attributes=(),excluded=(),category='ownership'):
    raw={'entities':[{'id':f'e{i+1}','name':name,'mentions':[q(v) for v in mentions]} for i,(name,mentions) in enumerate(entities)],
         'attributes':[{'id':f'a{i+1}','entity_id':f'e{owner}','slot':slot,'value':value,'evidence':[q(evidence)],'value_quotes':[q(value_quote)]} for i,(owner,slot,value,evidence,value_quote) in enumerate(attributes)],
         'excluded':[{'source':q(text),'reason':'scope_unclear' if reason=='out_of_scope' else reason} for text,reason in excluded]}
    return {'case_id':cid,'category':category,'text':text,'reference':raw,'reference_status':'assistant_authored_development_candidate_not_human_gold'}

def shots():
    examples=[
        case('s1','A woman carries a yellow bag.', [('woman',['woman']),('bag',['bag'])],[(2,'color','yellow','yellow bag','yellow')],[('carries a yellow bag','action')]),
        case('s2','A house has a metal gate.', [('house',['house']),('gate',['gate'])],[(2,'material','metal','metal gate','metal')],[('has a metal gate','relation')]),
        case('s3','A cup of brown coffee.', [('cup',['cup']),('coffee',['coffee'])],[(2,'color','brown','brown coffee','brown')],[('of brown coffee','relation')]),
        case('s4','A small round wooden table.', [('table',['table'])],[(1,'size','small','small round wooden table','small'),(1,'shape','round','round wooden table','round'),(1,'material','wood','wooden table','wooden')]),
        case('s5','An open window is above a wet bench.', [('window',['window']),('bench',['bench'])],[(1,'state','open','open window','open'),(2,'state','wet','wet bench','wet')],[('above a wet bench','relation')]),
        case('s6','A cloudy sky is above a bench.', [('sky',['sky']),('bench',['bench'])],[],[('cloudy','out_of_scope'),('above a bench','relation')]),
    ]
    # Keep the existing explicit one/the-other example and repeated/negated property boundary.
    old=final_shots(read_jsonl('analysis_skeleton/shots/decompose.jsonl'))
    out=[{'example_id':c['case_id'],'input':{'text':c['text']},'output':c['reference'],'reference_status':c['reference_status']} for c in examples]
    out+=copy.deepcopy(old[6:])
    return out

def probes():
    return [
        case('p01','A person wears a red coat.', [('person',['person']),('coat',['coat'])],[(2,'color','red','red coat','red')],[('wears a red coat','action')]),
        case('p02','A building has a wooden door.', [('building',['building']),('door',['door'])],[(2,'material','wood','wooden door','wooden')],[('has a wooden door','relation')],category='part_owner'),
        case('p03','A glass of red wine.', [('glass',['glass']),('wine',['wine'])],[(2,'color','red','red wine','red')],[('of red wine','relation')],category='container_content'),
        case('p04','A cloudy sky.', [('sky',['sky'])],[],[('cloudy','out_of_scope')],category='no_state_inference'),
        case('p05','The door is shut.', [('door',['door'])],[],[('shut','out_of_scope')],category='state_synonym_frozen'),
        case('p06','The door is closed.', [('door',['door'])],[(1,'state','closed','door is closed','closed')],category='state_explicit'),
        case('p07','A door is close to a chair.', [('door',['door']),('chair',['chair'])],[],[('close to a chair','relation')],category='state_near_miss'),
        case('p08','A wooden bench. The bench is made of wood.', [('bench',['bench',('bench',1)])],[(1,'material','wood','wooden bench','wooden')],category='deduplication'),
        case('p09','A tall rectangular metal cabinet.', [('cabinet',['cabinet'])],[(1,'size','tall','tall rectangular metal cabinet','tall'),(1,'shape','rectangular','rectangular metal cabinet','rectangular'),(1,'material','metal','metal cabinet','metal')],category='atomicity'),
        case('p10','A dog runs beside a broken bicycle.', [('dog',['dog']),('bicycle',['bicycle'])],[(2,'state','broken','broken bicycle','broken')],[('runs','action'),('beside a broken bicycle','relation')],category='relation_objects'),
        case('p11','A bird sits on a dry branch.', [('bird',['bird']),('branch',['branch'])],[(2,'state','dry','dry branch','dry')],[('sits','action'),('on a dry branch','relation')],category='state_explicit'),
        case('p12','Two people stand nearby. One wears a green jacket and the other wears a black jacket.', [('person',['One']),('person',['the other']),('jacket',['green jacket']),('jacket',['black jacket'])],[(3,'color','green','green jacket','green'),(4,'color','black','black jacket','black')],[('Two','count'),('stand','action'),('wears a green jacket','action'),('wears a black jacket','action')],category='multiple_owners'),
        case('p13','Three horses stand nearby.', [('horse',['horses'])],[],[('Three','count'),('stand','action')],category='group_not_instances'),
        case('p14','A car might be red. The car is not blue.', [('car',['car',('car',1)])],[],[('might be red','nonasserted'),('is not blue','nonasserted')],category='nonasserted'),
        case('p15','An intact vase is beside a closed box.', [('vase',['vase']),('box',['box'])],[(1,'state','intact','intact vase','intact'),(2,'state','closed','closed box','closed')],[('beside a closed box','relation')],category='state_explicit'),
        case('p16','A child holds a striped umbrella.', [('child',['child']),('umbrella',['umbrella'])],[],[('holds a striped umbrella','action'),('striped','out_of_scope')],category='out_of_scope_pattern'),
    ]

def build():
    ss=shots();pp=probes()
    assert len(ss)==8 and not {s['input']['text'] for s in ss}&{p['text'] for p in pp}
    for r in ss:assert not normalize_final(r['output'],r['input']['text'])['issues'],r['example_id']
    for r in pp:assert not normalize_final(r['reference'],r['text'])['issues'],r['case_id']
    write_jsonl(ROOT/'m2_shots.jsonl',ss);write_jsonl(ROOT/'m2_probes.jsonl',pp)
    for name,source in [('m3_shots.jsonl',align_cases()),('m3_probes.jsonl',align_cases(True))]:
        rows=[]
        for r in source:
            raw,_=project_v2(r['output'],**r['input']);validate(raw,**r['input'])
            rows.append({**r,'output':raw})
        write_jsonl(ROOT/name,rows)
    print({'m2_shots':8,'m2_probes':16,'m3_shots':8,'m3_probes':8,'llm_calls':0})

if __name__=='__main__':build()
