"""Reviewed v1.3 demonstration labels; historical v1.2 examples stay unchanged."""
import copy
import json
from pathlib import Path

from decomposition.storage import write_jsonl
from .alignment import align_entities
from .alignment_core import align_core
from .build_examples import document, entities, bindings, row
from .common import document_context, require


def build():
    path = Path('evaluation/examples/alignment.jsonl')
    cases = [json.loads(l) for l in path.read_text(encoding='utf-8').splitlines()]
    for case in cases:
        rows = case['output']['fact_alignment']
        for r in rows:
            if r['status'] == 'ambiguous': r['status'] = 'other'
        if case['id'] == 'roles_and_order':
            for r in rows:
                if r['status'] == 'other': r.update(status='modified', reason='value_changed')
            for side in ('original', 'steer'):
                for b in case['output'][side + '_bindings']:
                    if b['slot'] in {'holds', 'carries'}: b['slot'] = 'object_handling'
        if case['id'] == 'uncertain_child':
            rows[:] = [r for r in rows if r['original_fact_ids'] != ['f5', 'f6']]
            rows.extend([row([5], [], 'removed'), row([6], [], 'removed'), row([], [2], 'added')])
        if case['id'] == 'one_sided_and_conjoined_speculation':
            # New synthetic phase example, unrelated to any real test caption.
            a = document('A pianist prepares to play a piano.', [
                ('human', 'A pianist is present.', 'A pianist'),
                ('object', 'A piano is present.', 'a piano'),
                ('action', 'The pianist prepares to play the piano.', 'A pianist prepares to play a piano')])
            b = document('A pianist is playing a piano.', [
                ('human', 'A pianist is present.', 'A pianist'),
                ('object', 'A piano is present.', 'a piano'),
                ('action', 'The pianist plays the piano.', 'A pianist is playing a piano')])
            es = [('A pianist', [1, 3], 'pianist associated with the sole piano'), ('a piano', [2, 3], 'piano played by pianist')]
            ent = {'original_entities': entities('o', es), 'steer_entities': entities('s', es),
                   'entity_alignment': [{'original_entity_ids': [f'o{i}'], 'steer_entity_ids': [f's{i}'],
                                         'status': 'matched', 'reason': 'Unique corresponding performer/instrument context.'} for i in (1, 2)]}
            sidecar = align_entities(ent, a, b)
            bs = [([1], 'existence'), ([2], 'existence'), ([1, 2], 'play_music')]
            case.clear()
            case.update(id='pianist_event_phase', input={'original': document_context(a), 'steer': document_context(b), 'entity_sidecar': sidecar},
                        output={'original_bindings': bindings('o', bs), 'steer_bindings': bindings('s', bs),
                                'fact_alignment': [row([1], [1]), row([2], [2]), row([3], [3], 'modified')]})
        parsed = align_core(case['output'], case['input']['original'], case['input']['steer'], case['input']['entity_sidecar'])
        require(parsed['status'] == 'ready', str(parsed))
        require([r['status'] for r in parsed['fact_alignment']].count('modified') ==
                [r['status'] for r in case['output']['fact_alignment']].count('modified'), 'modified demo downgraded')
    return cases


if __name__ == '__main__':
    write_jsonl(Path('evaluation/examples/alignment_core.jsonl'), build())
    print('8 validated v1.3 alignment demonstrations; legacy examples unchanged.')
