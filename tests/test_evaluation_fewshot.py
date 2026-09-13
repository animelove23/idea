import copy
import json
import unittest
from pathlib import Path
from decomposition.config import APIConfig
from evaluation.build_examples import build
from evaluation.common import JsonStage


class FewShotTests(unittest.TestCase):
    def test_synthetic_examples_pass_existing_contracts(self):
        cases=build()
        self.assertEqual(len(cases),8)
        for stage in ['coverage','entities','alignment']:
            saved=[json.loads(x) for x in Path(f'evaluation/examples/{stage}.jsonl').read_text(encoding='utf-8').splitlines()]
            self.assertEqual(saved,[dict(id=c['id'],**c[stage]) for c in cases])

    def test_no_real_test_caption_in_examples(self):
        real=[json.loads(x) for x in Path('outputs/downstream_v1/pairs.jsonl').read_text(encoding='utf-8').splitlines()]
        test={p[s]['text'].lower().strip() for p in real for s in ['original','steer']}
        synthetic={c[s]['text'].lower().strip() for c in build() for s in ['original','steer']}
        self.assertEqual(len(synthetic),16)
        self.assertFalse(test & synthetic)

    def test_zero_and_eight_differ_only_in_examples_not_system_or_final_input(self):
        sent=[]
        def transport(body):
            sent.append(copy.deepcopy(body))
            return {'choices':[{'finish_reason':'stop','message':{'content':'{}'}}]}
        config=APIConfig('test','not-sent')
        examples=[c['coverage'] for c in build()]
        payload={'text':'Unseen input.','facts':[]}
        JsonStage(config,transport).run('coverage',payload)
        _,audit=JsonStage(config,transport,{'coverage':examples}).run('coverage',payload)
        a,b=sent
        self.assertEqual(len(a['messages']),2)
        self.assertEqual(len(b['messages']),18)
        self.assertEqual(a['messages'][0],b['messages'][0])
        self.assertEqual(a['messages'][-1],b['messages'][-1])
        self.assertEqual(audit['request'],b)
        self.assertEqual({k:v for k,v in a.items() if k!='messages'},{k:v for k,v in b.items() if k!='messages'})


if __name__=='__main__': unittest.main()
