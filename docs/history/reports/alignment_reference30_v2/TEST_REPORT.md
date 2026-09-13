# 30 对 Alignment 参考标注测试

完成 30/30 对；API 请求 30/60。固定助手标注的事实输入，8-shot不变，不运行Decomposer或Coverage。参考由助手起草，未经用户审核。

| 指标 | Precision | Recall | F1 |
| --- | --- | --- | --- |
| alignment_edge | 0.00% | 0.00% | 0.00% |
| joint_edge_status | 0.00% | 0.00% | 0.00% |
| two_sided_edges_only | N/A | 0.00% | 0.00% |

无标签Edge使用两侧fact ID集合（含∅）作为边；联合指标另要求状态相同。多对多按整组一条边，不展开成笛卡尔积。技术失败计入分母但不获TP。two_sided为仅含两侧事实的辅助指标，不涵盖单侧删除/新增和技术回退。

| 状态（逐事实） | Reference support | Precision | Recall | F1 |
| --- | --- | --- | --- | --- |
| retained | 392 | N/A | 0.00% | 0.00% |
| removed | 241 | N/A | 0.00% | 0.00% |
| added | 141 | N/A | 0.00% | 0.00% |
| modified | 2 | N/A | 0.00% | 0.00% |
| ambiguous | 81 | N/A | 0.00% | 0.00% |

Status Macro-F1：0.00%。每个固定fact计一次；它不检查对应目标，因此必须与Edge F1一起读。

误删除率 FRR（确认仍完整表达）：0/0 = N/A。部分保留 0 条、不可裁决 0 条；把二者都算作误删除的上界为 N/A。

Removed Precision 检查参考状态是否为 removed；FRR 只检查原事实是否仍在对侧原句完整表达，因此二者不是无条件互补。modified、partial overlap 和身份不可裁决分别保留，不强行当作完整保留。

技术失败：857/857 = 100.00%。

所有错误保存在 errors.jsonl；每条预测removed的审核依据在 false_removal_audit.jsonl；原始请求响应在entities/alignments中。参考不发送给DeepSeek。只运行一次，不能据此估计重复稳定性。
