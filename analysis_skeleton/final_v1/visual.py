"""Candidate M5 contract for whole propositions; independent schema intervention.

This module is not an accepted production replacement. It keeps the original six
image/question demonstrations and image transport, while adding a proposition
verdict that cannot bypass the existing evidence compiler's referent safeguards.
"""
import copy
from pathlib import Path

from analysis_skeleton.common import read_jsonl, sha
from analysis_skeleton.evidence_verifier_v1.compiler import compile_evidence
from analysis_skeleton.evidence_verifier_v1.stage import EvidenceStage, make_evidence_shots
from analysis_skeleton.m5_verify import VisualStage


ROOT = Path(__file__).parent
MODEL = "deepseek-flash"
CONTRACT = "final_v1_whole_proposition_candidate"
EVIDENCE_FIELDS = {
    "claim_type", "candidate_status", "region_status", "bbox",
    "observed_category", "scope", "visible_cues", "limitation",
    "attribute_status", "proposition_status",
}


def validate(raw, claim_type):
    """Compile visual evidence without accepting labels or evaluation references.

The old compiler still validates every old field. A visible object is necessary
but insufficient for supporting a complete entity statement with qualifiers.
"""
    if not isinstance(raw, dict):
        raise ValueError("evidence_object_required")
    if "label" in raw:
        raise ValueError("model_must_not_choose_final_label")
    if set(raw) != EVIDENCE_FIELDS:
        raise ValueError("whole_proposition_fields_required_no_extras")
    status = raw["proposition_status"]
    if not isinstance(status, str) or status not in {"supported", "contradicted", "unresolved"}:
        raise ValueError("invalid_proposition_status")
    old_raw = {key: copy.deepcopy(value) for key, value in raw.items() if key != "proposition_status"}
    result = compile_evidence(old_raw, claim_type)
    base_label = result["label"]
    base_rule = result["decision_rule"]
    decisive = raw["region_status"] == "inspectable" and raw["limitation"] == "none"
    referent_resolved = raw["candidate_status"] != "unresolved"

    if status == "unresolved":
        label, rule = "uncertain", "whole_proposition_unresolved"
    elif not decisive or not referent_resolved:
        label, rule = "uncertain", "whole_proposition_blocked_by_evidence_limit"
    elif status == "supported":
        if base_label == "supported":
            label, rule = "supported", "referent_and_whole_proposition_supported"
        else:
            label, rule = "uncertain", "whole_proposition_support_conflicts_with_evidence"
    else:
        # A matching category can still contradict count, subtype, or qualifiers.
        # No new model call, textual heuristic, or reference answer is consulted.
        label, rule = "hallucinated", "visible_whole_proposition_contradiction"

    result.update(
        label=label,
        evidence=copy.deepcopy(raw),
        decision_rule=rule,
        base_evidence_label=base_label,
        base_evidence_decision_rule=base_rule,
        proposition_support_blocked=status == "supported" and label != "supported",
        attribute_support_blocked_by_referent=(
            claim_type == "attribute" and raw["attribute_status"] == "supported"
            and (raw["candidate_status"] != "matches" or not decisive)
        ),
        contract_version=CONTRACT,
    )
    return result


def prepare_shots(original=None):
    """Transform only the original six demonstration outputs, never test labels."""
    if original is None:
        original = read_jsonl("analysis_skeleton/shots/verify.jsonl")
    canonical = read_jsonl("analysis_skeleton/shots/verify.jsonl")
    if original != canonical:
        raise ValueError("only_original_six_demonstrations_allowed")
    rows = make_evidence_shots(original)
    mapping = {"supported": "supported", "hallucinated": "contradicted", "uncertain": "unresolved"}
    for old, row in zip(original, rows):
        row["output"]["proposition_status"] = mapping[old["output"]["label"]]
        if validate(row["output"], row["semantic_type"])["label"] != old["output"]["label"]:
            raise ValueError("demonstration_contract_changed_label")
    return rows


class FinalVisualStage(EvidenceStage):
    """Exactly one full-image Flash request with six original image/text shots."""

    def __init__(self, shots_path, config_path="decomposition/api_config.local.json", transport=None):
        # Reuse EvidenceStage.user/messages, but explicitly pin Flash and the new
        # contract instead of invoking the old shot-equality constructor.
        VisualStage.__init__(self, config_path, transport=transport, model=MODEL)
        rows = read_jsonl(shots_path)
        if rows != prepare_shots(self.shots):
            raise ValueError("whole_proposition_demonstrations_changed")
        self.rules_path = ROOT / "visual_rules.txt"
        self.rules = self.rules_path.read_text(encoding="utf-8")
        self.shots = rows
        self.shots_path = Path(shots_path)
        self.identity.update(
            model=MODEL,
            explicit_model=MODEL,
            prompt_sha=sha(self.rules_path),
            shots_sha=sha(self.shots_path),
            evidence_contract=CONTRACT,
            decision_code_sha=sha(__file__),
            base_compiler_sha=sha("analysis_skeleton/evidence_verifier_v1/compiler.py"),
            base_validator_sha=sha("analysis_skeleton/evidence_verifier_v1/stage.py"),
            visual_transport_sha=sha("analysis_skeleton/m5_verify.py"),
            llm_transport_sha=sha("analysis_skeleton/llm.py"),
            intervention="independent_whole_proposition_schema_candidate_not_yet_accepted",
            extra_image_views=0,
        )
