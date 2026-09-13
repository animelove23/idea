# M3 固定事实输入的8-shot对齐测评

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "cases": 4,
  "joint": {
    "tp": 9,
    "predicted": 9,
    "reference": 9,
    "precision": 1.0,
    "recall": 1.0,
    "f1": 1.0
  },
  "per_case": [
    {
      "case_id": "align_01",
      "joint": {
        "tp": 2,
        "predicted": 2,
        "reference": 2,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "entity_correspondence": {
        "tp": 1,
        "predicted": 1,
        "reference": 1,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "extraction_gap": {
        "tp": 0,
        "predicted": 0,
        "reference": 0,
        "precision": null,
        "recall": null,
        "f1": null
      },
      "edge": {
        "tp": 2,
        "predicted": 2,
        "reference": 2,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "by_status": {
        "added": {
          "tp": 0,
          "predicted": 0,
          "reference": 0,
          "precision": null,
          "recall": null,
          "f1": null
        },
        "modified": {
          "tp": 1,
          "predicted": 1,
          "reference": 1,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "removed": {
          "tp": 0,
          "predicted": 0,
          "reference": 0,
          "precision": null,
          "recall": null,
          "f1": null
        },
        "retained": {
          "tp": 1,
          "predicted": 1,
          "reference": 1,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "unresolved": {
          "tp": 0,
          "predicted": 0,
          "reference": 0,
          "precision": null,
          "recall": null,
          "f1": null
        }
      },
      "macro_f1": 1.0,
      "confirmed_false_removals": 0,
      "predicted_removed": 0,
      "technical_fact_count": 0,
      "reference_fact_count": 4
    },
    {
      "case_id": "align_02",
      "joint": {
        "tp": 3,
        "predicted": 3,
        "reference": 3,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "entity_correspondence": {
        "tp": 1,
        "predicted": 1,
        "reference": 1,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "extraction_gap": {
        "tp": 0,
        "predicted": 0,
        "reference": 0,
        "precision": null,
        "recall": null,
        "f1": null
      },
      "edge": {
        "tp": 3,
        "predicted": 3,
        "reference": 3,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "by_status": {
        "added": {
          "tp": 1,
          "predicted": 1,
          "reference": 1,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "modified": {
          "tp": 0,
          "predicted": 0,
          "reference": 0,
          "precision": null,
          "recall": null,
          "f1": null
        },
        "removed": {
          "tp": 1,
          "predicted": 1,
          "reference": 1,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "retained": {
          "tp": 1,
          "predicted": 1,
          "reference": 1,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "unresolved": {
          "tp": 0,
          "predicted": 0,
          "reference": 0,
          "precision": null,
          "recall": null,
          "f1": null
        }
      },
      "macro_f1": 1.0,
      "confirmed_false_removals": 0,
      "predicted_removed": 1,
      "technical_fact_count": 0,
      "reference_fact_count": 4
    },
    {
      "case_id": "align_03",
      "joint": {
        "tp": 2,
        "predicted": 2,
        "reference": 2,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "entity_correspondence": {
        "tp": 1,
        "predicted": 1,
        "reference": 1,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "extraction_gap": {
        "tp": 1,
        "predicted": 1,
        "reference": 1,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "edge": {
        "tp": 2,
        "predicted": 2,
        "reference": 2,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "by_status": {
        "added": {
          "tp": 0,
          "predicted": 0,
          "reference": 0,
          "precision": null,
          "recall": null,
          "f1": null
        },
        "modified": {
          "tp": 0,
          "predicted": 0,
          "reference": 0,
          "precision": null,
          "recall": null,
          "f1": null
        },
        "removed": {
          "tp": 0,
          "predicted": 0,
          "reference": 0,
          "precision": null,
          "recall": null,
          "f1": null
        },
        "retained": {
          "tp": 1,
          "predicted": 1,
          "reference": 1,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "unresolved": {
          "tp": 1,
          "predicted": 1,
          "reference": 1,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        }
      },
      "macro_f1": 1.0,
      "confirmed_false_removals": 0,
      "predicted_removed": 0,
      "technical_fact_count": 0,
      "reference_fact_count": 3
    },
    {
      "case_id": "align_04",
      "joint": {
        "tp": 2,
        "predicted": 2,
        "reference": 2,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "entity_correspondence": {
        "tp": 1,
        "predicted": 1,
        "reference": 1,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "extraction_gap": {
        "tp": 0,
        "predicted": 0,
        "reference": 0,
        "precision": null,
        "recall": null,
        "f1": null
      },
      "edge": {
        "tp": 2,
        "predicted": 2,
        "reference": 2,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "by_status": {
        "added": {
          "tp": 0,
          "predicted": 0,
          "reference": 0,
          "precision": null,
          "recall": null,
          "f1": null
        },
        "modified": {
          "tp": 0,
          "predicted": 0,
          "reference": 0,
          "precision": null,
          "recall": null,
          "f1": null
        },
        "removed": {
          "tp": 0,
          "predicted": 0,
          "reference": 0,
          "precision": null,
          "recall": null,
          "f1": null
        },
        "retained": {
          "tp": 2,
          "predicted": 2,
          "reference": 2,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "unresolved": {
          "tp": 0,
          "predicted": 0,
          "reference": 0,
          "precision": null,
          "recall": null,
          "f1": null
        }
      },
      "macro_f1": 1.0,
      "confirmed_false_removals": 0,
      "predicted_removed": 0,
      "technical_fact_count": 0,
      "reference_fact_count": 4
    }
  ],
  "reference_status": "assistant_candidate_not_gold",
  "human_accuracy": null
}
```

- 只送固定事实/原文；未调用M2，隔离上游误差。
- 技术失败保留完整事实名册但不能获得unresolved正确分。
