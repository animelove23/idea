"""One-call eight-shot M2 candidate; normalization is identical to Final v1."""
from pathlib import Path
from analysis_skeleton.common import digest,sha,read_jsonl
from analysis_skeleton.final_v1.decompose import FinalDecomposeStage,normalize_final

ROOT=Path(__file__).parent

class NounCenteredStage(FinalDecomposeStage):
    def __init__(self,config_path='decomposition/api_config.local.json',transport=None):
        super().__init__(config_path,transport)
        self.rules+='\n\n'+(ROOT/'m2_rules.txt').read_text(encoding='utf-8')
        self.shots=read_jsonl(ROOT/'m2_shots.jsonl')
        if len(self.shots)!=8:raise ValueError('exactly_eight_shots_required')
        for ex in self.shots:
            if normalize_final(ex['output'],ex['input']['text'])['issues']:
                raise ValueError('invalid_noun_centered_demonstration')
        self.identity.update(condition='noun_centered_v3_prompt_and_shots',prompt_sha=digest(self.rules),
                             shots_sha=digest(self.shots),candidate_code_sha=sha(__file__),
                             normalization='unchanged_final_v1',calls_per_caption=1)
