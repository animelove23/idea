"""Prompt-only identity counterevidence intervention after the first probe failure."""
import argparse
from pathlib import Path
from analysis_skeleton.common import digest,sha
from .alignment import AlignStage
from . import run

COUNTEREVIDENCE='''
Mandatory identity counterevidence check BEFORE matching: compare explicit spatial anchors and distinguishing roles in both descriptions. A single mentioned subject plus a hypernym relationship is NOT sufficient. In particular, a bird by the LEFT door and an animal by the RIGHT door have conflicting location evidence: keep identity unresolved, even though bird is an animal. Do not discard opposite left/right, front/back or incompatible distinguishing anchors just to obtain a match. The same applies to different explicitly identified agents or owners. Only classify generalized/specialized AFTER identity has positive contextual support without such unresolved conflicts. State the specific positive anchors and any conflicting anchors in reason. In the hypernym_without_identity demonstration, the outcome is unresolved; apply that boundary to unseen categories as well.
'''


class GuardStage(AlignStage):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.rules+='\n'+COUNTEREVIDENCE
        self.identity.update(prompt_sha=digest(self.rules),identity_counterevidence_code_sha=sha(__file__))


if __name__=='__main__':
    run.ROOT=Path('outputs/coco400_revision_v2_guard');run.AlignStage=GuardStage
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','probe','align','review','B','C']);p.add_argument('--resume',action='store_true');a=p.parse_args()
    if a.action=='prepare':run.prepare()
    elif a.action in ('probe','align','review'):run.run_calls(a.action,a.resume)
    else:run.rebuild(a.action=='C')
