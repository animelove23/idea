"""Real images visually inspected by assistant. Candidate labels, never human gold."""
from pathlib import Path
from .common import read_jsonl,write_jsonl,sha
from .llm import ROOT


def build():
    pairs={r['pair_id']:r for r in read_jsonl('outputs/skeleton_v1/m0_resolved/pairs.jsonl')}
    examples=[
        ('54627','entity','There is a horse in the image.','supported','Several horses are visible in the field.'),
        ('212603','entity','There is a dog in the image.','hallucinated','The visible animal is a cat, not a dog.'),
        ('3501','entity','There is a carrot in the stew.','uncertain','The small orange pieces cannot be confidently identified as carrot from this image.'),
        ('8775','attribute','The pillow near the left side of the bed has blue fabric.','supported','Blue fabric is visible on the pillow.'),
        ('3501','attribute','The bowl is black.','hallucinated','The bowl is light-colored, not black.'),
        ('275717','attribute','The tie has red fabric.','uncertain','This grayscale image does not establish the actual hue of the tie.')]
    cases=[
        ('337055','entity','There is a suitcase in the image.','supported'),
        ('337055','entity','There is a dog in the image.','hallucinated'),
        ('150639','entity','There is a passenger inside the car visible through the rear window.','uncertain'),
        ('360487','attribute','The vase is green.','supported'),
        ('360487','attribute','The flowers are blue.','hallucinated'),
        ('150639','attribute','The eyeglass frame is made of titanium.','uncertain')]
    def payload(i,statement):
        path=pairs[i]['image_path']
        if not Path(path).is_file():raise ValueError('Visual fixture image missing')
        return {'image_path':path,'image_sha256':sha(path),'statement':statement,'entity_context':{}}
    write_jsonl(ROOT/'shots/verify.jsonl',[{'example_id':f'v{n+1}','image_id':i,'semantic_type':kind,
                                         'reference_status':'assistant_visual_candidate','input':payload(i,s),
                                         'output':{'label':label,'reason':reason}}
                                        for n,(i,kind,s,label,reason) in enumerate(examples)])
    write_jsonl(ROOT/'fixtures/verify_cases.jsonl',[{'case_id':f'visual_{n+1}','image_id':i,'semantic_type':kind,
                                                  'input':payload(i,s),'reference_label':label,
                                                  'reference_status':'assistant_visual_candidate','split':'visual_development'}
                                                 for n,(i,kind,s,label) in enumerate(cases)])


if __name__=='__main__':build()
