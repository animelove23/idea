"""Bound scene inventory size and prohibit redundant region enumeration."""
import json
from analysis_skeleton.common import digest,sha
from .stage import JointStage
from .search_binding import validate

class BoundedStage(JointStage):
    def __init__(self,transport=None):
        super().__init__(transport)
        self.rules+='\nREGION BUDGET: create no more regions than the provided region_budget. Reuse one region for identical visible referents; never enumerate repeated descriptions of the same room, background or crowd. Unrelated scene inventory is forbidden. Keep each visible_cues to at most one short sentence. After listing the necessary bounded regions, output all requested claim rows exactly once.'
        self.identity.update(condition='joint_region_graph_with_inventory_budget',prompt_sha=digest(self.rules),bounded_code_sha=sha(__file__))
    def user(self,payload):
        out=super().user(payload);data=json.loads(out['content'][0]['text']);data['region_budget']=len(payload['claims'])
        out['content'][0]['text']=json.dumps(data,ensure_ascii=False);return out

def compile_bounded(raw,payload):
    if isinstance(raw,dict) and isinstance(raw.get('regions'),list) and len(raw['regions'])>len(payload['claims']):raise ValueError('region_budget_exceeded')
    return validate(raw,payload)
