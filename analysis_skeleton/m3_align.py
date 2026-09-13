"""M3: one few-shot call, entity mapping before fact alignment; isolate invalid rows."""
import argparse
from collections import Counter
from .common import new_run,read_jsonl,write_json,write_jsonl,report,check_frozen
from .contracts import STATUSES,model_document,quote_span
from .llm import FewShotStage,CallFailure,ROOT
from .metrics import prf


def validate_alignment(raw, original, steer):
    if not isinstance(raw,dict) or not isinstance(raw.get("entities"),list) or not isinstance(raw.get("alignments"),list):
        raise ValueError("entities and alignments arrays required")
    result={"entities":[],"alignments":[],"issues":[]}
    eids={"original":{e["id"] for e in original["entities"]},"steer":{e["id"] for e in steer["entities"]}}
    def counts(rows,side):
        return Counter(i for r in rows if isinstance(r,dict) and isinstance(r.get(side),list) for i in r[side] if isinstance(i,str))
    ec={s:counts(raw["entities"],s) for s in eids}
    mapped, entity_states={},{}
    target_states={}
    for row in raw["entities"]:
        try:
            if any(not isinstance(row.get(s),list) for s in eids):
                raise ValueError("entity ID lists required")
            if any(any(not isinstance(i,str) or i not in eids[s] or ec[s][i]!=1 for i in row[s]) for s in eids):
                raise ValueError("unknown/duplicate entity reference")
            o,t=row["original"],row["steer"]
            status=row["status"]
            shape=(len(o),len(t))
            if not ((status=="matched" and shape==(1,1)) or (status=="original_only" and shape==(1,0)) or
                    (status=="steer_only" and shape==(0,1)) or (status=="unresolved" and sum(shape)>0)):
                raise ValueError("invalid entity shape/status")
            result["entities"].append(row)
            if status=="matched":mapped[o[0]]=t[0]
            for i in o:entity_states[i]=status
            for i in t:target_states[i]=status
        except (ValueError,KeyError,TypeError,AttributeError) as exc:
            result["issues"].append({"stage":"entity","raw":row,"reason":str(exc)})
    for s in eids:
        covered={i for r in result["entities"] for i in r[s]}
        for i in sorted(eids[s]-covered):
            result["entities"].append({"original":[i] if s=="original" else [],"steer":[i] if s=="steer" else [],
                                       "status":"unresolved","reason":"technical_entity_unassigned"})
            if s=="original":entity_states[i]="unresolved"
            else:target_states[i]="unresolved"
    fs={"original":{f["id"]:f for f in original["facts"]},"steer":{f["id"]:f for f in steer["facts"]}}
    fc={s:counts(raw["alignments"],s) for s in fs}
    for row in raw["alignments"]:
        try:
            if any(not isinstance(row.get(s),list) for s in fs):raise ValueError("fact ID lists required")
            if any(any(not isinstance(i,str) or i not in fs[s] or fc[s][i]!=1 for i in row[s]) for s in fs):
                raise ValueError("unknown/duplicate fact reference")
            o,t=row["original"],row["steer"]
            status=row.get("status")
            if status not in STATUSES or not(o or t):raise ValueError("invalid fact status/empty row")
            if status in {"retained","modified"}:
                if (len(o),len(t))!=(1,1):raise ValueError("determinate links are one-to-one")
                a,b=fs["original"][o[0]],fs["steer"][t[0]]
                if mapped.get(a["entity_id"])!=b["entity_id"]:raise ValueError("unresolved or different entity mapping")
                if a["type"]!=b["type"] or a["slot"]!=b["slot"]:raise ValueError("different semantic type/slot")
                if status=="modified" and a["type"]!="attribute":raise ValueError("modified restricted to attribute")
            if status=="removed" and (len(o),len(t))!=(1,0):raise ValueError("removed shape")
            if status=="added" and (len(o),len(t))!=(0,1):raise ValueError("added shape")
            if row.get("reason")=="extraction_gap":
                if status!="unresolved":raise ValueError("extraction_gap must remain unresolved")
                other=steer if o else original
                quote_span(other["text"],row["opposite_evidence"])
            if status=="removed":
                a=fs["original"][o[0]]
                state=entity_states.get(a["entity_id"],"unresolved")
                if state=="unresolved":raise ValueError("cannot remove facts with unresolved subject")
                if a['type']=='entity' and state=='matched':raise ValueError('matched entity existence cannot be removed')
                row={**row,"removal_reason":"entity_absent" if state=="original_only" else "attribute_omitted"}
            if status=='added':
                b=fs['steer'][t[0]];state=target_states.get(b['entity_id'],'unresolved')
                if state=='unresolved':raise ValueError('cannot add facts with unresolved subject')
                if b['type']=='entity' and state=='matched':raise ValueError('matched entity existence cannot be added')
            result["alignments"].append(row)
        except (ValueError,KeyError,TypeError,AttributeError) as exc:
            result["issues"].append({"stage":"fact","raw":row,"reason":str(exc)})
    for s in fs:
        covered={i for r in result["alignments"] for i in r[s]}
        for i in sorted(fs[s].keys()-covered):
            result["alignments"].append({"original":[i] if s=="original" else [],"steer":[i] if s=="steer" else [],
                                         "status":"unresolved","reason":"technical_fact_unassigned"})
    result["status"]="needs_review" if result["issues"] or any(r.get("reason","").startswith("technical") for r in result["alignments"]) else "ready"
    return result


def score_alignment(pred,ref):
    def key(row,status=True):
        return (tuple(sorted(row["original"])),tuple(sorted(row["steer"])))+((row["status"],) if status else ())
    p=[r for r in pred["alignments"] if not r.get("reason","").startswith("technical")]
    g=ref["alignments"]
    pk,gk={key(r) for r in p},{key(r) for r in g}
    by_status={s:prf(len({key(r) for r in p if r['status']==s}&{key(r) for r in g if r['status']==s}),
                     sum(r['status']==s for r in p),sum(r['status']==s for r in g)) for s in sorted(STATUSES)}
    active=[v['f1'] for v in by_status.values() if v['reference'] or v['predicted']]
    removed=[r['original'][0] for r in p if r['status']=='removed']
    retained={i for r in g if r['status']=='retained' for i in r['original']}
    denom=sum(len(r['original'])+len(r['steer']) for r in g)
    technical=sum(len(r['original'])+len(r['steer']) for r in pred['alignments'] if r.get('reason','').startswith('technical'))
    pe={key(r,False) for r in pred['entities'] if r['status']=='matched'}
    ge={key(r,False) for r in ref['entities'] if r['status']=='matched'}
    pg={key(r,False) for r in p if r.get('reason')=='extraction_gap'}
    gg={key(r,False) for r in g if r.get('reason')=='extraction_gap'}
    return {'joint':prf(len(pk&gk),len(p),len(g)),
            'entity_correspondence':prf(len(pe&ge),len(pe),len(ge)),
            'extraction_gap':prf(len(pg&gg),len(pg),len(gg)),
            'edge':prf(len({key(r,False) for r in p}&{key(r,False) for r in g}),len(p),len(g)),
            'by_status':by_status,'macro_f1':sum(active)/len(active) if active else None,
            'confirmed_false_removals':len(set(removed)&retained),'predicted_removed':len(removed),
            'technical_fact_count':technical,'reference_fact_count':denom}


def execute(cases_path,output,config="decomposition/api_config.local.json"):
    cases=read_jsonl(cases_path);stage=FewShotStage('align',config)
    out=new_run(output,'M3',[cases_path,stage.rules_path,stage.shots_path],stage.identity,
                [__file__,ROOT/'contracts.py',ROOT/'llm.py',ROOT/'metrics.py'])
    records=[]
    for c in cases:
        check_frozen(out)
        key=c['case_id'];write_json(out/(key+'_started.json'),{'started':True})
        payload={s:model_document(c[s]) for s in ('original','steer')}
        try:
            raw,audit=stage.run(payload)
            write_json(out/(key+'_response.json'),audit)
            aligned=validate_alignment(raw,c['original'],c['steer'])
        except CallFailure as exc:
            audit=exc.audit;aligned=validate_alignment({'entities':[],'alignments':[]},c['original'],c['steer'])
        except ValueError:
            aligned=validate_alignment({'entities':[],'alignments':[]},c['original'],c['steer'])
        score=score_alignment(aligned,c['reference'])
        record={'case_id':key,'alignment':aligned,'audit':audit,'score':score}
        write_json(out/(key+'.json'),record);records.append(record)
        print(f"M3 {key}: {aligned['status']}",flush=True)
    write_jsonl(out/'results.jsonl',records)
    sums={k:sum(r['score']['joint'][k] for r in records) for k in ('tp','predicted','reference')}
    metrics={'cases':len(records),'joint':prf(**sums),'per_case':[{'case_id':r['case_id'],**r['score']} for r in records],
             'reference_status':'assistant_candidate_not_gold','human_accuracy':None}
    report(out,'M3 固定事实输入的8-shot对齐测评',metrics,
           ['只送固定事实/原文；未调用M2，隔离上游误差。','技术失败保留完整事实名册但不能获得unresolved正确分。'])
    return metrics


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--cases',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();execute(a.cases,a.output)
