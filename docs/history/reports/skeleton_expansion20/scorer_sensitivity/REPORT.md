# M2实体词形还原的计分敏感性检查

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "baseline": {
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
  "lemma_entity_names": {
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
  "primary_run_unchanged": true,
  "llm_calls": 0,
  "post_hoc": true
}
```

- 只改变实体名称/存在事实值的词形规范化；来源重叠、一对一匹配、属性值、主体绑定规则保持不变。
- 该诊断用于揭示计分器敏感性，不作为模型改进、不替换原F1、不将新增匹配自动视为人工确认正确。
- 群体/个体拆分、部分与整体、train/model train等语义范围仍未解决；需独立审核。
