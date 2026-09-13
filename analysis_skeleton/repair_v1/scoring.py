"""Fixed comparison scorer: name lemma only, no new semantic synonym guesses."""
from functools import lru_cache
from analysis_skeleton.metrics import normal
from analysis_skeleton.expansion20.scorer_sensitivity import score
from analysis_skeleton.m1_lexical import LexicalRecorder


class LemmaScorer:
    def __init__(self,parser=None):self.parser=parser or LexicalRecorder()
    @lru_cache(maxsize=512)
    def name(self,value):
        return ' '.join(t.lemma_.casefold() for t in self.parser.nlp(normal(value)) if not t.is_space and not t.is_punct)
    def score(self,pred,ref):return score(pred,ref,self.name)
