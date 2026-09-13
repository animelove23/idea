"""Export structured fields; array targets remain JSON in CSV."""
import json
from .schemas import FACT_COLUMNS, validate_document

def build_facts(record, payload):
    validate_document(payload, expected_text=record["caption"])
    rows = []
    for fact in payload["facts"]:
        row = {"sample_id": record["sample_id"], "fact_id": fact["id"], **{k: v for k, v in fact.items() if k != "id"}}
        rows.append({k: json.dumps(row[k], ensure_ascii=False) if isinstance(row.get(k), list) else row.get(k, "") for k in FACT_COLUMNS})
    return rows
