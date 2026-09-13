# Coverage / Alignment 首轮有效请求测试

4 对既有真实 Vanilla–Steer 样本；直接使用先前独立生成的 v6 结果。Decomposer、few-shot、原始事实未修改。请求格式修复后的本轮发出 15 次请求，全部关闭思考；无语义规则调参或自动修复。此前 HTTP 格式失败记录在 ../real_run 保留，不并入语义统计。

## 结果

| 项目 | 结果 |
| --- | --- |
| Coverage | 8/8 完成，新增 1 条 |
| 实体对应 | 3/4 通过结构校验，1 对失败 |
| 事实对应 | 1 对 ready，2 对 needs_review，1 对跳过并回退 |
| 主线 alignment 行数 | retained 16，removed 11，added 2，modified 3，ambiguous 28 |
| 全量 alignment 行数（含 other） | retained 16，removed 16，added 2，modified 3，ambiguous 31 |
| 视觉验证 | 87 条全部 pending |
| 实际 extraction_gap | 0 条；不能据此认为系统没有漏拆 |

这些是状态分布，不是准确率。技术失败回退不算模型正确识别了 ambiguous；具体原因数量见 integrity_check.json。ready 仅表示结构校验通过，不保证语义正确。

## 实际例子和失败

- Coverage：299573_vanilla 从原文“tall grass”补充 attribute “The grass is tall.”，保留原有全部事实。
- 实体对应：花瓶 pair 中 vase、flowers、table、window 建立了对应；完整 sidecar 见 entity_alignment.jsonl 和 DETAIL_REPORT.md。
- removed / added：鞋子 pair 的“The shoes seem to be old.”被判 removed，“Both pairs of shoes are black.”被判 added，未将 age 与 color 合成 modified。花瓶 pair 的 made of glass 被判 added。
- retained：花瓶 pair 的 table existence、window existence、vase on table 得到保留对应。
- modified：长颈鹿 pair 的“one giraffe positioned slightly behind the other”与“stand side by side”被模型视为相对位置变化。仍需人工判断实体集合与粒度是否足够一致。
- 主体混淆被拦截：花瓶靠近窗户 ↔ 桌子靠近窗户被模型误判 modified，因 global participants 不同回退 ambiguous。
- 581451 实体步骤失败：模型把 paper、napkin 两个实体放进一个 original_only 行，违反该状态单实体契约。本版保留错误，不自动拆行；22 条事实回退 stage_failed。
- 鞋子 pair：模型引用“The shoes seem to be worn”作为证据，但它不是原文的连续片段，校验拒绝并回退 ambiguous。
- 原有事实粒度影响：entity “There is a vase.” ↔ “There is a glass vase.”被判 modified，而 glass 还有独立 attribute。entity “dried flowers” ↔ “flowers”也被判 modified。这些需要人工裁定，存在实体/属性重复计数风险；本版不重写 Decomposer 来掩盖它。
- 初步语义审查发现疑似误报删除：长颈鹿原文“standing close to each other”被判 removed，但 Steer 的“side by side”很可能仍表达相近语义。这应列入人工审核，可能是 retained、partial_overlap 或 extraction_gap，不能直接作为可靠的信息删除；本报告没有将助手审查当成人工 gold。
- Coverage 局限：花瓶 caption 的 dried 仍未得到独立 attribute；本轮补充少不代表已完全覆盖。

没有观察到实际 extraction_gap。受控同文漏拆案例保存在 ../local_contract_examples.json，明确属于本地测试，不能充当真实模型发现。

## 指标与审核

主指标采用人工 reference 下的“配对事实集合 + 状态”联合 Precision/Recall/F1；同时报告各状态 F1、Macro-F1、误报删除率和 extraction_gap P/R/F1。当前无人工对齐 gold，不输出准确率。详细口径见 [METRICS.md](../../../evaluation/METRICS.md)。

完整对应、removed/added 具体事实、每侧事实计数、原始响应和拒绝记录分别在 DETAIL_REPORT.md、alignment.jsonl、summary.json 及中间目录中。所有原始文档不变、事实恰好分配一次、冻结代码/提示词未变、验证全部 pending，已通过完整性检查。
