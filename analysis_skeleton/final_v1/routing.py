"""Fixed, post-evaluation M5 type routing; one call and no prediction selection."""
import copy
from pathlib import Path

from analysis_skeleton.common import read_json, read_jsonl, sha
from analysis_skeleton.evidence_verifier_v1.compiler import compile_evidence
from analysis_skeleton.evidence_verifier_v2.experiment import FlashStage
from analysis_skeleton.framework_v2.runtime import SafeStage
from analysis_skeleton.llm import CallFailure
from .visual import FinalVisualStage, validate as validate_proposition


ROUTES = {'entity': 'context', 'attribute': 'proposition'}
MODEL = 'deepseek-flash'


def read_routing_manifest(path):
    routes = read_json(path)
    if not isinstance(routes, dict) or set(routes) != set(ROUTES):
        raise ValueError('typed_visual_requires_entity_and_attribute_shot_paths')
    for value in routes.values():
        if not isinstance(value, str) or not value or not Path(value).is_file():
            raise ValueError('typed_visual_shots_path_must_exist')
    return routes


def routing_inputs(path):
    """Files frozen by the caller: manifest, both shots, every actual shot image."""
    routes = read_routing_manifest(path)
    files = [Path(path), *[Path(routes[kind]) for kind in ROUTES]]
    for kind in ROUTES:
        files.extend(Path(row['input']['image_path']) for row in read_jsonl(routes[kind]))
    return files


def contract_for(claim_type):
    if not isinstance(claim_type, str) or claim_type not in ROUTES:
        raise ValueError('typed_visual_unknown_claim_type')
    return ROUTES[claim_type]


def validate_typed(raw, claim_type):
    contract = contract_for(claim_type)
    return (compile_evidence if contract == 'context' else validate_proposition)(raw, claim_type)


class TypedVisualStage:
    stage = 'verify'

    def __init__(self, manifest_path, config_path='decomposition/api_config.local.json', transport=None):
        routes = read_routing_manifest(manifest_path)
        self.stages = {
            'entity': SafeStage(FlashStage(routes['entity'], 'sufficiency', config_path, transport=transport)),
            'attribute': SafeStage(FinalVisualStage(routes['attribute'], config_path, transport=transport)),
        }
        self.identity = {
            'model': MODEL, 'explicit_model': MODEL,
            'evidence_contract': 'final_v1_fixed_type_router',
            'routes': copy.deepcopy(ROUTES),
            'route_selection': 'fixed_by_input_claim_type_not_prediction_or_reference',
            'selection_status': 'post_evaluation_combination_not_independent_holdout',
            'router_code_sha': sha(__file__), 'routing_manifest_sha': sha(manifest_path),
            'shots_sha': {kind: sha(path) for kind, path in routes.items()},
            'contracts': {kind: copy.deepcopy(stage.identity) for kind, stage in self.stages.items()},
            'transport_timeouts': {kind: stage.source.config.timeout for kind, stage in self.stages.items()},
            'calls_per_claim': 1,
        }

    def _audit(self, audit, kind):
        result = copy.deepcopy(audit)
        # Keep identity from the actual model contract. The router identity is
        # separate so replay/audit cannot silently call this a third prompt.
        result['router_identity'] = copy.deepcopy(self.identity)
        result['typed_route'] = {'claim_type': kind, 'contract': ROUTES[kind]}
        return result

    def run(self, payload):
        kind = payload.get('claim_type') if isinstance(payload, dict) else None
        try:
            contract_for(kind)
        except ValueError:
            raise CallFailure({'stage': self.stage, 'identity': copy.deepcopy(self.identity),
                               'router_identity': copy.deepcopy(self.identity), 'input': copy.deepcopy(payload),
                               'api_calls': 0, 'error': 'typed_visual_unknown_claim_type',
                               'phase': 'input', 'failure_kind': 'technical_failure'}) from None
        try:
            raw, audit = self.stages[kind].run(payload)
        except CallFailure as exc:
            raise CallFailure(self._audit(exc.audit, kind)) from None
        return raw, self._audit(audit, kind)
