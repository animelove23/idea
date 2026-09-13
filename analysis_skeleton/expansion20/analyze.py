"""Post-run descriptive statistics, scoped candidate checks and standalone plots. No API."""
import json
from collections import Counter,defaultdict
from pathlib import Path
import numpy as np
from analysis_skeleton.common import read_json,read_jsonl,write_json,write_jsonl,write_csv,new_run,check_frozen,ratio,report
from analysis_skeleton.contracts import normalize_document
from analysis_skeleton.metrics import matching,normal,overlap,prf
from analysis_skeleton.m5_verify import score_labels
from analysis_skeleton.m6_analysis import analyze

ROOT=Path('outputs/skeleton_expansion20')
DATA=Path('analysis_skeleton/fixtures/expansion20')


def fact_mapping(pred,ref):
    pairs=matching(pred['entities'],ref['entities'],lambda a,b:normal(a['name'])==normal(b['name']) and overlap(a['mentions'],b['mentions']))
    entities={pred['entities'][i]['id']:ref['entities'][j]['id'] for i,j in pairs}
    pairs=matching(pred['facts'],ref['facts'],lambda a,b:a['type']==b['type'] and a['slot']==b['slot'] and normal(a['value'])==normal(b['value']) and entities.get(a['entity_id'])==b['entity_id'])
    return {ref['facts'][j]['id']:pred['facts'][i]['id'] for i,j in pairs}


def bootstrap(pairs,selection,repetitions=2000):
    rng=np.random.default_rng(1994)
    ids=[p['pair_id'] for p in pairs]
    groups=[[ids.index(s['pair_id']) for s in selection if s['length_stratum']==k] for k in range(1,5)]
    draws=[np.concatenate([rng.choice(g,len(g),replace=True) for g in groups]) for _ in range(repetitions)]
    result={}
    for kind in ('entity','attribute'):
        for label in ('true','hallucinated'):
            denom=np.array([p[kind][label]['denominator'] for p in pairs])
            for metric in ('removed','retained'):
                numerator=np.array([p[kind][label][metric] for p in pairs])
                rates=[numerator[idx].sum()/denom[idx].sum() for idx in draws if denom[idx].sum()]
                result[kind+'_'+label+'_'+metric]={'numerator':int(numerator.sum()),'denominator':int(denom.sum()),
                    'rate':ratio(int(numerator.sum()),int(denom.sum())),
                    'ci95':np.quantile(rates,[.025,.975]).tolist() if rates else None,
                    'valid_resamples':len(rates)}
    return {'unit':'image','stratified_by':'original_caption_length_quartile','repetitions':repetitions,'seed':1994,
            'interpretation':'Sampling uncertainty within this stratified 20-image development set; excludes judge/reference/systematic measurement error.',
            'rates':result}


def plots(out,rows,pair_rows):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'figure.dpi':150,'savefig.bbox':'tight'})
    def save(fig,name):
        for extension in ('png','svg'):fig.savefig(out/(name+'.'+extension))
        plt.close(fig)
    fig,ax=plt.subplots(figsize=(7,4.6))
    for kind,color,marker in [('entity','#2563eb','o'),('attribute','#d97706','^')]:
        pts=[p for p in pair_rows if p[kind+'_supported_original']]
        ax.scatter([p['word_change_pct'] for p in pts],[p[kind+'_retained_rate'] for p in pts],
                   label=f'{kind} (n={len(pts)} images)',color=color,marker=marker,alpha=.8)
    ax.set(xlabel='Caption word change (%)',ylabel='Retained / original judge-supported facts',ylim=(-.04,1.04),
           title='Length change and fact retention')
    ax.legend();ax.grid(alpha=.2)
    fig.text(.01,-.01,'Exploratory, 20 development images. Unresolved/modified remain in denominators. No causal inference.',fontsize=8)
    save(fig,'01_length_and_retention')
    fig,ax=plt.subplots(figsize=(6.6,4.4))
    selected=[r for r in rows if r['side']=='original' and r['type']=='attribute' and r['visual_label']=='supported' and not r['truth_conflict']]
    counts=Counter(r['removal_reason'] for r in selected if r['status']=='removed')
    ax.bar(['Entity absent','Attribute omitted'],[counts['entity_absent'],counts['attribute_omitted']],color=['#2563eb','#d97706'])
    ax.set(ylabel='Confirmed removed attributes (count)',title='Why judge-supported attributes disappear')
    for i,key in enumerate(('entity_absent','attribute_omitted')):ax.text(i,counts[key],str(counts[key]),ha='center',va='bottom')
    ax.set_ylim(0,max(1,max(counts.values(),default=0))*1.2)
    fig.text(.01,-.01,f'Original supported attributes: {len(selected)}; unresolved: {sum(r["status"]=="unresolved" for r in selected)}; truth conflicts excluded.',fontsize=8)
    save(fig,'02_attribute_removal_reasons')
    fig,axes=plt.subplots(1,2,figsize=(10,4.2))
    base=[r for r in rows if r['side']=='original' and r['visual_label']=='supported' and not r['truth_conflict']]
    pos=Counter(p for r in base for p in r['pos'])
    labels=[p for p,n in pos.most_common(8)]
    n=[pos[p] for p in labels];d=[sum(r['status']=='removed' and p in r['pos'] for r in base) for p in labels]
    axes[0].bar(labels,[a/b for a,b in zip(d,n)],color='#2563eb')
    for i,(a,b) in enumerate(zip(d,n)):axes[0].text(i,a/b,f'{a}/{b}',ha='center',va='bottom',fontsize=8)
    axes[0].set(title='Deletion by POS membership',ylabel='Removed / judge-supported',ylim=(0,1.08))
    axes[0].tick_params(axis='x',rotation=40)
    bins=[[] for _ in range(4)]
    for r in base:
        if r['positions']:bins[min(3,int(min(r['positions'])*4))].append(r)
    vals=[ratio(sum(r['status']=='removed' for r in b),len(b)) for b in bins]
    axes[1].bar(['0–25%','25–50%','50–75%','75–100%'],[v or 0 for v in vals],color='#d97706')
    for i,b in enumerate(bins):
        axes[1].text(i,vals[i] or 0,f'{sum(r["status"]=="removed" for r in b)}/{len(b)}' if b else 'N/A',ha='center',va='bottom',fontsize=8)
    axes[1].set(title='Deletion by first lexical position',xlabel='Relative position in original caption',ylim=(0,1.08))
    fig.text(.01,-.04,'A fact may belong to multiple POS classes. Positions use the first linked mention. Judge labels are not human truth.',fontsize=8)
    save(fig,'03_pos_and_position')


def main():
    for run in ('m2','m3_independent','m5_independent','end_to_end','orchestration'):check_frozen(ROOT/run)
    bpath=ROOT/'end_to_end/bundles.jsonl';qpath=ROOT/'end_to_end/m4/verification_queue.jsonl';vpath=ROOT/'end_to_end/verification.jsonl'
    source_files=[bpath,qpath,vpath,DATA/'selection.json',DATA/'decompose_cases.jsonl',DATA/'align_cases.jsonl',DATA/'verify_cases.jsonl']
    source_files += [ROOT/r/'results.jsonl' for r in ('m2','m3_independent','m5_independent')]
    out=new_run(ROOT/'analysis','post_run_analysis',source_files,{'llm_calls':0,'model_or_reference_changes':False},
                [__file__,Path('analysis_skeleton/m6_analysis.py'),Path('analysis_skeleton/metrics.py')])
    bundles=read_jsonl(bpath);queue=read_jsonl(qpath);vs=read_jsonl(vpath)
    raw_rows=[];pair_rows=[];pair_analysis=[]
    for b in bundles:
        q=[c for c in queue if c['pair_id']==b['pair_id']];ids={c['claim_id'] for c in q}
        r=analyze(b['original'],b['steer'],b['alignment'],q,[v for v in vs if v['claim_id'] in ids])
        pair_analysis.append({'pair_id':b['pair_id'],**r['metrics']})
        for f in r['facts']:
            source=next(x for x in b[f['side']]['facts'] if x['id']==f['fact_id'])
            raw_rows.append({'pair_id':b['pair_id'],**f,'value':source['value'],
                             'source_quotes':[s['quote'] for s in source['source_spans']]})
        lens={s:b['lexical'][s]['caption']['word_len'] for s in ('original','steer')}
        p={'pair_id':b['pair_id'],'original_words':lens['original'],'steer_words':lens['steer'],
           'word_change_pct':100*(lens['steer']-lens['original'])/lens['original']}
        for kind in ('entity','attribute'):
            stats=r['metrics'][kind]['true'];p[kind+'_supported_original']=stats['denominator']
            p[kind+'_retained_rate']=ratio(stats['retained'],stats['denominator'])
        pair_rows.append(p)
    write_jsonl(out/'fact_ledger.jsonl',raw_rows)
    write_csv(out/'fact_ledger.csv',list(raw_rows[0]),raw_rows)
    write_csv(out/'plot_pair_data.csv',list(pair_rows[0]),pair_rows)
    m2=read_jsonl(ROOT/'m2/results.jsonl');m3=read_jsonl(ROOT/'m3_independent/results.jsonl');m5=read_jsonl(ROOT/'m5_independent/results.jsonl')
    issue2=[{'case_id':r['case_id'],**i} for r in m2 for i in r['document']['issues']]
    issue3=[{'case_id':r['case_id'],**i} for r in m3 for i in r['alignment']['issues']]
    write_jsonl(out/'m2_validation_issues.jsonl',issue2);write_jsonl(out/'m3_validation_issues.jsonl',issue3)
    refs={c['case_id']:normalize_document(c['reference'],c['text'],c['case_id']) for c in read_jsonl(DATA/'decompose_cases.jsonl')}
    # Naming/mention disputes are review flags only; do not rescore the frozen baseline.
    naming=[]
    for r in m2:
        for p in r['score']['unmatched_prediction']:
            for g in r['score']['unmatched_reference']:
                if p['type']==g['type']=='entity' and overlap(p['source_spans'],g['source_spans']):
                    naming.append({'case_id':r['case_id'],'predicted':p['value'],'reference':g['value'],
                                   'note':'overlapping source, possible naming/granularity disagreement; not automatically equivalent'})
    write_jsonl(out/'m2_naming_review_flags.jsonl',naming)
    ref_align={c['case_id']:c for c in read_jsonl(DATA/'align_cases.jsonl')}
    target_rows=[]
    facts={(r['pair_id'],r['side'],r['fact_id']):r for r in raw_rows}
    maps={(b['pair_id'],s):fact_mapping(b[s],refs[b[s]['caption_id']]) for b in bundles for s in ('original','steer')}
    for c in read_jsonl(DATA/'verify_cases.jsonl'):
        pair=c['image_id'];side=c['source_caption_id'].rsplit('_',1)[1];fid=c['source_fact_id']
        reference_status=next(r['status'] for r in ref_align[pair]['reference']['alignments'] if fid in r[side])
        mapped=maps[(pair,side)].get(fid);actual=facts.get((pair,side,mapped),{})
        target_rows.append({'case_id':c['case_id'],'pair_id':pair,'side':side,'reference_fact_id':fid,
                            'statement':c['input']['statement'],'reference_label':c['reference_label'],
                            'reference_status':reference_status,'matched_prediction_fact_id':mapped,
                            'prediction_label':actual.get('visual_label'),'prediction_status':actual.get('status'),
                            'extraction_matched':mapped is not None,
                            'truth_agrees':actual.get('visual_label')==c['reference_label'],
                            'status_agrees':actual.get('status')==reference_status,
                            'both_agree':actual.get('visual_label')==c['reference_label'] and actual.get('status')==reference_status})
    write_csv(out/'fixed60_end_to_end_checks.csv',list(target_rows[0]),target_rows)
    vrefs={c['case_id']:c for c in read_jsonl(DATA/'verify_cases.jsonl')}
    disagreements=[{'case_id':r['case_id'],'input':vrefs[r['case_id']]['input'],
                    'reference_label':r['reference_label'],'reference_reason':vrefs[r['case_id']]['reference_reason'],
                    'prediction':r.get('prediction'),'reference_status':'unreviewed_candidate'} for r in m5 if r.get('prediction',{}).get('label')!=r['reference_label']]
    write_jsonl(out/'m5_disagreements.jsonl',disagreements)
    all_audits=[r['audit'] for rs in (m2,m3,m5) for r in rs]
    stage_audits=[]
    for d in sorted((ROOT/'end_to_end').glob('pair_*')):
        if not d.is_dir():continue
        for path in d.glob('m*.json'):
            if path.stem.endswith(('_started','_response')):continue
            r=read_json(path)
            if 'audit' in r:stage_audits.append(r['audit'])
    all_audits+=stage_audits
    original=[r for r in raw_rows if r['side']=='original']
    transitions=Counter((r['type'],r['status'],r['visual_label']) for r in original)
    e2e_issues=[{'pair_id':b['pair_id'],**i} for b in bundles for i in b['alignment']['issues']]
    write_jsonl(out/'m3_end_to_end_validation_issues.jsonl',e2e_issues)
    boot=bootstrap(pair_analysis,read_json(DATA/'selection.json')['selection'])
    write_json(out/'bootstrap.json',boot)
    stats={
        'images':len(bundles),'captions':len(bundles)*2,
        'word_counts':{'original':sum(p['original_words'] for p in pair_rows),'steer':sum(p['steer_words'] for p in pair_rows),
                       'mean_paired_percent_change':float(np.mean([p['word_change_pct'] for p in pair_rows])),
                       'all_pairs_shorter':all(p['steer_words']<p['original_words'] for p in pair_rows)},
        'm2':{'frozen_candidate_metrics':read_json(ROOT/'m2/metrics.json')['summary'],
              'captions_needing_review':sum(bool(r['document']['issues']) for r in m2),
              'validation_issue_count':len(issue2),'validation_reasons':dict(Counter(i['reason'] for i in issue2)),
              'overlapping_source_naming_flags':len(naming)},
        'm3_independent':{'joint':read_json(ROOT/'m3_independent/metrics.json')['joint'],
                          'pairs_needing_review':sum(bool(r['alignment']['issues']) for r in m3),
                          'validation_issue_count':len(issue3),
                          'technical_fact_count':sum(r['score']['technical_fact_count'] for r in m3),
                          'reference_fact_count':sum(r['score']['reference_fact_count'] for r in m3),
                          'by_status':{s:prf(**{k:sum(r['score']['by_status'][s][k] for r in m3) for k in ('tp','predicted','reference')}) for s in ('retained','removed','added','modified','unresolved')}},
        'm5_independent':read_json(ROOT/'m5_independent/metrics.json'),
        'm5_by_type':{k:score_labels([r for r in m5 if r['semantic_type']==k]) for k in ('entity','attribute')},
        'end_to_end':{'facts':len(raw_rows),'original_facts':len(original),'steer_facts':len(raw_rows)-len(original),
                       'unique_claims':len(queue),'verifications':len(vs),'labels':dict(Counter(v['label'] for v in vs)),
                       'm3_pairs_needing_review':sum(bool(b['alignment']['issues']) for b in bundles),
                       'm3_validation_issues':len(e2e_issues),
                       'truth_conflicts':sum(r['truth_conflict'] for r in raw_rows),
                       'original_transition_table':[{'type':k[0],'status':k[1],'label':k[2],'n':v} for k,v in sorted(transitions.items())]},
        'fixed60_partial_end_to_end_check':{'targets':len(target_rows),'extraction_matched':sum(r['extraction_matched'] for r in target_rows),
                     'truth_agrees':sum(r['truth_agrees'] for r in target_rows),'status_agrees':sum(r['status_agrees'] for r in target_rows),
                     'both_agree':sum(r['both_agree'] for r in target_rows),
                     'scope':'Preselected candidate target subset; missing extraction stays in denominator; not full E2E precision/F1.'},
        'usage':{'new_api_calls':sum(a.get('api_calls',0) for a in all_audits),
                 'end_to_end_api_calls':sum(a.get('api_calls',0) for a in stage_audits),
                 'end_to_end_reused_results':sum(bool(a.get('cache_hit')) for a in stage_audits),
                 'new_tokens':sum((a.get('usage') or {}).get('total_tokens',0) for a in all_audits),
                 'returned_models':sorted({a['response_model'] for a in all_audits if a.get('response_model')})},
        'bootstrap':boot,'human_gold':False,'independent_repeats':1,'causal_conclusions':False
    }
    report(out,'20图扩大测评：独立模块与真实端到端统计',stats,
           ['候选参考均在对应模型调用前编写；未根据输出更改答案。所有F1均是候选符合度，非独立人工准确率。',
            '程序/提示词/模型/few-shot保持基线；仅新增固定真实输入。技术问题保留，未自动修复或重试。',
            'M3独立测评使用固定参考事实；端到端M3使用实际M2输出，两者输入不同，分数不能直接当模块能力变化。',
            '60条视觉候选为按图预选的诊断命题，不是自然分布；端到端60目标检查不代表全链精确率。',
            '图像级区间只反映本开发样本的抽样变动，不能覆盖模型判断与候选参考误差；不支持steering因果结论。'])
    plots(out,raw_rows,pair_rows)


if __name__=='__main__':main()
