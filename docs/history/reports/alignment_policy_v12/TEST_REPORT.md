# v1.2 校验器离线回放

回放同一批历史模型响应，不调用API。不能证明新提示词更好，也不是新的few-shot实验。两边都使用用户已裁定发球/数量两例后的同一份reference，其余参考仍待审核。

| 指标 | 旧校验 | 新校验 |
| --- | --- | --- |
| Edge F1 | 83.63% | 90.63% |
| 联合F1 | 78.81% | 85.46% |
| Status Macro-F1 | 61.31% | 64.48% |
| Removed Precision | 95.48% | 95.54% |
| 确认误删除率 | 1.01% | 0.89% |
| 误删除保守上界 | 4.52% | 4.46% |
| 技术回退率 | 9.10% | 3.03% |

有29条保存的事实响应。264423的实体候选组现在可以恢复，但当时没有发出事实请求；本次没有编造结果，仍保留其26条技术回退记录。

技术回退下降部分来自把语义问题改为保留配对的semantic_reviews，而不是模型能力变化。语义待审即使与参考ambiguous同标签，也必须连同原始模型提议查看，不能声称模型自己判断正确。

## 语义审查规则次数

```json
{
  "count_scope_changed": 1,
  "unresolved_correspondence_identity": 3,
  "unresolved_existence_identity": 1,
  "participant_roles_or_scope_changed": 2,
  "different_attribute_dimensions": 1
}
```

全部事实变化见changes.jsonl；原始旧实验、参考和预测均未覆盖。新提示词尚未做实时测试。
