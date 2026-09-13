"""Isolated deterministic before/after evaluation on identical saved responses."""
import json
from pathlib import Path
from analysis_skeleton.common import read_jsonl,new_run,write_jsonl,report,check_frozen
from analysis_skeleton.contracts import normalize_document as baseline_normalize
from analysis_skeleton.metrics import aggregate_documents,score_documents,prf
from analysis_skeleton.m3_align import score_alignment,validate_alignment as baseline_align
from .contracts import normalize_document
from .alignment import validate_alignment
from .scoring import LemmaScorer

BASE=Path('outputs/skeleton_expansion20')
OUT=Path('outputs/skeleton_repair_v1')
DATA=Path('analysis_skeleton/fixtures/expansion20')


def main():
    scorer=LemmaScorer()
    check_frozen(BASE/'m2')
    out=new_run(OUT/'m2_replay','M2_mention_repair',[BASE/'m2/results.jsonl',DATA/'decompose_cases.jsonl'],
                {'only_model_processing_change':'invalid mention isolation','primary_scorer':'lemma names fixed on both conditions','new_api_calls':0},
                [__file__,Path(__file__).with_name('contracts.py'),Path(__file__).with_name('scoring.py')])
    refs={c['case_id']:baseline_normalize(c['reference'],c['text'],c['case_id']) for c in read_jsonl(DATA/'decompose_cases.jsonl')}
    rows=[]
    for r in read_jsonl(BASE/'m2/results.jsonl'):
        raw=json.loads(r['audit']['raw_content']);before=r['document']
        after=normalize_document(raw,before['text'],before['caption_id'])
        rows.append({'case_id':r['case_id'],'document':after,'source_run':str(BASE/'m2'),
                     'before_lemma':scorer.score(before,refs[r['case_id']]),'after_lemma':scorer.score(after,refs[r['case_id']]),
                     'before_legacy':score_documents(before,refs[r['case_id']]),'after_legacy':score_documents(after,refs[r['case_id']]),
                     'restored_facts':[f for f in after['facts'] if f['id'] not in {x['id'] for x in before['facts']}]})
    write_jsonl(out/'results.jsonl',rows)
    report(out,'M2坏提及局部隔离：固定响应重放',{'before':aggregate_documents([r['before_lemma'] for r in rows]),
        'after':aggregate_documents([r['after_lemma'] for r in rows]),
        'restored_facts':sum(len(r['restored_facts']) for r in rows),
        'captions_with_recovered_mentions':sum(bool(r['document']['source_audit']) for r in rows),
        'new_api_calls':0},['主比较两边固定同一词形计分器；仅改变提及校验粒度。',
        '保留错误原文及隔离日志，不猜引文、不改变state边界；不是独立模型重复。'])
    check_frozen(BASE/'m3_independent')
    out=new_run(OUT/'m3_replay','M3_format_repair',[BASE/'m3_independent/results.jsonl',DATA/'align_cases.jsonl'],
                {'only_change':'lossless format canonicalization','new_api_calls':0},
                [__file__,Path(__file__).with_name('alignment.py')])
    cases={c['case_id']:c for c in read_jsonl(DATA/'align_cases.jsonl')};rows=[]
    for r in read_jsonl(BASE/'m3_independent/results.jsonl'):
        c=cases[r['case_id']];raw=json.loads(r['audit']['raw_content'])
        after=validate_alignment(raw,c['original'],c['steer'])
        rows.append({'case_id':r['case_id'],'alignment':after,'before':r['score'],'after':score_alignment(after,c['reference'])})
    write_jsonl(out/'results.jsonl',rows)
    def aggregate(condition):
        return {'joint':prf(**{k:sum(r[condition]['joint'][k] for r in rows) for k in ('tp','predicted','reference')}),
                'technical_facts':sum(r[condition]['technical_fact_count'] for r in rows)}
    report(out,'M3格式规范化：固定事实与固定响应重放',
           {'before':aggregate('before'),'after':aggregate('after'),'new_api_calls':0,
            'rows_with_canonicalization':sum(bool(r['alignment']['format_audit']) for r in rows)},
           ['只拆开已声明的单侧新增/删除批量行，合并相交的纯unresolved集合；不推断任何确定实体匹配。',
            '冲突、非法ID、跨槽/不同主体仍走原隔离器。参考答案和输入事实不变。'])


if __name__=='__main__':main()
