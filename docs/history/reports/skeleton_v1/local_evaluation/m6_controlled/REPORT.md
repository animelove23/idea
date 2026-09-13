# M6 迁移统计与导出

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "pairs": 4,
  "fact_rows": 15,
  "queue_claims": 10,
  "verification_records": 10,
  "truth_counts": {
    "supported": 14,
    "hallucinated": 1
  },
  "original_attribute_removal_reasons": {
    "attribute_omitted": 1
  },
  "modified_truth_transitions": {
    "supported -> supported": 1
  },
  "truth_conflicts": 0,
  "llm_calls": 0,
  "synthetic_truth": true,
  "research_conclusion_validated": false
}
```

- synthetic_truth=true时，所有真假分布仅用于手算校验，不能作为模型现象。
- POS表为fact在不同词性中的成员数，一条fact可能跨多个POS，不能相加当总事实数。
- pending包含未执行或失败；uncertain为已执行的视觉证据不足。两者都不当幻觉。
- 当前导出按pair统计；同图不同生成条件须分开实验，不能作为独立图像做推断。
