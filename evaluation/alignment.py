"""Contextual referent sidecar and conservative, complete one-use fact alignment."""
import copy
from collections import Counter

from .common import ContractError, StageFailure, document_context, require, valid_quote
from .alignment_groups import resolve
from .alignment_policy import entity_groups, semantic_review

STATUSES = {"retained", "removed", "added", "modified", "ambiguous"}
REASONS = {"same_fact", "value_changed", "not_expressed", "entity_uncertain", "granularity",
           "partial_overlap", "extraction_gap", "source_uncertain", "other_scope", "qualifier_difference"}


def slot_key(slot):
    value=slot.strip().casefold().replace(' ', '_').replace('-', '_')
    return {'colour':'color','colour_attribute':'color','color_attribute':'color',
            'material_attribute':'material','age_attribute':'age'}.get(value,value)


def ids(value, allowed=None):
    require(isinstance(value, list) and all(isinstance(x, str) for x in value), "ID list required")
    require(len(value) == len(set(value)), "duplicate ID in one list")
    if allowed is not None:
        require(set(value) <= set(allowed), "unknown ID")
    return value


def align_entities(payload, original, steer):
    require(set(payload) == {"original_entities", "steer_entities", "entity_alignment"}, "entity sidecar fields required")
    entities = {}
    for side, doc in [("original", original), ("steer", steer)]:
        records = payload[side + "_entities"]
        require(isinstance(records, list), "entities must be an array")
        current = {}
        for e in records:
            require(isinstance(e, dict) and set(e) == {"id", "mention", "fact_ids", "description"}, "entity sidecar record fields")
            require(isinstance(e["id"], str) and bool(e["id"]) and e["id"] not in current, "unique local entity ID required")
            require(valid_quote(doc["text"], e["mention"]), "entity mention must occur in its caption")
            require(isinstance(e["description"], str), "entity description required")
            ids(e["fact_ids"], {f["id"] for f in doc["facts"]})
            current[e["id"]] = copy.deepcopy(e)
        entities[side] = current
    require(isinstance(payload["entity_alignment"], list), "entity alignment array required")
    seen = {"original": set(), "steer": set()}; groups = []; mappings = {"original": {}, "steer": {}}
    validated=[]
    for row in payload["entity_alignment"]:
        require(isinstance(row, dict) and set(row) == {"original_entity_ids", "steer_entity_ids", "status", "reason"}, "entity correspondence fields")
        a = ids(row["original_entity_ids"], entities["original"])
        b = ids(row["steer_entity_ids"], entities["steer"])
        status = row["status"]
        require(status in ("matched", "original_only", "steer_only", "ambiguous"), "invalid entity status")
        require(bool(a or b), "empty entity correspondence")
        require(isinstance(row["reason"], str) and bool(row["reason"]), "entity evidence reason required")
        if status == "matched": require(len(a) == len(b) == 1, "matched entity must be one-to-one")
        if status == "original_only": require(len(a) == 1 and not b, "original-only shape")
        if status == "steer_only": require(len(b) == 1 and not a, "steer-only shape")
        validated.append(copy.deepcopy(row))
    normalized,entity_notes=entity_groups(validated)
    for i,row in enumerate(normalized,1):
        a,b=row['original_entity_ids'],row['steer_entity_ids'];status=row['status']
        global_id = None if status == "ambiguous" else f"g{i}"
        for side, local in [("original", a), ("steer", b)]:
            require(not set(local) & seen[side], "entity used in multiple correspondences")
            seen[side].update(local)
            for entity_id in local: mappings[side][entity_id] = global_id
        groups.append({**copy.deepcopy(row), "global_entity": global_id})
    require(all(seen[s] == set(entities[s]) for s in seen), "every sidecar entity must have a correspondence")
    return {"original_entities": list(entities["original"].values()), "steer_entities": list(entities["steer"].values()),
            "entity_alignment": groups, "global_mapping": mappings,**({'resolution_notes':entity_notes} if entity_notes else {})}


def fallback_alignments(original, steer, reason="stage_failed"):
    return [{"original_fact_ids": [f["id"]] if side == "original" else [],
             "steer_fact_ids": [f["id"]] if side == "steer" else [],
             "type": f["type"], "types": [f["type"]], "status": "ambiguous", "reason": reason,
             "evidence": [], "global_entity_ids": [], "in_main": f["type"] != "other"}
            for side, doc in [("original", original), ("steer", steer)] for f in doc["facts"]]


def align_facts(payload, original, steer, sidecar, review_policy=semantic_review):
    require(set(payload) == {"original_bindings", "steer_bindings", "fact_alignment"}, "binding/alignment fields required")
    documents = {"original": original, "steer": steer}
    facts = {s: {f["id"]: f for f in d["facts"]} for s, d in documents.items()}
    bindings = {}
    for side in documents:
        records = payload[side + "_bindings"]
        require(isinstance(records, list), "bindings must be arrays")
        current = {}
        for b in records:
            require(isinstance(b, dict) and set(b) == {"fact_id", "entity_ids", "slot"}, "binding fields required")
            require(isinstance(b["fact_id"], str) and b["fact_id"] in facts[side] and b["fact_id"] not in current, "unique known bound fact required")
            ids(b["entity_ids"], sidecar["global_mapping"][side])
            require(isinstance(b["slot"], str) and bool(b["slot"].strip()), "narrow semantic slot required")
            current[b["fact_id"]] = copy.deepcopy(b)
        require(set(current) == set(facts[side]), "every fact requires a binding")
        bindings[side] = current
    raw_rows = payload["fact_alignment"]
    require(isinstance(raw_rows, list), "fact alignment array required")
    candidates, rejected, warnings, reviews = [], [], [], []
    for index, row in enumerate(raw_rows):
        try:
            require(isinstance(row, dict) and set(row) == {"original_fact_ids", "steer_fact_ids", "status", "reason", "evidence"}, "fact correspondence fields")
            a = ids(row["original_fact_ids"], facts["original"])
            b = ids(row["steer_fact_ids"], facts["steer"])
            require(bool(a or b), "empty correspondence")
            require(row["status"] in tuple(STATUSES), "invalid status")
            require(row["reason"] in tuple(REASONS), "invalid reason")
            require(isinstance(row["evidence"], list), "evidence must be an array")
            for e in row["evidence"]:
                require(isinstance(e, dict) and set(e) == {"side", "quote"}, "evidence side/quote required")
                require(e["side"] in ("original", "steer") and valid_quote(documents[e["side"]]["text"], e["quote"]), "evidence must be from that caption")
            status = row["status"]
            if status == "retained": require(bool(a) and bool(b), "retained requires both sides")
            if status == "modified": require(len(a) == len(b) == 1, "modified must be one-to-one")
            if status == "removed": require(len(a) == 1 and not b and row["reason"] == "not_expressed", "removed shape/reason")
            if status == "added": require(len(b) == 1 and not a and row["reason"] == "not_expressed", "added shape/reason")
            if status == "retained": require(row["reason"] == "same_fact", "retained reason")
            if status == "modified": require(row["reason"] == "value_changed", "modified reason")
            if row["reason"] == "extraction_gap":
                require(status == "ambiguous" and bool(a) != bool(b), "extraction gap must be one-sided ambiguous")
                opposite = "steer" if a else "original"
                require(any(e["side"] == opposite for e in row["evidence"]), "extraction gap needs opposite caption evidence")
            globals_by_side = {}
            used_facts = []
            participants=[]; slots=[]
            row_warnings=[]
            for side, local in [("original", a), ("steer", b)]:
                globals_by_side[side] = []
                for fid in local:
                    f = facts[side][fid]; used_facts.append(f)
                    binding = bindings[side][fid]
                    global_ids = [sidecar["global_mapping"][side][e] for e in binding["entity_ids"]]
                    globals_by_side[side].extend(global_ids)
                    participants.append(global_ids)
                    slots.append(slot_key(binding['slot']))
                    if status != "ambiguous":
                        require(valid_quote(documents[side]['text'], f.get('source')), "source must occur in its caption")
                        if f.get('source_status')=='ambiguous':
                            row_warnings.append({'rule':'repeated_source_occurrence','side':side,'fact_id':fid,
                                                 'note':'Grounding has repeated occurrences; referent binding is separately known. No occurrence chosen automatically.'})
            types = sorted({f["type"] for f in used_facts})
            decision,policy_warnings=review_policy(status,used_facts,participants,slots)
            row_warnings.extend({**w,'original_fact_ids':a,'steer_fact_ids':b} for w in policy_warnings)
            if decision:
                reason,rule=decision
                reviews.append({'index':index,'raw':copy.deepcopy(row),'rule':rule,'result':'ambiguous','reason':reason})
                row={**copy.deepcopy(row),'status':'ambiguous','reason':reason,
                     'model_proposal':{'status':status,'reason':row['reason']},'semantic_guard':rule}
            candidates.append({**copy.deepcopy(row), "type": types[0] if len(types) == 1 else None, "types": types,
                         "in_main": any(t != "other" for t in types),
                         "global_entity_ids": sorted({g for gs in globals_by_side.values() for g in gs if g is not None})})
            warnings.extend(row_warnings)
        except (ContractError, TypeError, KeyError) as exc:
            rejected.append({"index": index, "raw": copy.deepcopy(row), "error": str(exc)})
    equivalence_keys={(s,fid):(f['type'],tuple(sidecar['global_mapping'][s][e] for e in bindings[s][fid]['entity_ids']),
                               slot_key(bindings[s][fid]['slot']), ' '.join(f['fact'].casefold().rstrip('.').split()),f['assertion'],f['polarity'])
                      for s in documents for fid,f in facts[s].items()}
    rows,related,notes,conflicts=resolve(candidates,equivalence_keys)
    rejected.extend(conflicts)
    # Recompute group metadata after trimming contextual references / joining uncertainty groups.
    for row in rows:
        fs=[facts[s][fid] for s in documents for fid in row[s+'_fact_ids']]
        types=sorted({f['type'] for f in fs})
        row.update(type=types[0] if len(types)==1 else None,types=types,in_main=any(t!='other' for t in types))
        row['global_entity_ids']=sorted({sidecar['global_mapping'][s][e] for s in documents for fid in row[s+'_fact_ids'] for e in bindings[s][fid]['entity_ids'] if sidecar['global_mapping'][s][e] is not None})
        if row['status']=='retained' and (len(row['original_fact_ids'])>1 or len(row['steer_fact_ids'])>1):
            row.update(equivalent_fact_group=True,semantic_unit_count=1)
    for ref in related:
        ref['qualifiers']={s:[{'fact_id':fid,'assertion':facts[s][fid]['assertion'],'polarity':facts[s][fid]['polarity']} for fid in ref[s+'_fact_ids']] for s in documents}
    assigned={s:{fid for row in rows for fid in row[s+'_fact_ids']} for s in documents}
    # Failure to assign is an explicit ambiguous state, NEVER an inferred removal/addition.
    for row in fallback_alignments(original, steer, "alignment_validation_error"):
        side = "original" if row["original_fact_ids"] else "steer"
        if row[side + "_fact_ids"][0] not in assigned[side]: rows.append(row)
    complete = {s: Counter(fid for row in rows for fid in row[s + "_fact_ids"]) for s in documents}
    require(all(set(complete[s]) == set(facts[s]) and all(n == 1 for n in complete[s].values()) for s in documents), "internal completeness error")
    return {"fact_alignment": rows, "original_bindings": list(bindings["original"].values()),
            "steer_bindings": list(bindings["steer"].values()), "rejected_alignments": rejected,
            "related_correspondences":related,"resolution_notes":notes,"warnings":warnings,"semantic_reviews":reviews,
            "status": "needs_review" if rejected or reviews or any(r["reason"] == "alignment_validation_error" for r in rows) else "ready"}


class PairAligner:
    def __init__(self, stage): self.stage = stage

    def entities(self, original, steer):
        payload = {"original": document_context(original), "steer": document_context(steer)}
        raw, audit = self.stage.run("entities", payload)
        try:
            return {"status": "ready", **align_entities(raw, original, steer), "audit": audit}
        except (ContractError, TypeError, KeyError) as exc:
            raise StageFailure(str(exc), audit) from exc

    def facts(self, pair_id, original, steer, sidecar):
        payload = {"original": document_context(original), "steer": document_context(steer),
                   "entity_sidecar": {k: v for k, v in sidecar.items() if k not in {"audit", "status"}}}
        raw, audit = self.stage.run("alignment", payload)
        try:
            return {"pair_id": pair_id, **align_facts(raw, original, steer, sidecar), "audit": audit,
                    "entity_alignment": sidecar["entity_alignment"]}
        except (ContractError, TypeError, KeyError) as exc:
            raise StageFailure(str(exc), audit) from exc
