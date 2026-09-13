"""Deterministic, uncertainty-aware observation of frozen model outputs; no LLM."""
from collections import Counter
from itertools import product

STATES=('unchanged','gained','lost','mixed')
LABELS=('S','H')
KINDS=('entity','attribute')


def candidates(gain,loss,maybe_gain=False,maybe_loss=False):
    gs=[True] if gain else ([False,True] if maybe_gain else [False])
    ls=[True] if loss else ([False,True] if maybe_loss else [False])
    return sorted({('mixed' if g and l else 'gained' if g else 'lost' if l else 'unchanged')
                   for g,l in product(gs,ls)},key=STATES.index)


def role(row):
    label=row.get('visual_label')
    if row['type']=='attribute':
        parent=row.get('parent_visual_label')
        if parent=='hallucinated':return 'excluded_false_parent'
        if parent!='supported':return '?'
        if label=='supported' and not row.get('strict_parent_supported_eligible'):return '?'
    return {'supported':'S','hallucinated':'H'}.get(label,'?')


def length_info(bundle):
    lex={s:bundle['lexical'][s]['caption'] for s in ('original','steer')}
    a,b=lex['original']['word_len'],lex['steer']['word_len']
    pos=set(lex['original']['pos_counts'])|set(lex['steer']['pos_counts'])
    changes={p:lex['original']['pos_counts'].get(p,0)-lex['steer']['pos_counts'].get(p,0) for p in sorted(pos)}
    assert sum(changes.values())==a-b
    return {'original_words':a,'steer_words':b,'word_change':b-a,
        'word_reduction':(a-b)/a if a else None,
        'length_group':'shorter' if b<a else 'longer' if b>a else 'unchanged',
        'pos_original':lex['original']['pos_counts'],'pos_steer':lex['steer']['pos_counts'],
        'pos_net_reduction':changes,'pos_reduction_contribution':{p:n/a if a else None for p,n in changes.items()}}


def analyze_pair(bundle,ledger):
    pid=bundle['pair_id']
    rows={(r['side'],r['fact_id']):r for r in ledger}
    expected={(s,f['id']) for s in ('original','steer') for f in bundle[s]['facts']}
    assert len(rows)==len(ledger) and set(rows)==expected
    counts=Counter();possible=Counter();events=[];quality=Counter();seen=set()
    base=Counter();presence_unknown=Counter();attribute_removed=Counter()
    for (side,fid),r in rows.items():
        k=role(r);base[(side,r['type'],k)]+=1
        if k=='?':presence_unknown[side]+=1
        if k=='excluded_false_parent':quality['attributes_on_false_subject']+=1
        if r.get('truth_conflict'):quality['parent_attribute_conflict']+=1
        if r.get('visual_label')=='uncertain':quality['visual_uncertain_facts']+=1
        if r.get('visual_label')=='pending':quality['visual_pending_facts']+=1
        if r.get('alignment_axis')=='technical_unresolved':quality['alignment_technical_facts']+=1
        if r.get('alignment_axis')=='semantic_unresolved':quality['alignment_semantic_facts']+=1
    extraction_issues=sum(len(bundle[s].get('issues',[])) for s in ('original','steer'))
    quality['extraction_issues']=extraction_issues

    def event(side,fid,action,status,edge_index,uncertain=False):
        r=rows[(side,fid)];k=role(r);kind=r['type']
        rec={'pair_id':pid,'side':side,'fact_id':fid,'entity_id':r['entity_id'],
             'type':kind,'slot':r['slot'],'value':r.get('value'),'role':k,'action':action,
             'alignment_status':status,'edge_index':edge_index,'uncertain':uncertain or k=='?',
             'parent_visual_label':r.get('parent_visual_label'),'visual_label':r['visual_label']}
        events.append(rec)
        if k=='excluded_false_parent':return
        if action=='retained':
            if k in LABELS:counts[(kind,k,'retained')]+=1
            return
        if uncertain or k=='?':
            for lab in LABELS if k=='?' else (k,):possible[(kind,lab,action)]+=1
        else:
            counts[(kind,k,action)]+=1
            sub='removed' if status=='removed' else 'added' if status=='added' else 'modified_out' if side=='original' else 'modified_in'
            counts[(kind,k,sub)]+=1
        if kind=='attribute' and side=='original' and status=='removed' and k=='S':
            parent=rows.get((side,'entity_'+r['entity_id']))
            category='other_or_unresolved'
            if parent and parent['status']=='removed':category='parent_removed'
            elif parent and parent['status']=='retained' and parent['visual_label']=='supported':
                edge=next((e for e in bundle['alignment']['alignments'] if parent['fact_id'] in e['original']),None)
                if edge and len(edge['steer'])==1 and rows[('steer',edge['steer'][0])]['visual_label']=='supported':category='parent_retained_attribute_removed'
            attribute_removed[category]+=1;rec['attribute_removal_component']=category

    for i,edge in enumerate(bundle['alignment']['alignments']):
        status=edge['status'];refs=[(s,f) for s in ('original','steer') for f in edge[s]]
        assert not seen&set(refs);seen.update(refs)
        if status=='retained':
            assert len(edge['original'])==len(edge['steer'])==1
            left,right=rows[('original',edge['original'][0])],rows[('steer',edge['steer'][0])]
            lr,rr=role(left),role(right)
            label_conflict=lr in LABELS and rr in LABELS and lr!=rr
            qualification_conflict=(lr=='excluded_false_parent')!=(rr=='excluded_false_parent')
            if label_conflict or qualification_conflict:
                quality['retained_label_or_parent_conflicts']+=1
                for kind in {left['type'],right['type']}:
                    for lab in LABELS:
                        for action in ('gain','loss'):possible[(kind,lab,action)]+=1
                events.append({'pair_id':pid,'edge_index':i,'action':'retained_conflict','refs':refs,'uncertain':True})
            else:event('original',edge['original'][0],'retained',status,i)
        else:
            assert status in ('removed','added','modified','unresolved')
            for side,fid in refs:event(side,fid,'loss' if side=='original' else 'gain',status,i,status=='unresolved')
    assert seen==expected

    components=[]
    for kind,lab in product(KINDS,LABELS):
        row={'type':kind,'role':lab,'original_count':base[('original',kind,lab)],'steer_count':base[('steer',kind,lab)]}
        row.update({name:counts[(kind,lab,name)] for name in ('retained','loss','gain','removed','added','modified_out','modified_in')})
        row.update(possible_loss=possible[(kind,lab,'loss')],possible_gain=possible[(kind,lab,'gain')])
        components.append(row)
    states={};candidate_states={}
    for lab in LABELS:
        gg=sum(counts[(k,lab,'gain')] for k in KINDS);ll=sum(counts[(k,lab,'loss')] for k in KINDS)
        mg=any(possible[(k,lab,'gain')] for k in KINDS);ml=any(possible[(k,lab,'loss')] for k in KINDS)
        cs=list(STATES) if extraction_issues else candidates(gg,ll,mg,ml)
        candidate_states[lab]=cs;states[lab]=cs[0] if len(cs)==1 else 'unresolved'
    h0=sum(base[('original',k,'H')] for k in KINDS);h1=sum(base[('steer',k,'H')] for k in KINDS)
    h_unchanged=None
    if states['H']=='unchanged':
        h_unchanged=('known_nonzero_unchanged' if h0 or h1 else 'both_zero_confirmed'
                     if not sum(presence_unknown.values()) else 'zero_known_but_visual_membership_unknown')
    result={'pair_id':pid,**length_info(bundle),'supported_change':states['S'],'hallucination_change':states['H'],
        'candidate_states':candidate_states,'matrix_classifiable':all(v!='unresolved' for v in states.values()),
        'hallucination_unchanged_subtype':h_unchanged,'components':components,
        'attribute_removal_components':dict(attribute_removed),'quality':dict(quality),
        'accepted_facts':len(ledger),'independent_visual_accuracy_available':False,
        'entity_mentions':{s:sum(len(e.get('mentions',[])) for e in bundle[s]['entities']) for s in ('original','steer')},
        'repeat_mention_proxy':{s:sum(max(len(e.get('mentions',[]))-1,0) for e in bundle[s]['entities']) for s in ('original','steer')}}
    return result,events
