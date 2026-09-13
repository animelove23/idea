"""Explicit narrow alignment examples and controlled tests; assistant candidates only."""
from .build_fixtures import E,A,D,q,ROOT
from .contracts import normalize_document,model_document
from .m3_align import validate_alignment
from .common import write_jsonl


def single(text,name,slot=None,value=None,word=None):
    attrs=[] if slot is None else [A('a1','e1',slot,value,text,word or value)]
    return normalize_document(D([E('e1',name,name)],attrs),text)


def row(o,s,status,reason='same subject and slot'):
    return {'original':o,'steer':s,'status':status,'reason':reason}


def reference(a,b,arows,entities=None):
    r={'entities':entities or [row(['e1'],['e1'],'matched')],
       'alignments':[row(['entity_e1'],['entity_e1'],'retained')]+arows}
    checked=validate_alignment(r,a,b)
    assert not checked['issues'],checked['issues']
    return r


def build():
    examples=[]
    a=single('A wooden table.','table','material','wood','wooden');b=single('A table made of wood.','table','material','wood','wood')
    examples.append((a,b,reference(a,b,[row(['a1'],['a1'],'retained')])))
    a=single('A red car.','car','color','red');b=single('A car.','car')
    examples.append((a,b,reference(a,b,[row(['a1'],[],'removed')])))
    examples.append((b,a,reference(b,a,[row([],['a1'],'added')])))
    b=single('A blue car.','car','color','blue')
    examples.append((a,b,reference(a,b,[row(['a1'],['a1'],'modified')])))
    a=single('A wooden table.','table','material','wood','wooden');b=single('A red table.','table','color','red')
    examples.append((a,b,reference(a,b,[row(['a1'],[],'removed'),row([],['a1'],'added')])))
    a=normalize_document(D([E('e1','car','car'),E('e2','bench','bench')]),'A car and a bench.')
    b=single('A car.','car')
    examples.append((a,b,reference(a,b,[row(['entity_e2'],[],'removed')],
                                   [row(['e1'],['e1'],'matched'),row(['e2'],[],'original_only')])))
    a=normalize_document(D([E('e1','person','person'),E('e2','person',q('person',1))]),'A person and another person.')
    b=single('A person.','person')
    r={'entities':[row(['e1','e2'],['e1'],'unresolved','identity_unclear')],
       'alignments':[row(['entity_e1','entity_e2'],['entity_e1'],'unresolved','identity_unclear')]}
    examples.append((a,b,r))
    a=single('A red car.','car','color','red');b=single('A car is red.','car')
    gap=row(['a1'],[],'unresolved','extraction_gap');gap['opposite_evidence']=q('red')
    examples.append((a,b,reference(a,b,[gap])))
    shots=[{'example_id':f'a{i+1}','reference_status':'assistant_candidate','input':{'original':model_document(a),'steer':model_document(b)},'output':r}
           for i,(a,b,r) in enumerate(examples)]
    for a,b,r in examples:assert not validate_alignment(r,a,b)['issues']
    write_jsonl(ROOT/'shots/align.jsonl',shots)
    cases=[]
    a=single('A green bottle.','bottle','color','green');b=single('A blue bottle.','bottle','color','blue')
    cases.append(('align_01',a,b,reference(a,b,[row(['a1'],['a1'],'modified')])))
    a=single('A ceramic bowl.','bowl','material','ceramic');b=single('A small bowl.','bowl','size','small')
    cases.append(('align_02',a,b,reference(a,b,[row(['a1'],[],'removed'),row([],['a1'],'added')])))
    a=single('A wet towel.','towel','state','wet');b=single('A towel is wet.','towel')
    gap=row(['a1'],[],'unresolved','extraction_gap');gap['opposite_evidence']=q('wet')
    cases.append(('align_03',a,b,reference(a,b,[gap])))
    a=single('A mug made of glass.','mug','material','glass');b=single('A glass mug.','mug','material','glass')
    cases.append(('align_04',a,b,reference(a,b,[row(['a1'],['a1'],'retained')])))
    write_jsonl(ROOT/'fixtures/align_cases.jsonl',[{'case_id':i,'original':a,'steer':b,'reference':r,'split':'controlled_development','reference_status':'assistant_candidate'} for i,a,b,r in cases])


if __name__=='__main__':build()
