# M2坏提及局部隔离：固定响应重放

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "before": {
    "joint": {
      "tp": 225,
      "predicted": 261,
      "reference": 300,
      "precision": 0.8620689655172413,
      "recall": 0.75,
      "f1": 0.8021390374331551
    },
    "entity": {
      "tp": 196,
      "predicted": 222,
      "reference": 260,
      "precision": 0.8828828828828829,
      "recall": 0.7538461538461538,
      "f1": 0.8132780082987552
    },
    "attribute": {
      "tp": 29,
      "predicted": 39,
      "reference": 40,
      "precision": 0.7435897435897436,
      "recall": 0.725,
      "f1": 0.7341772151898734
    }
  },
  "after": {
    "joint": {
      "tp": 228,
      "predicted": 264,
      "reference": 300,
      "precision": 0.8636363636363636,
      "recall": 0.76,
      "f1": 0.8085106382978723
    },
    "entity": {
      "tp": 199,
      "predicted": 225,
      "reference": 260,
      "precision": 0.8844444444444445,
      "recall": 0.7653846153846153,
      "f1": 0.8206185567010309
    },
    "attribute": {
      "tp": 29,
      "predicted": 39,
      "reference": 40,
      "precision": 0.7435897435897436,
      "recall": 0.725,
      "f1": 0.7341772151898734
    }
  },
  "restored_facts": 3,
  "captions_with_recovered_mentions": 3,
  "new_api_calls": 0
}
```

- 主比较两边固定同一词形计分器；仅改变提及校验粒度。
- 保留错误原文及隔离日志，不猜引文、不改变state边界；不是独立模型重复。
