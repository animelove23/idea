# M5 固定6图文few-shot视觉测评

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
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
}
```

- 发送实际原图；query不包含参考标签、模型来源或对齐状态；图片哈希随run冻结。
- 参考是助手看图后预写的候选标签，不是独立人工gold；本轮不能据此宣称真实准确率。
- 模型由官方图像指南选择deepseek-flash，返回模型标识逐请求保存；没有文本替代或多模型投票。
