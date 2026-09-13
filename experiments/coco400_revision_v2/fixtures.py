"""Eight minimal demonstrations and eight distinct contract probes, not human gold."""
from pathlib import Path
from analysis_skeleton.common import write_jsonl
ROOT=Path(__file__).parent


def doc(text,name,attribute=None):
    start=text.index(name);span={'quote':name,'occurrence':0,'start':start,'end':start+len(name)}
    d={'text':text,'entities':[{'id':'e1','name':name,'mentions':[span]}],
       'facts':[{'id':'entity_e1','entity_id':'e1','type':'entity','slot':'existence','value':name,'source_spans':[span],'value_spans':[span]}],'issues':[]}
    if attribute:
        value,slot=attribute;start=text.index(value);a={'quote':value,'occurrence':0,'start':start,'end':start+len(value)}
        d['facts'].append({'id':'a1','entity_id':'e1','type':'attribute','slot':slot,'value':value,'source_spans':[a],'value_spans':[a]})
    return d


def cases(probe=False):
    a,b=('girl','person') if probe else ('boy','person')
    animal=('bird','animal') if probe else ('dog','animal')
    obj='lamp' if probe else 'clock';place='desk' if probe else 'table';part='desktop' if probe else 'tabletop'
    result=[]
    def add(name,o,t,change='equivalent',status='matched',fact_status='retained',attr=None):
        edges=[{'original':['entity_e1'],'steer':['entity_e1'],'status':fact_status,'reason':name}]
        if attr:edges+=attr
        result.append({'example_id':name,'input':{'original':o,'steer':t},'output':{
            'entities':[{'original':['e1'],'steer':['e1'],'status':status,'description_change':change,'reason':name}],
            'alignments':edges}})
    add('same_subject_equivalent',doc('A '+obj+' is beside the window.',obj),doc('Beside the window is a '+obj+'.',obj))
    add('same_subject_generalized',doc('A '+a+' holds a kite.',a),doc('A '+b+' holds the kite.',b),'generalized',fact_status='description_changed')
    add('same_subject_specialized',doc('An '+animal[1]+' rests beside the gate.',animal[1]),doc('The '+animal[0]+' rests beside the gate.',animal[0]),'specialized',fact_status='description_changed')
    add('part_whole_not_identical',doc('A '+place+' is in the room.',place),doc('The '+part+' is visible.',part),'part_whole','unresolved','unresolved')
    add('owner_specific_omission',doc('A wooden '+obj+' stands nearby.',obj,('wooden','material')),
        doc('The '+obj+' is beside a wooden shelf.',obj),attr=[{'original':['a1'],'steer':[],'status':'removed','reason':'wooden modifies shelf not target'}])
    add('extraction_gap_not_deletion',doc('A blue '+obj+' stands nearby.',obj,('blue','color')),
        doc('The blue '+obj+' is nearby.',obj),attr=[{'original':['a1'],'steer':[],'status':'unresolved','reason':'extraction_gap','opposite_evidence':{'quote':'blue','occurrence':0}}])
    add('attribute_value_changed',doc('A red '+obj+' stands nearby.',obj,('red','color')),
        doc('The blue '+obj+' stands nearby.',obj,('blue','color')),attr=[{'original':['a1'],'steer':['a1'],'status':'modified','reason':'same referent same slot different value'}])
    # The same hypernym relation does not link referents at incompatible positions.
    o=doc('A '+animal[0]+' is by the left door.',animal[0]);t=doc('An '+animal[1]+' is by the right door.',animal[1])
    add('hypernym_without_identity',o,t,'unresolved','unresolved','unresolved')
    return result


if __name__=='__main__':
    write_jsonl(ROOT/'align_shots.jsonl',cases())
    write_jsonl(ROOT/'align_probes.jsonl',cases(True))
