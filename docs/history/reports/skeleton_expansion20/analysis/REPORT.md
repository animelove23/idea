# 20图扩大测评：独立模块与真实端到端统计

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "images": 20,
  "captions": 40,
  "word_counts": {
    "original": 1914,
    "steer": 908,
    "mean_paired_percent_change": -53.072439633913845,
    "all_pairs_shorter": true
  },
  "m2": {
    "frozen_candidate_metrics": {
      "joint": {
        "tp": 201,
        "predicted": 261,
        "reference": 300,
        "precision": 0.7701149425287356,
        "recall": 0.67,
        "f1": 0.7165775401069518
      },
      "entity": {
        "tp": 173,
        "predicted": 222,
        "reference": 260,
        "precision": 0.7792792792792793,
        "recall": 0.6653846153846154,
        "f1": 0.7178423236514523
      },
      "attribute": {
        "tp": 28,
        "predicted": 39,
        "reference": 40,
        "precision": 0.717948717948718,
        "recall": 0.7,
        "f1": 0.7088607594936709
      }
    },
    "captions_needing_review": 9,
    "validation_issue_count": 12,
    "validation_reasons": {
      "source not found at requested occurrence": 5,
      "state outside frozen six-value vocabulary": 7
    },
    "overlapping_source_naming_flags": 32
  },
  "m3_independent": {
    "joint": {
      "tp": 166,
      "predicted": 180,
      "reference": 195,
      "precision": 0.9222222222222223,
      "recall": 0.8512820512820513,
      "f1": 0.8853333333333333
    },
    "pairs_needing_review": 10,
    "validation_issue_count": 32,
    "technical_fact_count": 30,
    "reference_fact_count": 300,
    "by_status": {
      "retained": {
        "tp": 59,
        "predicted": 62,
        "reference": 60,
        "precision": 0.9516129032258065,
        "recall": 0.9833333333333333,
        "f1": 0.9672131147540983
      },
      "removed": {
        "tp": 66,
        "predicted": 71,
        "reference": 74,
        "precision": 0.9295774647887324,
        "recall": 0.8918918918918919,
        "f1": 0.9103448275862069
      },
      "added": {
        "tp": 32,
        "predicted": 32,
        "reference": 41,
        "precision": 1.0,
        "recall": 0.7804878048780488,
        "f1": 0.8767123287671232
      },
      "modified": {
        "tp": 0,
        "predicted": 0,
        "reference": 0,
        "precision": null,
        "recall": null,
        "f1": null
      },
      "unresolved": {
        "tp": 9,
        "predicted": 15,
        "reference": 20,
        "precision": 0.6,
        "recall": 0.45,
        "f1": 0.5142857142857142
      }
    }
  },
  "m5_independent": {
    "cases": 60,
    "valid_labels": 60,
    "technical_failures": 0,
    "by_label": {
      "hallucinated": {
        "tp": 4,
        "predicted": 8,
        "reference": 7,
        "precision": 0.5,
        "recall": 0.5714285714285714,
        "f1": 0.5333333333333333
      },
      "supported": {
        "tp": 37,
        "predicted": 44,
        "reference": 40,
        "precision": 0.8409090909090909,
        "recall": 0.925,
        "f1": 0.8809523809523809
      },
      "uncertain": {
        "tp": 4,
        "predicted": 8,
        "reference": 13,
        "precision": 0.5,
        "recall": 0.3076923076923077,
        "f1": 0.38095238095238093
      }
    },
    "macro_f1": 0.5984126984126984,
    "confusion": [
      {
        "reference": "hallucinated",
        "prediction": "hallucinated",
        "count": 4
      },
      {
        "reference": "hallucinated",
        "prediction": "supported",
        "count": 1
      },
      {
        "reference": "hallucinated",
        "prediction": "uncertain",
        "count": 2
      },
      {
        "reference": "supported",
        "prediction": "hallucinated",
        "count": 1
      },
      {
        "reference": "supported",
        "prediction": "supported",
        "count": 37
      },
      {
        "reference": "supported",
        "prediction": "uncertain",
        "count": 2
      },
      {
        "reference": "uncertain",
        "prediction": "hallucinated",
        "count": 3
      },
      {
        "reference": "uncertain",
        "prediction": "supported",
        "count": 6
      },
      {
        "reference": "uncertain",
        "prediction": "uncertain",
        "count": 4
      }
    ],
    "decided_coverage": 0.8666666666666667,
    "false_supported_rate": 0.14285714285714285,
    "false_hallucinated_rate": 0.025,
    "reference_status": "assistant_visual_candidate_not_human_gold",
    "human_accuracy": null
  },
  "m5_by_type": {
    "entity": {
      "cases": 41,
      "valid_labels": 41,
      "technical_failures": 0,
      "by_label": {
        "hallucinated": {
          "tp": 3,
          "predicted": 7,
          "reference": 6,
          "precision": 0.42857142857142855,
          "recall": 0.5,
          "f1": 0.46153846153846156
        },
        "supported": {
          "tp": 24,
          "predicted": 28,
          "reference": 26,
          "precision": 0.8571428571428571,
          "recall": 0.9230769230769231,
          "f1": 0.8888888888888888
        },
        "uncertain": {
          "tp": 3,
          "predicted": 6,
          "reference": 9,
          "precision": 0.5,
          "recall": 0.3333333333333333,
          "f1": 0.4
        }
      },
      "macro_f1": 0.5834757834757834,
      "confusion": [
        {
          "reference": "hallucinated",
          "prediction": "hallucinated",
          "count": 3
        },
        {
          "reference": "hallucinated",
          "prediction": "supported",
          "count": 1
        },
        {
          "reference": "hallucinated",
          "prediction": "uncertain",
          "count": 2
        },
        {
          "reference": "supported",
          "prediction": "hallucinated",
          "count": 1
        },
        {
          "reference": "supported",
          "prediction": "supported",
          "count": 24
        },
        {
          "reference": "supported",
          "prediction": "uncertain",
          "count": 1
        },
        {
          "reference": "uncertain",
          "prediction": "hallucinated",
          "count": 3
        },
        {
          "reference": "uncertain",
          "prediction": "supported",
          "count": 3
        },
        {
          "reference": "uncertain",
          "prediction": "uncertain",
          "count": 3
        }
      ],
      "decided_coverage": 0.8536585365853658,
      "false_supported_rate": 0.16666666666666666,
      "false_hallucinated_rate": 0.038461538461538464,
      "reference_status": "assistant_visual_candidate_not_human_gold",
      "human_accuracy": null
    },
    "attribute": {
      "cases": 19,
      "valid_labels": 19,
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
          "tp": 13,
          "predicted": 16,
          "reference": 14,
          "precision": 0.8125,
          "recall": 0.9285714285714286,
          "f1": 0.8666666666666667
        },
        "uncertain": {
          "tp": 1,
          "predicted": 2,
          "reference": 4,
          "precision": 0.5,
          "recall": 0.25,
          "f1": 0.3333333333333333
        }
      },
      "macro_f1": 0.7333333333333334,
      "confusion": [
        {
          "reference": "hallucinated",
          "prediction": "hallucinated",
          "count": 1
        },
        {
          "reference": "supported",
          "prediction": "supported",
          "count": 13
        },
        {
          "reference": "supported",
          "prediction": "uncertain",
          "count": 1
        },
        {
          "reference": "uncertain",
          "prediction": "supported",
          "count": 3
        },
        {
          "reference": "uncertain",
          "prediction": "uncertain",
          "count": 1
        }
      ],
      "decided_coverage": 0.8947368421052632,
      "false_supported_rate": 0.0,
      "false_hallucinated_rate": 0.0,
      "reference_status": "assistant_visual_candidate_not_human_gold",
      "human_accuracy": null
    }
  },
  "end_to_end": {
    "facts": 261,
    "original_facts": 147,
    "steer_facts": 114,
    "unique_claims": 196,
    "verifications": 196,
    "labels": {
      "supported": 151,
      "uncertain": 29,
      "hallucinated": 16
    },
    "m3_pairs_needing_review": 3,
    "m3_validation_issues": 16,
    "truth_conflicts": 1,
    "original_transition_table": [
      {
        "type": "attribute",
        "status": "removed",
        "label": "hallucinated",
        "n": 1
      },
      {
        "type": "attribute",
        "status": "removed",
        "label": "supported",
        "n": 9
      },
      {
        "type": "attribute",
        "status": "retained",
        "label": "supported",
        "n": 6
      },
      {
        "type": "attribute",
        "status": "retained",
        "label": "uncertain",
        "n": 1
      },
      {
        "type": "attribute",
        "status": "unresolved",
        "label": "supported",
        "n": 1
      },
      {
        "type": "entity",
        "status": "removed",
        "label": "hallucinated",
        "n": 8
      },
      {
        "type": "entity",
        "status": "removed",
        "label": "supported",
        "n": 34
      },
      {
        "type": "entity",
        "status": "removed",
        "label": "uncertain",
        "n": 15
      },
      {
        "type": "entity",
        "status": "retained",
        "label": "hallucinated",
        "n": 2
      },
      {
        "type": "entity",
        "status": "retained",
        "label": "supported",
        "n": 52
      },
      {
        "type": "entity",
        "status": "retained",
        "label": "uncertain",
        "n": 4
      },
      {
        "type": "entity",
        "status": "unresolved",
        "label": "supported",
        "n": 13
      },
      {
        "type": "entity",
        "status": "unresolved",
        "label": "uncertain",
        "n": 1
      }
    ]
  },
  "fixed60_partial_end_to_end_check": {
    "targets": 60,
    "extraction_matched": 47,
    "truth_agrees": 37,
    "status_agrees": 41,
    "both_agree": 33,
    "scope": "Preselected candidate target subset; missing extraction stays in denominator; not full E2E precision/F1."
  },
  "usage": {
    "new_api_calls": 310,
    "end_to_end_api_calls": 190,
    "end_to_end_reused_results": 66,
    "new_tokens": 903074,
    "returned_models": [
      "deepseek-flash",
      "deepseek-v4-pro"
    ]
  },
  "bootstrap": {
    "unit": "image",
    "stratified_by": "original_caption_length_quartile",
    "repetitions": 2000,
    "seed": 1994,
    "interpretation": "Sampling uncertainty within this stratified 20-image development set; excludes judge/reference/systematic measurement error.",
    "rates": {
      "entity_true_removed": {
        "numerator": 34,
        "denominator": 99,
        "rate": 0.3434343434343434,
        "ci95": [
          0.27,
          0.41509833706427884
        ],
        "valid_resamples": 2000
      },
      "entity_true_retained": {
        "numerator": 52,
        "denominator": 99,
        "rate": 0.5252525252525253,
        "ci95": [
          0.419341053212021,
          0.63292194092827
        ],
        "valid_resamples": 2000
      },
      "entity_hallucinated_removed": {
        "numerator": 8,
        "denominator": 10,
        "rate": 0.8,
        "ci95": [
          0.5714285714285714,
          1.0
        ],
        "valid_resamples": 2000
      },
      "entity_hallucinated_retained": {
        "numerator": 2,
        "denominator": 10,
        "rate": 0.2,
        "ci95": [
          0.0,
          0.42857142857142855
        ],
        "valid_resamples": 2000
      },
      "attribute_true_removed": {
        "numerator": 8,
        "denominator": 15,
        "rate": 0.5333333333333333,
        "ci95": [
          0.2222222222222222,
          0.8181818181818182
        ],
        "valid_resamples": 2000
      },
      "attribute_true_retained": {
        "numerator": 6,
        "denominator": 15,
        "rate": 0.4,
        "ci95": [
          0.1426948051948052,
          0.6875
        ],
        "valid_resamples": 2000
      },
      "attribute_hallucinated_removed": {
        "numerator": 1,
        "denominator": 1,
        "rate": 1.0,
        "ci95": [
          1.0,
          1.0
        ],
        "valid_resamples": 1362
      },
      "attribute_hallucinated_retained": {
        "numerator": 0,
        "denominator": 1,
        "rate": 0.0,
        "ci95": [
          0.0,
          0.0
        ],
        "valid_resamples": 1362
      }
    }
  },
  "human_gold": false,
  "independent_repeats": 1,
  "causal_conclusions": false
}
```

- 候选参考均在对应模型调用前编写；未根据输出更改答案。所有F1均是候选符合度，非独立人工准确率。
- 程序/提示词/模型/few-shot保持基线；仅新增固定真实输入。技术问题保留，未自动修复或重试。
- M3独立测评使用固定参考事实；端到端M3使用实际M2输出，两者输入不同，分数不能直接当模块能力变化。
- 60条视觉候选为按图预选的诊断命题，不是自然分布；端到端60目标检查不代表全链精确率。
- 图像级区间只反映本开发样本的抽样变动，不能覆盖模型判断与候选参考误差；不支持steering因果结论。
