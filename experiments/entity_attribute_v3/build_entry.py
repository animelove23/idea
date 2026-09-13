"""Mechanical fork of the frozen entry; never modifies the frozen source."""
from pathlib import Path
ROOT=Path(__file__).parent
SOURCE=ROOT.parent/'coco400_revision_v2'

def build():
    target=ROOT/'pipeline.py'
    if target.exists():raise ValueError('generated_entry_already_exists')
    s=(SOURCE/'pipeline.py').read_text(encoding='utf-8')
    s=s.replace('from .local_alignment import validate_local as validate_alignment','from experiments.coco400_revision_v2.local_alignment import validate_local as baseline_align\nfrom .m3 import SimplifiedAlignStage,validate as simple_align\nfrom .m2 import NounCenteredStage\nV2_ROOT=Path(__file__).parent.parent/"coco400_revision_v2"')
    s=s.replace('from .guard import GuardStage','from experiments.coco400_revision_v2.guard import GuardStage')
    s=s.replace('def make_stages(profile,config):','def make_stages(profile,config,variant):')
    s=s.replace("decompose=(FinalDecomposeStage(config) if profile['decompose_candidate']=='owner'", "decompose=(NounCenteredStage(config) if variant in {'m2_only','combined'} else FinalDecomposeStage(config) if profile['decompose_candidate']=='owner'")
    s=s.replace("'align':SafeStage(GuardStage(config)),","'align':SafeStage(SimplifiedAlignStage(config) if variant in {'m3_only','combined'} else GuardStage(config)),")
    s=s.replace("replicate_id='r1',stages=None,parser=None,profile=None):","replicate_id='r1',stages=None,parser=None,profile=None,variant='m2_only'):")
    s=s.replace("    if cache_mode!='fresh' or cache_path:","    if variant not in {'baseline','m2_only','m3_only','combined'}:raise ValueError('unknown_variant')\n    validate_alignment=simple_align if variant in {'m3_only','combined'} else baseline_align\n    if cache_mode!='fresh' or cache_path:")
    s=s.replace('stages=make_stages(profile,config)','stages=make_stages(profile,config,variant)')
    s=s.replace("Path(__file__).parent/'align.txt',Path(__file__).parent/'align_shots.jsonl'","V2_ROOT/'align.txt',V2_ROOT/'align_shots.jsonl'")
    s=s.replace("    code=[*Path(__file__).parent.glob('*.py'),", "    files += list(Path(__file__).parent.glob('*.txt'))+list(Path(__file__).parent.glob('*.jsonl'))\n    code=[*Path(__file__).parent.glob('*.py'),*V2_ROOT.glob('*.py'),*(ROOT/'final_v1').glob('*.py'),")
    s=s.replace("identity={'profile':profile,", "identity={'variant':variant,'profile':profile,")
    s=s.replace("'revision_v2_first_pass_pipeline'","'entity_attribute_v3_first_pass_pipeline'")
    # This module is the library entry; end_to_end.py is the sole public CLI.
    s=s.split("if __name__=='__main__':")[0]
    target.write_text(s,encoding='utf-8')
    s=(SOURCE/'end_to_end.py').read_text(encoding='utf-8')
    s=s.replace('from .visual import ReviewStage,validate_typed,merge','from experiments.coco400_revision_v2.visual import ReviewStage,validate_typed,merge')
    s=s.replace('from .observation import analyze_pair','from experiments.coco400_revision_v2.observation import analyze_pair\nfrom .retention import analyze as retention_analysis')
    s=s.replace('stages=None,review_stage=None,workers=8,parser=None):',"stages=None,review_stage=None,workers=8,parser=None,variant='m2_only',config='decomposition/api_config.local.json'):")
    s=s.replace("    out=Path(output);out.mkdir(parents=True,exist_ok=True)","    profile=read_json(profile) if isinstance(profile,(str,Path)) else copy.deepcopy(profile)\n    if profile.get('visual_candidate')!='typed':raise ValueError('v3_requires_explicit_typed_visual_profile')\n    routes=profile['visual_shots_path']\n    out=Path(output);out.mkdir(parents=True,exist_ok=True)")
    s=s.replace("condition_id='revision_v2_fresh_pairs',replicate_id='r1')","condition_id='entity_attribute_v3_'+variant,replicate_id='r1',variant=variant,config=config)")
    s=s.replace("ReviewStage('outputs/final_v1_release/visual_routes.json')","ReviewStage(routes,config_path=config)")
    s=s.replace("routing_inputs('outputs/final_v1_release/visual_routes.json')","routing_inputs(routes)")
    s=s.replace("    write_json(out/'summary.json',summary);return summary", "    retention,attribute_rows,pair_rates,entity_rows=retention_analysis(records)\n    write_json(out/'retention.json',retention);write_jsonl(out/'conditional_attribute_denominator.jsonl',attribute_rows)\n    write_jsonl(out/'entity_retention_denominator.jsonl',entity_rows);write_jsonl(out/'retention_by_pair.jsonl',pair_rates)\n    summary['variant']=variant;write_json(out/'summary.json',summary);return summary")
    s=s.split("if __name__=='__main__':")[0]+'''if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pairs',required=True);p.add_argument('--output',required=True)
    p.add_argument('--profile',default='outputs/final_v1_release/profile.json');p.add_argument('--resume',action='store_true')
    p.add_argument('--variant',choices=['baseline','m2_only','m3_only','combined'],default='m2_only')
    p.add_argument('--config',default='decomposition/api_config.local.json');a=p.parse_args()
    print(json.dumps(run_full(a.pairs,a.output,a.profile,a.resume,variant=a.variant,config=a.config),ensure_ascii=False))
'''
    (ROOT/'end_to_end.py').write_text(s,encoding='utf-8')
    print('created isolated configurable entries')

if __name__=='__main__':build()
