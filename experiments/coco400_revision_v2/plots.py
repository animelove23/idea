"""Reuse presentation utilities, not old classification logic."""
import csv
from collections import Counter
from pathlib import Path
from analysis_skeleton.common import read_jsonl
from experiments.coco400_v1 import summarize as presentation

root=Path('outputs/coco400_revision_v2_guard/C_reviewed')
(root/'observations').mkdir(exist_ok=True)
records=read_jsonl(root/'pairs.jsonl');rows=[r['observation'] for r in records]
with (root/'matrix.csv').open(encoding='utf-8-sig') as stream:
    matrix=[{'length_group':r['length_group'],'hallucination_change':r['H'],'supported_change':r['S'],'count':int(r['count'])} for r in csv.DictReader(stream)]
summary={'length_counts':dict(Counter(r['length_group'] for r in rows)),
    'matrix_unresolved_by_length':{g:sum(r['length_group']==g and not r['matrix_classifiable'] for r in rows) for g in ('shorter','unchanged','longer')},
    'component_totals':{}}
for kind in ('entity','attribute'):
    for label in ('S','H'):
        cc=[c for r in rows for c in r['components'] if c['type']==kind and c['role']==label]
        summary['component_totals'][kind+'_'+label]={k:sum(c[k] for c in cc) for k in ('original_count','removed','modified_out','retained')}
presentation.ROOT=root
from matplotlib.figure import Figure
original_suptitle=Figure.suptitle
def candidate_title(self,text,*args,**kwargs):
    return original_suptitle(self,text.replace('Frozen Final v1','Revision candidate'),*args,**kwargs)
Figure.suptitle=candidate_title
presentation.figures(rows,matrix,summary)
presentation.gallery(rows,[e for r in records for e in r['events']],{p['pair_id']:p for p in read_jsonl('outputs/coco400_final_v1/pairs.jsonl')})
path=root/'observations/case_gallery.html'
path.write_text(path.read_text(encoding='utf-8').replace('frozen-framework observation audit','revision candidate observation audit'),encoding='utf-8')
