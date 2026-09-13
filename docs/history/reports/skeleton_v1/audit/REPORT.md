# 冻结结果复核与分项指标

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "frozen_runs_checked": [
    "m0_resolved",
    "m1",
    "m2_online",
    "m3_online",
    "m5_online"
  ],
  "m2_by_attribute_slot": {
    "color": {
      "tp": 5,
      "predicted": 5,
      "reference": 5,
      "precision": 1.0,
      "recall": 1.0,
      "f1": 1.0
    },
    "material": {
      "tp": 4,
      "predicted": 4,
      "reference": 4,
      "precision": 1.0,
      "recall": 1.0,
      "f1": 1.0
    },
    "shape": {
      "tp": 1,
      "predicted": 1,
      "reference": 1,
      "precision": 1.0,
      "recall": 1.0,
      "f1": 1.0
    },
    "size": {
      "tp": 1,
      "predicted": 1,
      "reference": 1,
      "precision": 1.0,
      "recall": 1.0,
      "f1": 1.0
    },
    "state": {
      "tp": 2,
      "predicted": 2,
      "reference": 2,
      "precision": 1.0,
      "recall": 1.0,
      "f1": 1.0
    }
  },
  "m3_by_status": {
    "retained": {
      "tp": 5,
      "predicted": 5,
      "reference": 5,
      "precision": 1.0,
      "recall": 1.0,
      "f1": 1.0
    },
    "removed": {
      "tp": 1,
      "predicted": 1,
      "reference": 1,
      "precision": 1.0,
      "recall": 1.0,
      "f1": 1.0
    },
    "added": {
      "tp": 1,
      "predicted": 1,
      "reference": 1,
      "precision": 1.0,
      "recall": 1.0,
      "f1": 1.0
    },
    "modified": {
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
  "m5_by_semantic_type": {
    "entity": {
      "cases": 3,
      "valid_labels": 3,
      "technical_failures": 0,
      "by_label": {
        "hallucinated": {
          "tp": 1,
          "predicted": 1,
          "reference": 1,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "supported": {
          "tp": 1,
          "predicted": 1,
          "reference": 1,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "uncertain": {
          "tp": 1,
          "predicted": 1,
          "reference": 1,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        }
      },
      "macro_f1": 1.0,
      "confusion": [
        {
          "reference": "hallucinated",
          "prediction": "hallucinated",
          "count": 1
        },
        {
          "reference": "supported",
          "prediction": "supported",
          "count": 1
        },
        {
          "reference": "uncertain",
          "prediction": "uncertain",
          "count": 1
        }
      ],
      "decided_coverage": 0.6666666666666666,
      "false_supported_rate": 0.0,
      "false_hallucinated_rate": 0.0,
      "reference_status": "assistant_visual_candidate_not_human_gold",
      "human_accuracy": null
    },
    "attribute": {
      "cases": 3,
      "valid_labels": 3,
      "technical_failures": 0,
      "by_label": {
        "hallucinated": {
          "tp": 1,
          "predicted": 1,
          "reference": 1,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "supported": {
          "tp": 1,
          "predicted": 1,
          "reference": 1,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        },
        "uncertain": {
          "tp": 1,
          "predicted": 1,
          "reference": 1,
          "precision": 1.0,
          "recall": 1.0,
          "f1": 1.0
        }
      },
      "macro_f1": 1.0,
      "confusion": [
        {
          "reference": "hallucinated",
          "prediction": "hallucinated",
          "count": 1
        },
        {
          "reference": "supported",
          "prediction": "supported",
          "count": 1
        },
        {
          "reference": "uncertain",
          "prediction": "uncertain",
          "count": 1
        }
      ],
      "decided_coverage": 0.6666666666666666,
      "false_supported_rate": 0.0,
      "false_hallucinated_rate": 0.0,
      "reference_status": "assistant_visual_candidate_not_human_gold",
      "human_accuracy": null
    }
  },
  "api_usage": {
    "m2": {
      "calls": 8,
      "returned_models": [
        "deepseek-v4-pro"
      ],
      "total_tokens": 18544,
      "sum_call_seconds": 29.937999999994645
    },
    "m3": {
      "calls": 4,
      "returned_models": [
        "deepseek-v4-pro"
      ],
      "total_tokens": 23223,
      "sum_call_seconds": 7.2510000000474975
    },
    "m5": {
      "calls": 6,
      "returned_models": [
        "deepseek-flash"
      ],
      "total_tokens": 11925,
      "sum_call_seconds": 10.609000000054948
    }
  },
  "independent_repeats": 1,
  "human_gold": false,
  "llm_calls_in_this_audit": 0
}
```

- 只读取已落盘结果；没有补调用、改参考或重跑语义模型。
- 本轮每条输入仅一次生成，不能报告独立重复稳定性。计数只反映候选符合度，尚未覆盖完整计划中的人工审计指标。
