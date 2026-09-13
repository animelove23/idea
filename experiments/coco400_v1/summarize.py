"""Aggregate completed frozen pair runs into motivation-first observations and figures."""
import html
import json
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,write_csv,check_frozen,sha
from analysis_skeleton.m1_lexical import LexicalRecorder
from .observe import analyze_pair,length_info,KINDS,LABELS

ROOT=Path('outputs/coco400_final_v1')
LENGTHS=('shorter','unchanged','longer')
HSTATES=('lost','unchanged','gained','mixed')
SSTATES=('unchanged','gained','lost','mixed')


def csv(path,rows):
    fields=sorted(set().union(*(r.keys() for r in rows))) if rows else ['empty']
    write_csv(path,fields,[{k:r.get(k) for k in fields} for r in rows])


def collect():
    out=ROOT/'observations';out.mkdir(exist_ok=True)
    pairs=read_jsonl(ROOT/'pairs.jsonl');assert len(pairs)==400
    by_id={p['pair_id']:p for p in pairs}
    observations=[];events=[];component_rows=[];ledgers=[];calls=[];failures=[];known_runs=[]
    parser=None
    for p in pairs:
        pid=p['pair_id'];run=ROOT/'runs'/pid
        if run.exists():
            for path in (run/'checkpoints').glob('*.json'):
                if path.name.endswith('_response.json'):continue
                value=read_json(path)['value'];audit=value.get('audit',{})
                calls.append({'pair_id':pid,'task_key':value['task_key'],'status':value['status'],
                    'failure_phase':value.get('phase'),'diagnostic':value.get('diagnostic'),
                    'stage':audit.get('stage'),'api_calls':audit.get('api_calls',0),
                    'requested_model':audit.get('identity',{}).get('model'),'response_model':audit.get('response_model'),
                    'response_id':audit.get('response_id'),'error':audit.get('error'),
                    'elapsed_seconds':audit.get('elapsed_seconds'),'usage':audit.get('usage'),
                    'checkpoint_path':str(path.resolve())})
        if (run/'metrics.json').exists():
            check_frozen(run);known_runs.append(pid)
            bundles=read_jsonl(run/'bundles.jsonl');ledger=read_jsonl(run/'denominator_ledger.jsonl')
            if len(bundles)==1:
                assert bundles[0]['pair_id']==pid
                result,ee=analyze_pair(bundles[0],ledger)
                result['run_metrics']=read_json(run/'metrics.json')
                result['known_development_overlap']=p['known_development_overlap']
                observations.append(result);events+=ee;ledgers+=ledger
                for r in result['components']:
                    component_rows.append({'pair_id':pid,'length_group':result['length_group'],
                        'supported_change':result['supported_change'],'hallucination_change':result['hallucination_change'],**r})
                continue
        failures.append(pid)
        if parser is None:parser=LexicalRecorder()
        stub={'lexical':{s:parser.record(p[s]['caption_id'],p[s]['text']) for s in ('original','steer')}}
        observations.append({'pair_id':pid,**length_info(stub),'supported_change':'unresolved','hallucination_change':'unresolved',
            'matrix_classifiable':False,'candidate_states':{'S':list(SSTATES),'H':list(HSTATES)},
            'components':[],'quality':{'pair_analysis_unavailable':1},'known_development_overlap':p['known_development_overlap']})
    assert len(observations)==400
    matrix=[]
    for length in LENGTHS:
        group=[r for r in observations if r['length_group']==length];n=len(group)
        resolved=sum(r['matrix_classifiable'] for r in group)
        for h in HSTATES:
            for s in SSTATES:
                ids=[r['pair_id'] for r in group if r['hallucination_change']==h and r['supported_change']==s]
                possible_ids=[r['pair_id'] for r in group if h in r['candidate_states']['H'] and s in r['candidate_states']['S']]
                matrix.append({'length_group':length,'hallucination_change':h,'supported_change':s,
                    'count':len(ids),'length_group_denominator':n,'fraction_all_in_length_group':len(ids)/n if n else None,
                    'classifiable_denominator':resolved,'fraction_classifiable':len(ids)/resolved if resolved else None,'pair_ids':ids,
                    'possible_count_including_unresolved':len(possible_ids),
                    'possible_fraction_including_unresolved':len(possible_ids)/n if n else None})
        assert sum(r['count'] for r in matrix if r['length_group']==length)+n-resolved==n
    quality=Counter()
    for row in observations:quality.update(row['quality'])
    ids=[r['response_id'] for r in calls if r['response_id']]
    assert len(ids)==len(set(ids)),'response_id_reused_across_calls'
    request_models=Counter(r['requested_model'] for r in calls if r['api_calls'])
    response_models=Counter(r['response_model'] for r in calls if r['response_model'])
    assert set(request_models)<={'deepseek-flash'} and set(response_models)<={'deepseek-flash'}
    totals={}
    for kind in KINDS:
        for label in LABELS:
            rr=[r for r in component_rows if r['type']==kind and r['role']==label]
            totals[kind+'_'+label]={k:sum(r[k] for r in rr) for k in ('original_count','steer_count','retained','loss','gain','removed','added','modified_out','modified_in','possible_loss','possible_gain')}
    attr=Counter()
    for row in observations:attr.update(row.get('attribute_removal_components',{}))
    word_reductions=[r['word_reduction'] for r in observations if r['word_reduction'] is not None]
    summary={'selected_pairs':400,'exported_runs':len(known_runs),'analyzed_pairs':400-len(failures),'failed_pair_ids':failures,
        'length_counts':dict(Counter(r['length_group'] for r in observations)),
        'matrix_classifiable_by_length':{g:sum(r['length_group']==g and r['matrix_classifiable'] for r in observations) for g in LENGTHS},
        'matrix_unresolved_by_length':{g:sum(r['length_group']==g and not r['matrix_classifiable'] for r in observations) for g in LENGTHS},
        'original_words':sum(r['original_words'] for r in observations),'steer_words':sum(r['steer_words'] for r in observations),
        'mean_word_reduction':float(np.mean(word_reductions)) if word_reductions else None,
        'median_word_reduction':float(np.median(word_reductions)) if word_reductions else None,
        'component_totals':totals,'attribute_removed_components':dict(attr),'quality':dict(quality),
        'quality_affected_pairs':dict(Counter(k for r in observations for k,v in r['quality'].items() if v)),
        'entity_mentions':{side:sum(r.get('entity_mentions',{}).get(side,0) for r in observations) for side in ('original','steer')},
        'repeat_mention_proxy':{side:sum(r.get('repeat_mention_proxy',{}).get(side,0) for r in observations) for side in ('original','steer')},
        'accepted_fact_rows':len(ledgers),'visual_fact_labels':dict(Counter(r['visual_label'] for r in ledgers)),
        'call_status':dict(Counter(r['status'] for r in calls)),
        'stage_calls':dict(Counter(r['stage'] for r in calls)),
        'new_api_calls_recorded_in_checkpoints':sum(r['api_calls'] for r in calls),
        'unique_response_ids':len(ids),'requested_models':dict(request_models),'response_models':dict(response_models),
        'usage':{k:sum((r['usage'] or {}).get(k,0) or 0 for r in calls) for k in ('prompt_tokens','completion_tokens','total_tokens')},
        'known_development_overlap':sum(r['known_development_overlap'] for r in observations),
        'hallucination_unchanged_subtypes':dict(Counter(r.get('hallucination_unchanged_subtype') for r in observations if r.get('hallucination_unchanged_subtype'))),
        'reference_visual_accuracy_available':False,'causal_mechanism_established':False,
        'labels':'automatic_frozen_M5_predictions_not_human_gold',
        'matrix_definition':'S/H gain and loss of aligned atomic propositions; modified keeps paired loss/gain; uncertain memberships not filled with zero',
        'observation_code_sha256':sha(Path(__file__).with_name('observe.py'))}
    assert summary['observation_code_sha256']==read_json(ROOT/'protocol.json')['observation_code_sha256']
    profiles=[]
    for length,h,s,kind,label in sorted({(r['length_group'],r['hallucination_change'],r['supported_change'],r['type'],r['role']) for r in component_rows}):
        rr=[r for r in component_rows if (r['length_group'],r['hallucination_change'],r['supported_change'],r['type'],r['role'])==(length,h,s,kind,label)]
        profiles.append({'length_group':length,'hallucination_change':h,'supported_change':s,'type':kind,'role':label,'pairs':len(rr),
            **{k:sum(r[k] for r in rr) for k in ('original_count','steer_count','retained','loss','gain','removed','added','modified_out','modified_in','possible_loss','possible_gain')}})
    pos_rows=[]
    for row in observations:
        for tag,n in row['pos_net_reduction'].items():
            pos_rows.append({'pair_id':row['pair_id'],'length_group':row['length_group'],
                'hallucination_change':row['hallucination_change'],'supported_change':row['supported_change'],
                'pos':tag,'original_count':row['pos_original'].get(tag,0),'steer_count':row['pos_steer'].get(tag,0),
                'net_reduction':n,'contribution_to_original_words':row['pos_reduction_contribution'][tag]})
    write_jsonl(out/'observation_pairs.jsonl',observations);write_jsonl(out/'metric_audit.jsonl',events)
    write_jsonl(out/'denominator_ledger.jsonl',ledgers);write_jsonl(out/'api_call_audit.jsonl',calls)
    csv(out/'change_matrices.csv',matrix);csv(out/'component_profiles.csv',profiles)
    csv(out/'pair_components.csv',component_rows);csv(out/'pos_components.csv',pos_rows)
    csv(out/'pair_metrics.csv',[{k:v for k,v in r.items() if k not in ('components','run_metrics')} for r in observations])
    write_json(out/'summary.json',summary)
    write_json(out/'matrix_missingness.json',{'unresolved_pairs':[{k:r[k] for k in ('pair_id','length_group','supported_change','hallucination_change','candidate_states','quality')} for r in observations if not r['matrix_classifiable']]})
    return observations,events,matrix,summary,by_id


def figures(rows,matrix,summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    out=ROOT/'observations'
    fig,axes=plt.subplots(1,3,figsize=(17,6.2))
    color_max=max(1,max(r['count'] for r in matrix))
    for ax,length in zip(axes,LENGTHS):
        subset=[r for r in matrix if r['length_group']==length]
        data=np.array([[next(r['count'] for r in subset if r['hallucination_change']==h and r['supported_change']==s) for s in SSTATES] for h in HSTATES])
        n=summary['length_counts'].get(length,0);unresolved=summary['matrix_unresolved_by_length'][length]
        ax.imshow(data,cmap='Blues',vmin=0,vmax=color_max)
        for i,j in product_indices():
            count=data[i,j];p=f'{100*count/n:.1f}%' if n else 'N/A'
            ax.text(j,i,f'{count}\n{p}',ha='center',va='center',color='white' if count>color_max*.6 else 'black',fontsize=10)
        ax.set_xticks(range(4),['Same','Gain','Loss','Mixed']);ax.set_yticks(range(4),['Loss','Same','Gain','Mixed'])
        ax.set_xlabel('Supported information change');ax.set_ylabel('Hallucination change')
        ax.set_title(f'{length.title()}: N={n}\nUnclassified: {unresolved}')
    fig.suptitle('COCO 400 | Frozen Final v1 | Automatic labels\nPercentages use ALL pairs in each length group, including unclassified pairs',fontsize=13)
    fig.tight_layout();fig.savefig(out/'change_matrices.png',dpi=170,bbox_inches='tight');plt.close(fig)
    keys=['entity_S','entity_H','attribute_S','attribute_H']
    fig,ax=plt.subplots(figsize=(9,5));x=np.arange(4)
    for offset,key,label,color in [(-.26,'removed','Removed','#de7061'),(0,'modified_out','Modified out','#e8bb63'),(.26,'retained','Retained','#588eb5')]:
        vals=[]
        for kind in keys:
            c=summary['component_totals'][kind];den=c['original_count'];vals.append(c[key]/den if den else np.nan)
        ax.bar(x+offset,vals,.24,label=label,color=color)
    ax.set_xticks(x,[f'{k}\nN={summary["component_totals"][k]["original_count"]}' for k in keys]);ax.set_ylim(0,1)
    ax.set_ylabel('Fraction of original classified component');ax.legend();ax.set_title('Semantic components | Unknown transitions remain outside these bars')
    fig.tight_layout();fig.savefig(out/'semantic_components.png',dpi=170);plt.close(fig)
    groups={'Noun/proper noun':{'NOUN','PROPN'},'Adjective':{'ADJ'},'Verb':{'VERB'},'Adverb':{'ADV'}}
    short=[r for r in rows if r['length_group']=='shorter'];names=[*groups,'Other POS'];values=[]
    used=set().union(*groups.values())
    for name in names:
        ns=sum(sum(n for p,n in r['pos_net_reduction'].items() if (p in groups[name] if name in groups else p not in used)) for r in short)
        den=sum(r['original_words'] for r in short);values.append(100*ns/den if den else 0)
    fig,ax=plt.subplots(figsize=(9,4.5));ax.barh(names,values,color='#588eb5');ax.axvline(0,color='black',lw=.6)
    ax.set_xlabel('Net word reduction / original words (%)');ax.set_title(f'POS composition of shortening | N={len(short)} | Net counts, not semantic causes')
    fig.tight_layout();fig.savefig(out/'pos_composition.png',dpi=170);plt.close(fig)


def product_indices():
    return ((i,j) for i in range(4) for j in range(4))


def gallery(rows,events,pairs):
    cards=[];ev=defaultdict(list)
    for e in events:ev[e['pair_id']].append(e)
    for r in rows:
        p=pairs[r['pair_id']];escape=lambda v:html.escape(str(v))
        ee=ev[r['pair_id']]
        items=''.join(f'<tr><td>{escape(e.get("type",""))}</td><td>{escape(e.get("role",""))}</td><td>{escape(e["action"])}</td><td>{escape(e.get("value",""))}</td><td>{escape(e.get("alignment_status",""))}</td></tr>' for e in ee if e['action']!='retained')
        cards.append(f'<article data-length="{r["length_group"]}" data-h="{r["hallucination_change"]}" data-s="{r["supported_change"]}"><h2>{r["pair_id"]} · {r["length_group"]} · H:{r["hallucination_change"]} / S:{r["supported_change"]}</h2><img loading="lazy" src="{escape(Path(p["image_path"]).as_uri())}"><div><b>Original ({r["original_words"]} words)</b><p>{escape(p["original"]["text"])}</p><b>Steer ({r["steer_words"]} words)</b><p>{escape(p["steer"]["text"])}</p><p>Quality: {escape(json.dumps(r["quality"]))}</p><table><tr><th>Type</th><th>S/H/?</th><th>Event</th><th>Value</th><th>Alignment</th></tr>{items}</table></div></article>')
    options=lambda items:''.join(f'<option value="{x}">{x}</option>' for x in items)
    doc='''<!doctype html><html><meta charset="utf-8"><title>COCO 400 observation audit</title><style>body{font:15px system-ui;background:#f3f5f7;color:#142333;margin:28px}header{position:sticky;top:0;background:#fff;padding:16px;border-bottom:2px solid #567;z-index:2}article{display:grid;grid-template-columns:330px 1fr;gap:20px;padding:20px;margin:18px 0;background:white;border-radius:8px}h2{grid-column:1/-1;margin:0}img{max-width:330px;max-height:360px}table{border-collapse:collapse;width:100%}td,th{border-bottom:1px solid #ddd;padding:5px;text-align:left}p{line-height:1.6}select,input{padding:7px;margin-right:8px}.hide{display:none}small{color:#567}</style><header><h1>COCO 400: frozen-framework observation audit</h1><small>Automatic S/H labels, not human gold. All cases are retained; uncertain cases are searchable.</small><p><select id="length"><option value="">All lengths</option>'''+options(LENGTHS)+'''</select><select id="h"><option value="">All H changes</option>'''+options((*HSTATES,'unresolved'))+'''</select><select id="s"><option value="">All S changes</option>'''+options((*SSTATES,'unresolved'))+'''</select><input id="search" placeholder="Image ID or text"><span id="count"></span></p></header>'''+''.join(cards)+'''<script>function filter(){let n=0;const q=document.querySelector('#search').value.toLowerCase();document.querySelectorAll('article').forEach(a=>{const ok=['length','h','s'].every(k=>!document.getElementById(k).value||a.dataset[k]===document.getElementById(k).value)&&(!q||a.textContent.toLowerCase().includes(q));a.classList.toggle('hide',!ok);n+=ok});document.querySelector('#count').textContent=n+' / 400'}document.querySelectorAll('select,input').forEach(x=>x.addEventListener('input',filter));filter();</script></html>'''
    (ROOT/'observations/case_gallery.html').write_text(doc,encoding='utf-8')


if __name__=='__main__':
    rows,events,matrix,summary,pairs=collect();figures(rows,matrix,summary);gallery(rows,events,pairs)
    print(json.dumps(summary,ensure_ascii=False,indent=2))
