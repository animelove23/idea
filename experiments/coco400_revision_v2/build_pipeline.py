"""Create the new entry point from the unchanged first-pass pipeline, with explicit substitutions."""
from pathlib import Path

source=Path('analysis_skeleton/final_v1/pipeline.py').read_text(encoding='utf-8')
source=source[:source.index('\nif __name__')]
for name in ('decompose','visual','context','statistics','routing'):
    source=source.replace('from .'+name+' import','from analysis_skeleton.final_v1.'+name+' import')
source=source.replace('from analysis_skeleton.framework_v2.contracts import validate_alignment',
    'from .local_alignment import validate_local as validate_alignment\nfrom .guard import GuardStage')
source=source.replace("SafeStage(FewShotStage('align',config,model=MODEL))",'SafeStage(GuardStage(config))')
source=source.replace("Path(__file__).parent/'decompose_rules.txt',Path(__file__).parent/'visual_rules.txt'",
    "ROOT/'final_v1/decompose_rules.txt',ROOT/'final_v1/visual_rules.txt',Path(__file__).parent/'align.txt',Path(__file__).parent/'align_shots.jsonl'")
source=source.replace("out,'final_v1_pipeline'","out,'revision_v2_first_pass_pipeline'")
target=Path(__file__).with_name('pipeline.py')
assert not target.exists()
target.write_text(source,encoding='utf-8')
