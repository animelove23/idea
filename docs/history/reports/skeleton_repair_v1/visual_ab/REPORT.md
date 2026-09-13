# M5 主体语境单变量同期对照

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "control": {
    "cases": 60,
    "valid_labels": 60,
    "technical_failures": 0,
    "by_label": {
      "hallucinated": {
        "tp": 4,
        "predicted": 9,
        "reference": 7,
        "precision": 0.4444444444444444,
        "recall": 0.5714285714285714,
        "f1": 0.5
      },
      "supported": {
        "tp": 35,
        "predicted": 39,
        "reference": 40,
        "precision": 0.8974358974358975,
        "recall": 0.875,
        "f1": 0.8860759493670886
      },
      "uncertain": {
        "tp": 5,
        "predicted": 12,
        "reference": 13,
        "precision": 0.4166666666666667,
        "recall": 0.38461538461538464,
        "f1": 0.4
      }
    },
    "macro_f1": 0.5953586497890295,
    "confusion": [
      {
        "reference": "hallucinated",
        "prediction": "hallucinated",
        "count": 4
      },
      {
        "reference": "hallucinated",
        "prediction": "uncertain",
        "count": 3
      },
      {
        "reference": "supported",
        "prediction": "hallucinated",
        "count": 1
      },
      {
        "reference": "supported",
        "prediction": "supported",
        "count": 35
      },
      {
        "reference": "supported",
        "prediction": "uncertain",
        "count": 4
      },
      {
        "reference": "uncertain",
        "prediction": "hallucinated",
        "count": 4
      },
      {
        "reference": "uncertain",
        "prediction": "supported",
        "count": 4
      },
      {
        "reference": "uncertain",
        "prediction": "uncertain",
        "count": 5
      }
    ],
    "decided_coverage": 0.8,
    "false_supported_rate": 0.0,
    "false_hallucinated_rate": 0.025,
    "reference_status": "assistant_visual_candidate_not_human_gold",
    "human_accuracy": null,
    "agreement": 0.7333333333333333
  },
  "context": {
    "cases": 60,
    "valid_labels": 60,
    "technical_failures": 0,
    "by_label": {
      "hallucinated": {
        "tp": 4,
        "predicted": 4,
        "reference": 7,
        "precision": 1.0,
        "recall": 0.5714285714285714,
        "f1": 0.7272727272727273
      },
      "supported": {
        "tp": 35,
        "predicted": 40,
        "reference": 40,
        "precision": 0.875,
        "recall": 0.875,
        "f1": 0.875
      },
      "uncertain": {
        "tp": 8,
        "predicted": 16,
        "reference": 13,
        "precision": 0.5,
        "recall": 0.6153846153846154,
        "f1": 0.5517241379310345
      }
    },
    "macro_f1": 0.7179989550679206,
    "confusion": [
      {
        "reference": "hallucinated",
        "prediction": "hallucinated",
        "count": 4
      },
      {
        "reference": "hallucinated",
        "prediction": "uncertain",
        "count": 3
      },
      {
        "reference": "supported",
        "prediction": "supported",
        "count": 35
      },
      {
        "reference": "supported",
        "prediction": "uncertain",
        "count": 5
      },
      {
        "reference": "uncertain",
        "prediction": "supported",
        "count": 5
      },
      {
        "reference": "uncertain",
        "prediction": "uncertain",
        "count": 8
      }
    ],
    "decided_coverage": 0.7333333333333333,
    "false_supported_rate": 0.0,
    "false_hallucinated_rate": 0.0,
    "reference_status": "assistant_visual_candidate_not_human_gold",
    "human_accuracy": null,
    "agreement": 0.7833333333333333
  },
  "paired": {
    "improved": 6,
    "regressed": 3,
    "label_changed": 10
  }
}
```

- 60个固定候选标签，双条件各一次；不是人工准确率，也不宣称跨重复稳定。
- 图片、命题、模型、温度、系统规则、6-shot相同；只改变query的entity_context。
- source window是定位线索，不是视觉真值证据；不将原文关系加入计分事实。
