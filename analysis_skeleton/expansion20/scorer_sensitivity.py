"""Post-hoc scorer diagnosis: entity-name lemmatization only; baseline outputs untouched."""
from functools import lru_cache
from pathlib import Path
from analysis_skeleton.common import read_jsonl,new_run,report,write_jsonl,check_frozen
from analysis_skeleton.contracts import normalize_document
from analysis_skeleton.metrics import normal,overlap,matching,prf,aggregate_documents
from analysis_skeleton.m1_lexical import LexicalRecorder


def score(pred,ref,name_normal):
    em=matching(pred['entities'],ref['entities'],lambda a,b:name_normal(a['name'])==name_normal(b['name']) and overlap(a['mentions'],b['mentions']))
    entity_map={pred['entities'][i]['id']:ref['entities'][j]['id'] for i,j in em}
    def same(a,b):
        values=name_normal(a['value'])==name_normal(b['value']) if a['type']==b['type']=='entity' else normal(a['value'])==normal(b['value'])
        return a['type']==b['type'] and a['slot']==b['slot'] and values and entity_map.get(a['entity_id'])==b['entity_id']
    pairs=matching(pred['facts'],ref['facts'],same)
    return {'joint':prf(len(pairs),len(pred['facts']),len(ref['facts'])),
            'by_type':{k:prf(sum(pred['facts'][i]['type']==k for i,j in pairs),
                               sum(f['type']==k for f in pred['facts']),sum(f['type']==k for f in ref['facts'])) for k in ('entity','attribute')}}


def main():
    root=Path('outputs/skeleton_expansion20');check_frozen(root/'m2')
    cases=Path('analysis_skeleton/fixtures/expansion20/decompose_cases.jsonl')
    parser=LexicalRecorder()
    @lru_cache(None)
    def lemmatize(name):
        return ' '.join(t.lemma_.casefold() for t in parser.nlp(normal(name)) if not t.is_punct and not t.is_space)
    out=new_run(root/'scorer_sensitivity','post_hoc_scorer_sensitivity',[cases,root/'m2/results.jsonl'],
                {'only_change':'entity names and entity-existence values normalized with fixed spaCy lemma',
                 'nlp':parser.identity,'post_hoc':True,'llm_calls':0,'not_primary_score':True},[__file__,Path('analysis_skeleton/metrics.py')])
    refs={c['case_id']:normalize_document(c['reference'],c['text'],c['case_id']) for c in read_jsonl(cases)}
    rows=[]
    for r in read_jsonl(root/'m2/results.jsonl'):
        # This path must exactly reproduce original metrics when normal is unchanged.
        base=score(r['document'],refs[r['case_id']],normal)
        assert base['joint']==r['score']['joint'] and base['by_type']==r['score']['by_type']
        rows.append({'case_id':r['case_id'],'baseline':base,'lemma_entity_names':score(r['document'],refs[r['case_id']],lemmatize)})
    write_jsonl(out/'per_caption.jsonl',rows)
    report(out,'M2实体词形还原的计分敏感性检查',
           {'baseline':aggregate_documents([r['baseline'] for r in rows]),
            'lemma_entity_names':aggregate_documents([r['lemma_entity_names'] for r in rows]),
            'primary_run_unchanged':True,'llm_calls':0,'post_hoc':True},
           ['只改变实体名称/存在事实值的词形规范化；来源重叠、一对一匹配、属性值、主体绑定规则保持不变。',
            '该诊断用于揭示计分器敏感性，不作为模型改进、不替换原F1、不将新增匹配自动视为人工确认正确。',
            '群体/个体拆分、部分与整体、train/model train等语义范围仍未解决；需独立审核。'])


if __name__=='__main__':main()
