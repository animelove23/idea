"""Frozen-reference alignment metrics. No model-based judging or reference rewriting."""
from collections import Counter

STATES = ('retained','removed','added','modified','ambiguous')
TECHNICAL = {'stage_failed','alignment_validation_error'}


def prf(tp, predicted, reference):
    p = tp/predicted if predicted else None
    r = tp/reference if reference else None
    return dict(tp=tp,predicted=predicted,reference=reference,precision=p,recall=r,
                f1=2*tp/(predicted+reference) if predicted+reference else None)


def rowkey(pid,row,labeled=False):
    key=(pid,tuple(sorted(row['original_fact_ids'])),tuple(sorted(row['steer_fact_ids'])))
    return key+(row['status'],) if labeled else key


def compute(references,predictions,states=STATES):
    gold={x['pair_id']:x for x in references}; pred={x['pair_id']:x for x in predictions}
    assert len(gold)==len(references) and len(pred)==len(predictions) and set(pred)<=set(gold)
    ge=set();pe=set();gj=set();pj=set(); confusion=Counter(); per_class={}; errors=[]; frr=[]
    tech=0;fact_total=0;gap_gold=set();gap_pred=set();invalid_rows=0
    for pid,g in gold.items():
        gr=g['fact_alignment']; a=pred.get(pid); rows=a['fact_alignment'] if a else []
        # Fixed enrollment: missing predictions produce false negatives and failure status, never removed.
        gm={};pm={}
        for row in gr:
            ge.add(rowkey(pid,row));gj.add(rowkey(pid,row,True))
            for side in ('original','steer'):
                for fid in row[side+'_fact_ids']:
                    assert (side,fid) not in gm
                    gm[side,fid]=row
                    if row['reason']=='extraction_gap':gap_gold.add((pid,side,fid))
        for ix,row in enumerate(rows):
            failed=row['reason'] in TECHNICAL
            if failed:
                # Count attempted failed groups in precision denominators but never award a TP, even for gold ambiguous.
                pe.add((pid,'technical_failure',ix));pj.add((pid,'technical_failure',ix,'failed'));invalid_rows+=1
            else:
                pe.add(rowkey(pid,row));pj.add(rowkey(pid,row,True))
            for side in ('original','steer'):
                for fid in row[side+'_fact_ids']:
                    assert (side,fid) in gm and (side,fid) not in pm,(pid,side,fid)
                    pm[side,fid]=row
                    if not failed and row['reason']=='extraction_gap':gap_pred.add((pid,side,fid))
        for key,grow in gm.items():
            prow=pm.get(key);failed=not prow or prow['reason'] in TECHNICAL
            gs=grow['status'];ps='technical_failure' if failed else prow['status']
            confusion[gs,ps]+=1;fact_total+=1;tech+=failed
            if prow and ps=='removed' and key[0]=='original':
                frr.append(dict(pair_id=pid,side=key[0],fact_id=key[1],gold_status=gs,
                    survival=grow['survival_in_opposite_caption'],false_removal=grow['survival_in_opposite_caption']=='present'))
            if failed or rowkey(pid,grow,True)!=rowkey(pid,prow,True):
                errors.append(dict(pair_id=pid,side=key[0],fact_id=key[1],gold_status=gs,predicted_status=ps,
                    gold_original_ids=grow['original_fact_ids'],gold_steer_ids=grow['steer_fact_ids'],
                    predicted_original_ids=prow['original_fact_ids'] if prow else [],predicted_steer_ids=prow['steer_fact_ids'] if prow else [],
                    gold_reason=grow['reason'],predicted_reason=prow['reason'] if prow else 'missing_prediction'))
    for s in states:
        tp=confusion[s,s];pp=sum(n for (g,p),n in confusion.items() if p==s);gg=sum(n for (g,p),n in confusion.items() if g==s)
        per_class[s]=prf(tp,pp,gg)
    present=sum(x['survival']=='present' for x in frr);partial=sum(x['survival']=='partial' for x in frr);uncertain=sum(x['survival']=='uncertain' for x in frr)
    both_g={k for k in ge if k[1] and k[2]};both_p={k for k in pe if len(k)==3 and isinstance(k[1],tuple) and k[1] and k[2]}
    result=dict(pairs_planned=len(gold),pairs_returned=len(pred),facts=fact_total,
        alignment_edge=prf(len(ge&pe),len(pe),len(ge)),joint_edge_status=prf(len(gj&pj),len(pj),len(gj)),
        two_sided_edges_only=prf(len(both_g&both_p),len(both_p),len(both_g)),
        status_per_class=per_class,status_macro_f1=sum(c['f1'] for c in per_class.values() if c['f1'] is not None)/sum(c['f1'] is not None for c in per_class.values()),
        macro_classes=sum(c['f1'] is not None for c in per_class.values()),
        confusion=[dict(reference=g,predicted=p,count=n) for (g,p),n in sorted(confusion.items())],
        technical_failure=dict(facts=tech,total=fact_total,rate=tech/fact_total if fact_total else None,rows=invalid_rows),
        false_removal=dict(confirmed_false=present,predicted_removed=len(frr),partial_overlap=partial,uncertain=uncertain,
            rate=present/len(frr) if frr else None,upper_bound=(present+partial+uncertain)/len(frr) if frr else None),
        extraction_gap=prf(len(gap_gold&gap_pred),len(gap_pred),len(gap_gold)),human_reviewed=False)
    return result,errors,frr
