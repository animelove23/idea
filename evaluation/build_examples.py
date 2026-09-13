"""Assistant-authored synthetic demonstrations, independent of eight real captions."""
import copy
import json
from pathlib import Path
from decomposition.v6.schema import fold_document
from decomposition.storage import write_jsonl
from .common import document_context, require
from .coverage import apply_coverage
from .alignment import align_entities, align_facts


def document(text, specs):
    elements = []
    for spec in specs:
        category, fact, source, *qualifiers = spec
        elements.append(dict(category=category, fact=fact, source=source,
                             assertion=qualifiers[0] if qualifiers else 'asserted',
                             polarity=qualifiers[1] if len(qualifiers)>1 else 'positive'))
    doc = fold_document({'elements':elements}, text)
    require(doc['status']=='ready', str(doc))
    return doc


def entities(prefix, specs):
    return [dict(id=f'{prefix}{i}',mention=mention,fact_ids=[f'f{x}' for x in facts],description=description)
            for i,(mention,facts,description) in enumerate(specs,1)]


def bindings(prefix, specs):
    return [dict(fact_id=f'f{i}',entity_ids=[f'{prefix}{x}' for x in entity_ids],slot=slot)
            for i,(entity_ids,slot) in enumerate(specs,1)]


def row(a,b,status='retained',reason=None,evidence=None):
    return dict(original_fact_ids=[f'f{x}' for x in a],steer_fact_ids=[f'f{x}' for x in b],status=status,
                reason=reason or {'retained':'same_fact','modified':'value_changed','removed':'not_expressed','added':'not_expressed'}[status],
                evidence=evidence or [])


def build():
    cases=[]
    def add(name,a,b,oe,se,mapping,ob,sb,rows,missing=()):
        ent={'original_entities':entities('o',oe),'steer_entities':entities('s',se),'entity_alignment':[]}
        for left,right,status,reason in mapping:
            ent['entity_alignment'].append(dict(original_entity_ids=[f'o{x}' for x in left],steer_entity_ids=[f's{x}' for x in right],status=status,reason=reason))
        sidecar=align_entities(ent,a,b)
        raw=dict(original_bindings=bindings('o',ob),steer_bindings=bindings('s',sb),fact_alignment=rows)
        parsed=align_facts(raw,a,b,sidecar)
        require(parsed['status']=='ready', f'{name}: {parsed}')
        covinput=copy.deepcopy(a)
        covinput['facts']=[f for f in a['facts'] if f['id'] not in {f'f{x}' for x in missing}]
        covout={'added_elements':[{k:f[k] for k in ['category','fact','source','assertion','polarity']} for f in a['facts'] if f['id'] in {f'f{x}' for x in missing}]}
        cov=apply_coverage(covinput,covout)
        require(cov['status']=='ready' and len(cov['added_facts'])==len(missing),'bad coverage example')
        cases.append(dict(id=name,original=a,steer=b,coverage={'input':document_context(covinput),'output':covout},
                          entities={'input':{'original':document_context(a),'steer':document_context(b)},'output':ent},
                          alignment={'input':{'original':document_context(a),'steer':document_context(b),'entity_sidecar':sidecar},'output':raw}))

    # 1: same entity and narrow slot; source evidence; append-only missing color.
    def helmet(color):
        t=f'A {color} helmet rests on a crate.'
        return document(t,[('object','There is a helmet.','helmet'),('object','There is a crate.','crate'),
                           ('color',f'The helmet is {color}.',f'{color} helmet'),('spatial','The helmet is on the crate.',t)])
    es=[('helmet',[1,3,4],'helmet resting on the crate'),('crate',[2,4],'supporting crate')]
    bs=[([1],'existence'),([2],'existence'),([1],'color'),([1,2],'on')]
    match=[([1],[1],'matched','Helmet in the same supporting relation.'),([2],[2],'matched','Same supporting crate.')]
    add('helmet_color',helmet('white'),helmet('blue'),es,es,match,bs,bs,[row([i],[i],'modified' if i==3 else 'retained') for i in range(1,5)],missing=(3,))

    # 2: mention order changes; specific roles and carried objects determine correspondence.
    a=document('A nurse holds a folder. A pilot holds a radio.',[
        ('human','There is a nurse.','A nurse'),('human','There is a pilot.','A pilot'),('object','There is a folder.','a folder'),('object','There is a radio.','a radio'),
        ('relation','The nurse holds the folder.','A nurse holds a folder'),('relation','The pilot holds the radio.','A pilot holds a radio')])
    b=document('A pilot carries a radio, while a nurse carries a folder.',[
        ('human','There is a pilot.','A pilot'),('human','There is a nurse.','a nurse'),('object','There is a radio.','a radio'),('object','There is a folder.','a folder'),
        ('relation','The pilot carries the radio.','A pilot carries a radio'),('relation','The nurse carries the folder.','a nurse carries a folder')])
    # Carrying and holding only overlap: do not force complete equivalence.
    add('roles_and_order',a,b,[('A nurse',[1,5],'nurse holding folder'),('A pilot',[2,6],'pilot holding radio'),('a folder',[3,5],'folder held by nurse'),('a radio',[4,6],'radio held by pilot')],
        [('A pilot',[1,5],'pilot carrying radio'),('a nurse',[2,6],'nurse carrying folder'),('a radio',[3,5],'radio carried by pilot'),('a folder',[4,6],'folder carried by nurse')],
        [([1],[2],'matched','Nurse with folder.'),([2],[1],'matched','Pilot with radio.'),([3],[4],'matched','Folder associated with nurse.'),([4],[3],'matched','Radio associated with pilot.')],
        [([1],'existence'),([2],'existence'),([3],'existence'),([4],'existence'),([1,3],'holds'),([2,4],'holds')],
        [([1],'existence'),([2],'existence'),([3],'existence'),([4],'existence'),([1,3],'carries'),([2,4],'carries')],
        [row([1],[2]),row([2],[1]),row([3],[4]),row([4],[3]),row([5],[6],'ambiguous','partial_overlap'),row([6],[5],'ambiguous','partial_overlap')])

    # 3: multiple same-class individuals, no evidence for selecting which survives.
    a=document('A child holds a kite. Another child holds a balloon.',[
        ('human','There is a child holding a kite.','A child holds a kite'),('human','There is another child holding a balloon.','Another child holds a balloon'),
        ('object','There is a kite.','a kite'),('object','There is a balloon.','a balloon'),
        ('relation','The first child holds a kite.','A child holds a kite'),('relation','The other child holds a balloon.','Another child holds a balloon')])
    b=document('A child is smiling.',[('human','There is a child.','A child'),('action','The child is smiling.','is smiling')])
    add('uncertain_child',a,b,[('A child',[1,5],'child with kite'),('Another child',[2,6],'different child with balloon'),('a kite',[3,5],'held kite'),('a balloon',[4,6],'held balloon')],
        [('A child',[1,2],'unspecified smiling child')],
        [([1,2],[1],'ambiguous','No evidence identifies which child the shorter caption describes.'),([3],[],'original_only','No kite in shorter caption.'),([4],[],'original_only','No balloon in shorter caption.')],
        [([1],'existence'),([2],'existence'),([3],'existence'),([4],'existence'),([1,3],'holds'),([2,4],'holds')],[([1],'existence'),([1],'smile')],
        [row([1,2],[1],'ambiguous','entity_uncertain'),row([3],[],'removed'),row([4],[],'removed'),row([5,6],[2],'ambiguous','entity_uncertain')],missing=(3,))

    # 4: a qualifier embedded inside an entity statement is not a second attribute change.
    a=document('A metal lantern is on a cabinet.',[('object','There is a metal lantern.','A metal lantern'),('object','There is a cabinet.','a cabinet'),('material','The lantern is metal.','metal lantern'),('spatial','The lantern is on the cabinet.','A metal lantern is on a cabinet')])
    b=document('A lantern is on a cabinet.',[('object','There is a lantern.','A lantern'),('object','There is a cabinet.','a cabinet'),('spatial','The lantern is on the cabinet.','A lantern is on a cabinet')])
    add('embedded_material',a,b,[('A metal lantern',[1,3,4],'lantern on cabinet'),('a cabinet',[2,4],'cabinet supporting lantern')],
        [('A lantern',[1,3],'lantern on cabinet'),('a cabinet',[2,3],'cabinet supporting lantern')],
        [([1],[1],'matched','Same lantern by its support context.'),([2],[2],'matched','Same cabinet.')],
        [([1],'existence'),([2],'existence'),([1],'material'),([1,2],'on')],[([1],'existence'),([2],'existence'),([1,2],'on')],
        [row([1],[1],'ambiguous','granularity'),row([2],[2]),row([3],[],'removed'),row([4],[3])],missing=(3,))

    # 5: opposite caption says it; fact list omitted it. Source is exact, no invented quote.
    a=document('A violet curtain hangs beside a door.',[('object','There is a curtain.','A violet curtain'),('object','There is a door.','a door'),('color','The curtain is violet.','violet curtain'),('spatial','The curtain is beside the door.','A violet curtain hangs beside a door')])
    b=document('A purple curtain hangs next to a door.',[('object','There is a curtain.','A purple curtain'),('object','There is a door.','a door'),('spatial','The curtain is next to the door.','A purple curtain hangs next to a door')])
    add('missing_color_in_other_extraction',a,b,[('A violet curtain',[1,3,4],'curtain beside door'),('a door',[2,4],'door beside curtain')],
        [('A purple curtain',[1,3],'curtain next to door'),('a door',[2,3],'door next to curtain')],
        [([1],[1],'matched','Same curtain and neighboring door; violet/purple compatible.'),([2],[2],'matched','Same door.')],
        [([1],'existence'),([2],'existence'),([1],'color'),([1,2],'beside')],[([1],'existence'),([2],'existence'),([1,2],'beside')],
        [row([1],[1]),row([2],[2]),row([3],[],'ambiguous','extraction_gap',[{'side':'steer','quote':'purple curtain'}]),row([4],[3])])

    # 6: two original claims become one bundled claim, not one match plus false removal.
    a=document('Two cyclists ride next to each other on a path.',[('human','There are cyclists.','Two cyclists'),('counting','There are two cyclists.','Two cyclists'),('place','There is a path.','a path'),('action','The cyclists are riding.','cyclists ride'),('spatial','The cyclists are next to each other.','next to each other'),('location','The cyclists are on a path.','Two cyclists ride next to each other on a path')])
    b=document('Two cyclists ride side by side on a path.',[('human','There are cyclists.','Two cyclists'),('counting','There are two cyclists.','Two cyclists'),('place','There is a path.','a path'),('relation','The cyclists are riding side by side.','cyclists ride side by side'),('location','The cyclists are on a path.','Two cyclists ride side by side on a path')])
    add('many_to_one_partial_information',a,b,[('Two cyclists',[1,2,4,5,6],'pair of cyclists'),('a path',[3,6],'path under cyclists')],
        [('Two cyclists',[1,2,4,5],'pair of cyclists'),('a path',[3,5],'path under cyclists')],
        [([1],[1],'matched','Same two cyclists with matching activity and location.'),([2],[2],'matched','Same path.')],
        [([1],'existence'),([1],'count_people'),([2],'existence'),([1],'ride'),([1],'relative_position'),([1,2],'on')],
        [([1],'existence'),([1],'count_people'),([2],'existence'),([1],'ride_and_relative_position'),([1,2],'on')],
        [row([1],[1]),row([2],[2]),row([3],[3]),row([4,5],[4],'ambiguous','granularity'),row([6],[5])],missing=(5,))

    # 7: one-sided referents must be separate rows; speculative coordination uses actual quote.
    a=document('A parcel rests on a mat. The mat may be a towel. The parcel seems to be dented and torn.',[
        ('object','There is a parcel.','A parcel'),('object','There is a mat.','a mat'),('object','There may be a towel.','may be a towel','speculative'),
        ('spatial','The parcel is on the mat.','A parcel rests on a mat'),('relation','The mat may be a towel.','The mat may be a towel','speculative'),
        ('state','The parcel seems dented.','The parcel seems to be dented and torn','speculative'),('state','The parcel seems torn.','The parcel seems to be dented and torn','speculative')])
    b=document('A courier carries a parcel.',[('human','There is a courier.','A courier'),('object','There is a parcel.','a parcel'),('relation','The courier carries the parcel.','A courier carries a parcel')])
    add('one_sided_and_conjoined_speculation',a,b,[('A parcel',[1,4,6,7],'parcel on mat'),('a mat',[2,4,5],'support under parcel'),('a towel',[3,5],'speculative identification of mat')],
        [('A courier',[1,3],'carrier of parcel'),('a parcel',[2,3],'carried parcel')],
        [([1],[2],'matched','Same parcel in the only parcel description.'),([2],[],'original_only','Mat not mentioned in steer.'),([3],[],'original_only','Towel not mentioned in steer; keep its speculation, do not merge it.'),([],[1],'steer_only','Courier mentioned only in steer.')],
        [([1],'existence'),([2],'existence'),([3],'existence'),([1,2],'on'),([2,3],'identification'),([1],'dent'),([1],'tear')],
        [([1],'existence'),([2],'existence'),([1,2],'carries')],
        [row([1],[2]),row([2],[],'removed'),row([3],[],'removed'),row([4],[],'removed'),row([5],[],'removed'),row([6],[],'removed',evidence=[{'side':'original','quote':'The parcel seems to be dented and torn'}]),row([7],[],'removed',evidence=[{'side':'original','quote':'The parcel seems to be dented and torn'}]),row([],[1],'added'),row([],[3],'added')],missing=(7,))

    # 8: count units preserved; do not convert pairs into individual objects.
    def gloves(number):
        word={3:'Three',2:'Two'}[number]; t=f'{word} pairs of gloves lie on a shelf.'
        return document(t,[('object','There are gloves.',f'{word} pairs of gloves'),('object','There is a shelf.','a shelf'),('counting',f'There are {number} pairs of gloves.',f'{word} pairs of gloves'),('spatial','The gloves are on the shelf.',t)])
    add('count_with_unit',gloves(3),gloves(2),[('Three pairs of gloves',[1,3,4],'gloves group'),('a shelf',[2,4],'supporting shelf')],
        [('Two pairs of gloves',[1,3,4],'gloves group'),('a shelf',[2,4],'supporting shelf')],
        [([1],[1],'matched','Same described glove group on shelf; cardinality is a property difference, not an instance mapping.'),([2],[2],'matched','Same shelf.')],
        [([1],'existence'),([2],'existence'),([1],'count_pairs'),([1,2],'on')],[([1],'existence'),([2],'existence'),([1],'count_pairs'),([1,2],'on')],
        [row([i],[i],'modified' if i==3 else 'retained') for i in range(1,5)],missing=(3,))
    return cases


if __name__=='__main__':
    cases=build()
    out=Path('evaluation/examples');out.mkdir(exist_ok=True)
    for stage in ['coverage','entities','alignment']:
        write_jsonl(out/f'{stage}.jsonl',[dict(id=c['id'],**c[stage]) for c in cases])
    write_jsonl(out/'synthetic_sources.jsonl',[{k:c[k] for k in ['id','original','steer']} for c in cases])
    print('8 validated demonstrations per stage; 16 new synthetic captions; no real evaluation captions.')
