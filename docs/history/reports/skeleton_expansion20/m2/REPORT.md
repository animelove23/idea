# M2 固定8-shot独立分解测评

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "calls": 40,
  "summary": {
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
  "technical_failures": 0,
  "by_split": {
    "real_development_expansion": {
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
    }
  },
  "independent_human_accuracy": null,
  "reference_status": "assistant_candidate_not_gold"
}
```

- 先冻结参考/示例/代码再请求；没有自动修复或重试，没有视觉/POS输入。
- 指标是相对预写候选参考的确定性匹配，主体依据名称及原文span；有限同义词表可能漏计等义表达，需审阅差异。
- 真实样本与合成边界分开，不将候选符合度当独立人工准确率；技术失败仍计参考漏报。
