"""Readable image/input/reference/prediction disagreements, without changing any labels."""
from pathlib import Path
from analysis_skeleton.common import read_jsonl


def main():
    root=Path('outputs/skeleton_expansion20')
    rows=read_jsonl(root/'analysis/m5_disagreements.jsonl')
    text=['# M5视觉分歧审核：15条','','候选参考未经独立人工确认。请先仅依据下列实际图像与实际模型输入判断，再核对候选和预测；不要因为候选已经写好就默认其正确。所有原始标签保持不变。','']
    for r in rows:
        text += [f'## {r["case_id"]}','',f'![原始图像]({Path(r["input"]["image_path"]).resolve().as_posix()})','',
                 '**实际命题：** '+r['input']['statement'],'',
                 '**实际主体语境：** '+str(r['input'].get('entity_context',{})),'',
                 '**候选：** '+r['reference_label']+' — '+r['reference_reason'],'',
                 '**模型：** '+r['prediction']['label']+' — '+r['prediction']['reason'],'',
                 '待审核：主体是否唯一？候选是否借用了模型未收到的定位信息？图像证据足以肯定/否定，还是应保留uncertain？','']
    (root/'VISUAL_REVIEW.md').write_text('\n'.join(text),encoding='utf-8')


if __name__=='__main__':main()
