"""One bounded alignment call and one new visual review condition."""
import copy
from analysis_skeleton.common import sha, digest
from analysis_skeleton.framework_v2.runtime import SafeStage
from experiments.entity_attribute_v3.m3 import SimplifiedAlignStage, validate
from experiments.coco400_revision_v2.visual import ReviewStage

ALIGN_RULES = '''
Completeness pass before answering: enumerate every entity ID once in entities and every ATTRIBUTE fact ID once in attributes, including attributes of unresolved owners. An unresolved owner requires an explicit unresolved attribute row, not omission, addition or removal. Never put entity_e IDs into attributes.
Distinguish identity uncertainty from clearly distinct concepts. A house and a carriage, a wig and a hat, or a shoelace and a boot are not interchangeable entities just because both captions describe the same image. If each is absent as a concept from the opposite caption, represent separate original_only and steer_only rows; do not manufacture an ambiguous match merely because they occupy a similar role. Part/whole and genuine group/member ambiguity remain unresolved when texts point to overlapping referents. A disjunction such as 'table or shelf' is not evidence of two separate physical objects; if decomposition splits it, explicitly retain extraction/identity uncertainty.
For same-category unique scene participants, shared scene and role can establish a match even without identical wording. For multiple candidates use distinguishing anchors; never merge them to satisfy coverage. Do not choose a match based solely on preserving an attribute value.
All assertions of absence concern absence from the opposite TEXT, not the image. Opposite textual mentions missing from decomposition must remain extraction_gap with a literal quote. No images or visual verdicts are provided for alignment.
'''


class AlignStage(SimplifiedAlignStage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rules += '\n' + ALIGN_RULES
        self.identity.update(condition='complete_entity_attribute_mapping_v4', prompt_sha=digest(self.rules), v4_code_sha=sha(__file__))

    def messages(self, payload):
        clean=copy.deepcopy(payload)
        clean['required_ids']={s:{'entity_ids':[e['id'] for e in payload[s]['entities']],
            'attribute_fact_ids':[f['id'] for f in payload[s]['facts'] if f['type']=='attribute']}
            for s in ('original','steer')}
        return super().messages(clean)


VISUAL_RULES = '''
Task-specific sufficiency: assess whether a limitation actually prevents THIS proposition from being decided. A monochrome image can still establish object identity or shape; do not apply a color limitation to an entity claim. Visible diagnostic parts can identify a partially occluded object without seeing its entire body. Conversely a supporting surface alone does not establish a dining table, and liquid alone does not establish juice.
Caption source_status is a text-locator diagnostic, not a visual verdict. Use source text only to disambiguate the target; do not require all neighboring claims, actions, colors or counts to be true to establish an entity existence proposition. Preserve category-defining words in the requested entity name. For an attribute, identify the intended owner and judge the exact requested property.
Distinguish inspected absence from unresolvable evidence: after inspecting the full frame, use not_found with inspectable/none only when the relevant visible area is sufficiently clear and the claimed object is absent. If the only possible target is outside the frame, hidden, or visually indistinguishable, remain unresolved with the actual limitation. Never use uncertainty merely to avoid a justified negative, and never use a negative to remove legitimate uncertainty. A crop is a detail aid, not proof of identity or absence.
For size, state a visible comparison or category-specific visual cue only if it is present; do not invent scale. For ingredients, fine-grained categories and hidden materials, retain unresolved when appearance is insufficient. Return the exact demonstrated schema. This is a single new-condition review, not a vote or a request to reach a coverage target.
'''


class VisualStage(ReviewStage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for kind, stage in self.stages.items():
            source=stage.source
            old=source.messages
            def messages(payload, prior=old):
                result=prior(payload)
                result[0]['content']+='\n'+VISUAL_RULES
                return result
            source.messages=messages
            source.identity.update(v4_code_sha=sha(__file__), condition='proposition_specific_sufficiency_v4', new_condition_review=True)
            self.stages[kind]=SafeStage(source)
        self.identity.update(v4_code_sha=sha(__file__),condition='proposition_specific_sufficiency_v4',
            contracts={k:copy.deepcopy(v.identity) for k,v in self.stages.items()})
