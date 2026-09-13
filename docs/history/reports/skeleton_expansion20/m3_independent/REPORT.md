# M3 固定事实输入的8-shot对齐测评

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "cases": 20,
  "joint": {
    "tp": 166,
    "predicted": 180,
    "reference": 195,
    "precision": 0.9222222222222223,
    "recall": 0.8512820512820513,
    "f1": 0.8853333333333333
  },
  "per_case": [
    {
      "case_id": "326667",
      "joint": {
        "tp": 6,
        "predicted": 6,
        "reference": 6,
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
        "tp": 6,
        "predicted": 6,
        "reference": 6,
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
          "tp": 4,
          "predicted": 4,
          "reference": 4,
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
      "predicted_removed": 4,
      "technical_fact_count": 0,
      "reference_fact_count": 8
    },
    {
      "case_id": "352377",
      "joint": {
        "tp": 2,
        "predicted": 4,
        "reference": 7,
        "precision": 0.5,
        "recall": 0.2857142857142857,
        "f1": 0.36363636363636365
      },
      "entity_correspondence": {
        "tp": 2,
        "predicted": 2,
        "reference": 2,
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
        "predicted": 4,
        "reference": 7,
        "precision": 0.5,
        "recall": 0.2857142857142857,
        "f1": 0.36363636363636365
      },
      "by_status": {
        "added": {
          "tp": 0,
          "predicted": 0,
          "reference": 4,
          "precision": null,
          "recall": 0.0,
          "f1": 0.0
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
          "predicted": 2,
          "reference": 1,
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0
        }
      },
      "macro_f1": 0.3333333333333333,
      "confirmed_false_removals": 0,
      "predicted_removed": 0,
      "technical_fact_count": 4,
      "reference_fact_count": 13
    },
    {
      "case_id": "195269",
      "joint": {
        "tp": 9,
        "predicted": 9,
        "reference": 10,
        "precision": 1.0,
        "recall": 0.9,
        "f1": 0.9473684210526315
      },
      "entity_correspondence": {
        "tp": 3,
        "predicted": 3,
        "reference": 3,
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
        "tp": 9,
        "predicted": 9,
        "reference": 10,
        "precision": 1.0,
        "recall": 0.9,
        "f1": 0.9473684210526315
      },
      "by_status": {
        "added": {
          "tp": 2,
          "predicted": 2,
          "reference": 2,
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
          "tp": 2,
          "predicted": 2,
          "reference": 2,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "retained": {
          "tp": 4,
          "predicted": 4,
          "reference": 4,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "unresolved": {
          "tp": 1,
          "predicted": 1,
          "reference": 2,
          "precision": 1.0,
          "recall": 0.5,
          "f1": 0.6666666666666666
        }
      },
      "macro_f1": 0.9166666666666666,
      "confirmed_false_removals": 0,
      "predicted_removed": 2,
      "technical_fact_count": 4,
      "reference_fact_count": 19
    },
    {
      "case_id": "69584",
      "joint": {
        "tp": 6,
        "predicted": 6,
        "reference": 6,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "entity_correspondence": {
        "tp": 2,
        "predicted": 2,
        "reference": 2,
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
        "tp": 6,
        "predicted": 6,
        "reference": 6,
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
          "tp": 3,
          "predicted": 3,
          "reference": 3,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "retained": {
          "tp": 3,
          "predicted": 3,
          "reference": 3,
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
      "predicted_removed": 3,
      "technical_fact_count": 0,
      "reference_fact_count": 9
    },
    {
      "case_id": "317188",
      "joint": {
        "tp": 9,
        "predicted": 9,
        "reference": 9,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "entity_correspondence": {
        "tp": 4,
        "predicted": 4,
        "reference": 4,
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
        "tp": 9,
        "predicted": 9,
        "reference": 9,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "by_status": {
        "added": {
          "tp": 2,
          "predicted": 2,
          "reference": 2,
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
          "tp": 3,
          "predicted": 3,
          "reference": 3,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "retained": {
          "tp": 4,
          "predicted": 4,
          "reference": 4,
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
      "predicted_removed": 3,
      "technical_fact_count": 0,
      "reference_fact_count": 13
    },
    {
      "case_id": "373677",
      "joint": {
        "tp": 12,
        "predicted": 12,
        "reference": 12,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "entity_correspondence": {
        "tp": 3,
        "predicted": 3,
        "reference": 3,
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
        "tp": 12,
        "predicted": 12,
        "reference": 12,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "by_status": {
        "added": {
          "tp": 3,
          "predicted": 3,
          "reference": 3,
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
          "tp": 6,
          "predicted": 6,
          "reference": 6,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "retained": {
          "tp": 3,
          "predicted": 3,
          "reference": 3,
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
      "predicted_removed": 6,
      "technical_fact_count": 0,
      "reference_fact_count": 15
    },
    {
      "case_id": "279634",
      "joint": {
        "tp": 8,
        "predicted": 8,
        "reference": 10,
        "precision": 1.0,
        "recall": 0.8,
        "f1": 0.8888888888888888
      },
      "entity_correspondence": {
        "tp": 5,
        "predicted": 5,
        "reference": 5,
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
        "tp": 8,
        "predicted": 8,
        "reference": 10,
        "precision": 1.0,
        "recall": 0.8,
        "f1": 0.8888888888888888
      },
      "by_status": {
        "added": {
          "tp": 2,
          "predicted": 2,
          "reference": 2,
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
          "tp": 0,
          "predicted": 0,
          "reference": 2,
          "precision": null,
          "recall": 0.0,
          "f1": 0.0
        },
        "retained": {
          "tp": 5,
          "predicted": 5,
          "reference": 5,
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
      "macro_f1": 0.75,
      "confirmed_false_removals": 0,
      "predicted_removed": 0,
      "technical_fact_count": 2,
      "reference_fact_count": 17
    },
    {
      "case_id": "45094",
      "joint": {
        "tp": 14,
        "predicted": 14,
        "reference": 14,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "entity_correspondence": {
        "tp": 4,
        "predicted": 4,
        "reference": 4,
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
        "tp": 14,
        "predicted": 14,
        "reference": 14,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "by_status": {
        "added": {
          "tp": 2,
          "predicted": 2,
          "reference": 2,
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
          "tp": 8,
          "predicted": 8,
          "reference": 8,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "retained": {
          "tp": 4,
          "predicted": 4,
          "reference": 4,
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
      "predicted_removed": 8,
      "technical_fact_count": 0,
      "reference_fact_count": 18
    },
    {
      "case_id": "381925",
      "joint": {
        "tp": 12,
        "predicted": 12,
        "reference": 12,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "entity_correspondence": {
        "tp": 5,
        "predicted": 5,
        "reference": 5,
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
        "tp": 12,
        "predicted": 12,
        "reference": 12,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "by_status": {
        "added": {
          "tp": 3,
          "predicted": 3,
          "reference": 3,
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
          "tp": 3,
          "predicted": 3,
          "reference": 3,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "retained": {
          "tp": 6,
          "predicted": 6,
          "reference": 6,
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
      "predicted_removed": 3,
      "technical_fact_count": 0,
      "reference_fact_count": 18
    },
    {
      "case_id": "54264",
      "joint": {
        "tp": 11,
        "predicted": 11,
        "reference": 11,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "entity_correspondence": {
        "tp": 2,
        "predicted": 2,
        "reference": 2,
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
        "tp": 11,
        "predicted": 11,
        "reference": 11,
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
          "tp": 6,
          "predicted": 6,
          "reference": 6,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "retained": {
          "tp": 4,
          "predicted": 4,
          "reference": 4,
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
      "predicted_removed": 6,
      "technical_fact_count": 0,
      "reference_fact_count": 15
    },
    {
      "case_id": "256003",
      "joint": {
        "tp": 8,
        "predicted": 8,
        "reference": 10,
        "precision": 1.0,
        "recall": 0.8,
        "f1": 0.8888888888888888
      },
      "entity_correspondence": {
        "tp": 1,
        "predicted": 1,
        "reference": 2,
        "precision": 1.0,
        "recall": 0.5,
        "f1": 0.6666666666666666
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
        "tp": 8,
        "predicted": 8,
        "reference": 10,
        "precision": 1.0,
        "recall": 0.8,
        "f1": 0.8888888888888888
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
          "tp": 7,
          "predicted": 7,
          "reference": 8,
          "precision": 1.0,
          "recall": 0.875,
          "f1": 0.9333333333333333
        },
        "retained": {
          "tp": 1,
          "predicted": 1,
          "reference": 2,
          "precision": 1.0,
          "recall": 0.5,
          "f1": 0.6666666666666666
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
      "macro_f1": 0.8,
      "confirmed_false_removals": 0,
      "predicted_removed": 7,
      "technical_fact_count": 3,
      "reference_fact_count": 12
    },
    {
      "case_id": "462687",
      "joint": {
        "tp": 6,
        "predicted": 12,
        "reference": 11,
        "precision": 0.5,
        "recall": 0.5454545454545454,
        "f1": 0.5217391304347826
      },
      "entity_correspondence": {
        "tp": 0,
        "predicted": 1,
        "reference": 0,
        "precision": 0.0,
        "recall": null,
        "f1": 0.0
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
        "tp": 6,
        "predicted": 12,
        "reference": 11,
        "precision": 0.5,
        "recall": 0.5454545454545454,
        "f1": 0.5217391304347826
      },
      "by_status": {
        "added": {
          "tp": 1,
          "predicted": 1,
          "reference": 2,
          "precision": 1.0,
          "recall": 0.5,
          "f1": 0.6666666666666666
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
          "tp": 5,
          "predicted": 8,
          "reference": 6,
          "precision": 0.625,
          "recall": 0.8333333333333334,
          "f1": 0.7142857142857143
        },
        "retained": {
          "tp": 0,
          "predicted": 1,
          "reference": 0,
          "precision": 0.0,
          "recall": null,
          "f1": 0.0
        },
        "unresolved": {
          "tp": 0,
          "predicted": 2,
          "reference": 3,
          "precision": 0.0,
          "recall": 0.0,
          "f1": 0.0
        }
      },
      "macro_f1": 0.34523809523809523,
      "confirmed_false_removals": 0,
      "predicted_removed": 8,
      "technical_fact_count": 3,
      "reference_fact_count": 18
    },
    {
      "case_id": "450500",
      "joint": {
        "tp": 14,
        "predicted": 16,
        "reference": 15,
        "precision": 0.875,
        "recall": 0.9333333333333333,
        "f1": 0.9032258064516129
      },
      "entity_correspondence": {
        "tp": 6,
        "predicted": 6,
        "reference": 6,
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
        "tp": 14,
        "predicted": 16,
        "reference": 15,
        "precision": 0.875,
        "recall": 0.9333333333333333,
        "f1": 0.9032258064516129
      },
      "by_status": {
        "added": {
          "tp": 3,
          "predicted": 3,
          "reference": 3,
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
          "tp": 5,
          "predicted": 7,
          "reference": 5,
          "precision": 0.7142857142857143,
          "recall": 1.0,
          "f1": 0.8333333333333334
        },
        "retained": {
          "tp": 6,
          "predicted": 6,
          "reference": 6,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "unresolved": {
          "tp": 0,
          "predicted": 0,
          "reference": 1,
          "precision": null,
          "recall": 0.0,
          "f1": 0.0
        }
      },
      "macro_f1": 0.7083333333333334,
      "confirmed_false_removals": 0,
      "predicted_removed": 7,
      "technical_fact_count": 0,
      "reference_fact_count": 22
    },
    {
      "case_id": "69946",
      "joint": {
        "tp": 6,
        "predicted": 7,
        "reference": 7,
        "precision": 0.8571428571428571,
        "recall": 0.8571428571428571,
        "f1": 0.8571428571428571
      },
      "entity_correspondence": {
        "tp": 3,
        "predicted": 4,
        "reference": 3,
        "precision": 0.75,
        "recall": 1.0,
        "f1": 0.8571428571428571
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
        "tp": 7,
        "predicted": 7,
        "reference": 7,
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
          "tp": 2,
          "predicted": 2,
          "reference": 2,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "retained": {
          "tp": 3,
          "predicted": 4,
          "reference": 3,
          "precision": 0.75,
          "recall": 1.0,
          "f1": 0.8571428571428571
        },
        "unresolved": {
          "tp": 0,
          "predicted": 0,
          "reference": 1,
          "precision": null,
          "recall": 0.0,
          "f1": 0.0
        }
      },
      "macro_f1": 0.7142857142857143,
      "confirmed_false_removals": 0,
      "predicted_removed": 2,
      "technical_fact_count": 0,
      "reference_fact_count": 11
    },
    {
      "case_id": "265462",
      "joint": {
        "tp": 7,
        "predicted": 7,
        "reference": 7,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "entity_correspondence": {
        "tp": 2,
        "predicted": 2,
        "reference": 2,
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
        "tp": 7,
        "predicted": 7,
        "reference": 7,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "by_status": {
        "added": {
          "tp": 4,
          "predicted": 4,
          "reference": 4,
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
      "predicted_removed": 1,
      "technical_fact_count": 0,
      "reference_fact_count": 9
    },
    {
      "case_id": "303499",
      "joint": {
        "tp": 4,
        "predicted": 5,
        "reference": 5,
        "precision": 0.8,
        "recall": 0.8,
        "f1": 0.8
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
        "tp": 4,
        "predicted": 5,
        "reference": 5,
        "precision": 0.8,
        "recall": 0.8,
        "f1": 0.8
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
          "tp": 2,
          "predicted": 3,
          "reference": 3,
          "precision": 0.6666666666666666,
          "recall": 0.6666666666666666,
          "f1": 0.6666666666666666
        }
      },
      "macro_f1": 0.8333333333333333,
      "confirmed_false_removals": 0,
      "predicted_removed": 0,
      "technical_fact_count": 2,
      "reference_fact_count": 16
    },
    {
      "case_id": "316617",
      "joint": {
        "tp": 3,
        "predicted": 4,
        "reference": 10,
        "precision": 0.75,
        "recall": 0.3,
        "f1": 0.42857142857142855
      },
      "entity_correspondence": {
        "tp": 0,
        "predicted": 1,
        "reference": 0,
        "precision": 0.0,
        "recall": null,
        "f1": 0.0
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
        "tp": 4,
        "predicted": 4,
        "reference": 10,
        "precision": 1.0,
        "recall": 0.4,
        "f1": 0.5714285714285714
      },
      "by_status": {
        "added": {
          "tp": 1,
          "predicted": 1,
          "reference": 5,
          "precision": 1.0,
          "recall": 0.2,
          "f1": 0.3333333333333333
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
          "reference": 2,
          "precision": null,
          "recall": 0.0,
          "f1": 0.0
        },
        "retained": {
          "tp": 0,
          "predicted": 1,
          "reference": 0,
          "precision": 0.0,
          "recall": null,
          "f1": 0.0
        },
        "unresolved": {
          "tp": 2,
          "predicted": 2,
          "reference": 3,
          "precision": 1.0,
          "recall": 0.6666666666666666,
          "f1": 0.8
        }
      },
      "macro_f1": 0.2833333333333333,
      "confirmed_false_removals": 0,
      "predicted_removed": 0,
      "technical_fact_count": 6,
      "reference_fact_count": 17
    },
    {
      "case_id": "519838",
      "joint": {
        "tp": 7,
        "predicted": 7,
        "reference": 9,
        "precision": 1.0,
        "recall": 0.7777777777777778,
        "f1": 0.875
      },
      "entity_correspondence": {
        "tp": 3,
        "predicted": 3,
        "reference": 3,
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
        "tp": 7,
        "predicted": 7,
        "reference": 9,
        "precision": 1.0,
        "recall": 0.7777777777777778,
        "f1": 0.875
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
          "tp": 3,
          "predicted": 3,
          "reference": 5,
          "precision": 1.0,
          "recall": 0.6,
          "f1": 0.75
        },
        "retained": {
          "tp": 3,
          "predicted": 3,
          "reference": 3,
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
      "macro_f1": 0.9166666666666666,
      "confirmed_false_removals": 0,
      "predicted_removed": 3,
      "technical_fact_count": 2,
      "reference_fact_count": 14
    },
    {
      "case_id": "565761",
      "joint": {
        "tp": 13,
        "predicted": 13,
        "reference": 14,
        "precision": 1.0,
        "recall": 0.9285714285714286,
        "f1": 0.9629629629629629
      },
      "entity_correspondence": {
        "tp": 4,
        "predicted": 4,
        "reference": 4,
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
        "tp": 13,
        "predicted": 13,
        "reference": 14,
        "precision": 1.0,
        "recall": 0.9285714285714286,
        "f1": 0.9629629629629629
      },
      "by_status": {
        "added": {
          "tp": 3,
          "predicted": 3,
          "reference": 3,
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
          "tp": 5,
          "predicted": 5,
          "reference": 5,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "retained": {
          "tp": 5,
          "predicted": 5,
          "reference": 5,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "unresolved": {
          "tp": 0,
          "predicted": 0,
          "reference": 1,
          "precision": null,
          "recall": 0.0,
          "f1": 0.0
        }
      },
      "macro_f1": 0.75,
      "confirmed_false_removals": 0,
      "predicted_removed": 5,
      "technical_fact_count": 3,
      "reference_fact_count": 21
    },
    {
      "case_id": "483723",
      "joint": {
        "tp": 9,
        "predicted": 10,
        "reference": 10,
        "precision": 0.9,
        "recall": 0.9,
        "f1": 0.9
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
        "tp": 9,
        "predicted": 10,
        "reference": 10,
        "precision": 0.9,
        "recall": 0.9,
        "f1": 0.9
      },
      "by_status": {
        "added": {
          "tp": 4,
          "predicted": 4,
          "reference": 4,
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
          "tp": 3,
          "predicted": 3,
          "reference": 3,
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
          "tp": 1,
          "predicted": 2,
          "reference": 2,
          "precision": 0.5,
          "recall": 0.5,
          "f1": 0.5
        }
      },
      "macro_f1": 0.875,
      "confirmed_false_removals": 0,
      "predicted_removed": 3,
      "technical_fact_count": 1,
      "reference_fact_count": 15
    }
  ],
  "reference_status": "assistant_candidate_not_gold",
  "human_accuracy": null
}
```

- 只送固定事实/原文；未调用M2，隔离上游误差。
- 技术失败保留完整事实名册但不能获得unresolved正确分。
