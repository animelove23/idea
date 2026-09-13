"""Only complete example input context; no new images, statements or answers."""
import copy
from analysis_skeleton.common import read_jsonl,sha
from analysis_skeleton.m5_verify import VisualStage

NAMES={'v1':'horse','v2':'dog','v3':'carrot','v4':'pillow','v5':'bowl','v6':'tie'}
ROLE='Caption context for locating the referent only, not evidence that the statement is visually true.'

def with_context(shots):
    result=copy.deepcopy(shots)
    for row in result:
        name=NAMES[row['example_id']];text=row['input']['statement'];start=text.lower().index(name)
        quote=text[start:start+len(name)]
        row['input']['entity_context']={'name':name,'source_mentions':[quote],'source_window':text,
              'target_mention':{'quote':quote,'start':start,'end':start+len(quote)},'context_role':ROLE}
    return result

class ContextShotStage(VisualStage):
    def __init__(self,shots_path,config_path='decomposition/api_config.local.json',transport=None):
        super().__init__(config_path,transport=transport)
        rows=read_jsonl(shots_path)
        if rows!=with_context(self.shots):raise ValueError('only_context_fields_may_change')
        self.shots=rows;self.shots_path=shots_path
        self.identity={**self.identity,'shots_sha':sha(shots_path)}
