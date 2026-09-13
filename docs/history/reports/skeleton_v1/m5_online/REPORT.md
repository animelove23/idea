# M5 固定6图文few-shot视觉测评

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "cases": 6,
  "valid_labels": 6,
  "technical_failures": 0,
  "by_label": {
    "hallucinated": {
      "tp": 2,
      "predicted": 2,
      "reference": 2,
      "precision": 1.0,
      "recall": 1.0,
      "f1": 1.0
    },
    "supported": {
      "tp": 2,
      "predicted": 2,
      "reference": 2,
      "precision": 1.0,
      "recall": 1.0,
      "f1": 1.0
    },
    "uncertain": {
      "tp": 2,
      "predicted": 2,
      "reference": 2,
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
      "count": 2
    },
    {
      "reference": "supported",
      "prediction": "supported",
      "count": 2
    },
    {
      "reference": "uncertain",
      "prediction": "uncertain",
      "count": 2
    }
  ],
  "decided_coverage": 0.6666666666666666,
  "false_supported_rate": 0.0,
  "false_hallucinated_rate": 0.0,
  "reference_status": "assistant_visual_candidate_not_human_gold",
  "human_accuracy": null
}
```

- 发送实际原图；query不包含参考标签、模型来源或对齐状态；图片哈希随run冻结。
- 参考是助手看图后预写的候选标签，不是独立人工gold；本轮不能据此宣称真实准确率。
- 模型由官方图像指南选择deepseek-flash，返回模型标识逐请求保存；没有文本替代或多模型投票。
