# M3格式规范化：固定事实与固定响应重放

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "before": {
    "joint": {
      "tp": 166,
      "predicted": 180,
      "reference": 195,
      "precision": 0.9222222222222223,
      "recall": 0.8512820512820513,
      "f1": 0.8853333333333333
    },
    "technical_facts": 30
  },
  "after": {
    "joint": {
      "tp": 183,
      "predicted": 198,
      "reference": 195,
      "precision": 0.9242424242424242,
      "recall": 0.9384615384615385,
      "f1": 0.9312977099236641
    },
    "technical_facts": 3
  },
  "new_api_calls": 0,
  "rows_with_canonicalization": 8
}
```

- 只拆开已声明的单侧新增/删除批量行，合并相交的纯unresolved集合；不推断任何确定实体匹配。
- 冲突、非法ID、跨槽/不同主体仍走原隔离器。参考答案和输入事实不变。
