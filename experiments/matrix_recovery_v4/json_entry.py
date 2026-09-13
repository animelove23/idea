"""Explicit JSON format requirement; failed v4 preflight is preserved unchanged."""
import argparse
from pathlib import Path
from analysis_skeleton.common import digest,sha
from . import run
from .stages import AlignStage as BaseAlignStage


class AlignStage(BaseAlignStage):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self.rules+='\nReturn one valid JSON object only, without Markdown fences.\n'
        self.identity.update(prompt_sha=digest(self.rules),json_format_entry_sha=sha(__file__))


def configure():
    run.ROOT=Path('outputs/matrix_recovery_v4_json')
    run.AlignStage=AlignStage


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','probe','align','visual','B','C','report']);p.add_argument('--resume',action='store_true');a=p.parse_args()
    configure()
    if a.action=='prepare':run.prepare()
    elif a.action in ('probe','align','visual'):run.calls(a.action,a.resume)
    elif a.action=='B':run.align_result()
    elif a.action=='C':run.visual_result()
    else:run.report()
