# M2 固定8-shot独立分解测评

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "calls": 8,
  "summary": {
    "joint": {
      "tp": 37,
      "predicted": 38,
      "reference": 37,
      "precision": 0.9736842105263158,
      "recall": 1.0,
      "f1": 0.9866666666666667
    },
    "entity": {
      "tp": 24,
      "predicted": 25,
      "reference": 24,
      "precision": 0.96,
      "recall": 1.0,
      "f1": 0.9795918367346939
    },
    "attribute": {
      "tp": 13,
      "predicted": 13,
      "reference": 13,
      "precision": 1.0,
      "recall": 1.0,
      "f1": 1.0
    }
  },
  "technical_failures": 0,
  "by_split": {
    "real_development": {
      "joint": {
        "tp": 24,
        "predicted": 25,
        "reference": 24,
        "precision": 0.96,
        "recall": 1.0,
        "f1": 0.9795918367346939
      },
      "entity": {
        "tp": 18,
        "predicted": 19,
        "reference": 18,
        "precision": 0.9473684210526315,
        "recall": 1.0,
        "f1": 0.972972972972973
      },
      "attribute": {
        "tp": 6,
        "predicted": 6,
        "reference": 6,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      }
    },
    "synthetic_boundary_development": {
      "joint": {
        "tp": 13,
        "predicted": 13,
        "reference": 13,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "entity": {
        "tp": 6,
        "predicted": 6,
        "reference": 6,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      },
      "attribute": {
        "tp": 7,
        "predicted": 7,
        "reference": 7,
        "precision": 1.0,
        "recall": 1.0,
        "f1": 1.0
      }
    }
  },
  "independent_human_accuracy": null,
  "reference_status": "assistant_candidate_not_gold"
}
```

- 先冻结参考/示例/代码再请求；没有自动修复或重试，没有视觉/POS输入。
- 指标是相对预写候选参考的确定性匹配，主体依据名称及原文span；有限同义词表可能漏计等义表达，需审阅差异。
- 真实样本与合成边界分开，不将候选符合度当独立人工准确率；技术失败仍计参考漏报。
