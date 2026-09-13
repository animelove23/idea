"""Deterministic visual locator: exact source sentences and marked mention offsets; no LLM."""
import copy
from functools import lru_cache
from analysis_skeleton.m1_lexical import LexicalRecorder
from analysis_skeleton.m4_queue import build_queue as baseline_queue


class SourceLocator:
    def __init__(self,parser=None):
        self.parser=parser or LexicalRecorder()
        self.identity={'version':'source_window_v1','previous_sentences':1,'nlp':self.parser.identity}
    @lru_cache(maxsize=256)
    def sentences(self,text):
        return [(s.start_char,s.end_char) for s in self.parser.nlp(text).sents]
    def context(self,doc,entity,existing):
        result=copy.deepcopy(existing)
        if not entity['mentions']:return result
        mention=min(entity['mentions'],key=lambda m:m['start'])
        sentences=self.sentences(doc['text'])
        for i,(start,end) in enumerate(sentences):
            if start<=mention['start']<end:
                start=sentences[max(0,i-1)][0]
                # Span may cross sentences; retain the complete exact mention.
                end=max(end,mention['end'])
                text=doc['text'][start:end]
                result.update(source_window=text,
                              target_mention={'quote':mention['quote'],'start':mention['start']-start,'end':mention['end']-start},
                              context_role='Caption context for locating the referent only, not evidence that the statement is visually true.')
                assert text[result['target_mention']['start']:result['target_mention']['end']]==mention['quote']
                return result
        raise ValueError('Mention is outside source sentences')
    def enrich(self,claim,docs):
        claim=copy.deepcopy(claim);first=claim['refs'][0];doc=docs[first['side']]
        fact=next(f for f in doc['facts'] if f['id']==first['fact_id'])
        entity=next(e for e in doc['entities'] if e['id']==fact['entity_id'])
        claim['entity_context']=self.context(doc,entity,claim['entity_context'])
        return claim


def build_queue(pair_id,original,steer,alignment,image_path,image_sha256=None,lexical=None,locator=None):
    queue=baseline_queue(pair_id,original,steer,alignment,image_path,image_sha256,lexical)
    locator=locator or SourceLocator()
    return [locator.enrich(q,{'original':original,'steer':steer}) for q in queue]
