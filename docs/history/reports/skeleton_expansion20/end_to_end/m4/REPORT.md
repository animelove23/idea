# M4 验证队列与词语关联

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "pairs": 20,
  "input_facts": 261,
  "backfill_refs": 261,
  "queue_coverage": 1.0,
  "unique_claims": 196,
  "shared_claims": 65,
  "span_link_rate": 1.0,
  "image_manifest_available": 196,
  "llm_calls": 0
}
```

- 结构覆盖率不证明主体对应或视觉命题正确；缺图不会删除事实名册。
