# 修复与复测结果

固定原 20 图、40 条文本、60 条视觉候选事实。原响应、参考标签、类别规则和 8/8/6-shot 未改。修复版独立保存在 repair_v1，旧基线保持可复查。

## 独立模块结果

| 模块与口径 | 修复前/同期对照 | 修复后/补充语境 |
|---|---:|---:|
| M2，同一响应、同一实体词形计分器 F1 | 80.2% | 80.9% |
| M3，同一响应、固定候选事实联合 F1 | 88.5% | 93.1% |
| M3 技术未决事实 / 300 | 30 | 3 |
| M5，同期 60 条 Macro-F1 | 59.5% | 71.8% |
| M5，候选标签一致率 | 73.3% | 78.3% |
| M5，uncertain 召回 | 38.5% | 61.5% |

M2 只隔离错误提及，恢复 cloud、man、skateboarders 三个实体；有效实体仍参与对齐和视觉验证。原 71.7% 与词形口径 80.2% 的差异属于计分变化，不能算作本次修复提升。7 条非法 state 仍按原规则隔离。

M3 只拆开单侧批量行、合并相交纯 unresolved 集合。剩余 3 条技术未决在 303499 与 483723：主体未确定，属性却被声明新增/删除；保留冲突，不猜身份。

M5 同一模型、图片、命题、系统规则和 6-shot；仅 query 增加原文定位窗口及主体提及偏移。两种条件各一次，30/30 平衡先后顺序。历史 59.8% 仅作历史值，不作为同期对照。

配对结果：6 条由不符候选变为符合，3 条反向变化；共 10 条标签变化。候选一致率差的图像级配对 bootstrap 95% 区间为 -5.0 至 13.3 个百分点，包含零，不能据此宣称稳定显著提升。该区间不覆盖人工标签不确定性或模型跨次生成变动。

改善/退化仅指与冻结候选标签的符合度。比如 small tractor 从 supported 变 uncertain 的模型理由是无法确定主体为 tractor，原候选属性与主体之间已有一致性问题；不能直接认定这是模型新增错误。large bird 仍存在大小参照标准分歧。

## 视觉逐例复查

[完整 60 条对照 CSV](visual_case_review.csv) 保存命题、原文语境、候选理由、两个模型理由及改善/退化标记。以下列出所有发生标签变化的样本：

| ID | 命题 | 候选 | 原输入 | 补充语境 |
|---|---|---|---|---|
| 326667_v3 | The referenced bird is large. | uncertain | uncertain | supported |
| 352377_v3 | An entity or group described as "banana" is present in the image. | uncertain | hallucinated | uncertain |
| 195269_v3 | An entity or group described as "car" is present in the image. | uncertain | hallucinated | uncertain |
| 381925_v1 | An entity or group described as "dog" is present in the image. | supported | hallucinated | uncertain |
| 381925_v2 | An entity or group described as "remote control" is present in the image. | uncertain | hallucinated | uncertain |
| 54264_v2 | An entity or group described as "car" is present in the image. | uncertain | supported | uncertain |
| 256003_v3 | The referenced tractor is small. | supported | supported | uncertain |
| 450500_v2 | The referenced shirt is pink. | supported | uncertain | supported |
| 69946_v2 | An entity or group described as "car" is present in the image. | uncertain | uncertain | supported |
| 565761_v3 | An entity or group described as "bowl" is present in the image. | uncertain | hallucinated | uncertain |

## 端到端集成

| 统计 | 原版本 | 修复版本 |
|---|---:|---:|
| 原文/steer 事实数 | 147/114 | 148/116 |
| 技术未决事实 | 12 | 9 |
| 唯一视觉命题 | 196 | 199 |
| 属性/主体真值冲突 | 1 | 0 |
| 原文视觉supported实体删除 / 分母 | 34/99 | 32/99 |
| 原文视觉hallucinated实体删除 / 分母 | 8/10 | 4/6 |
| 原文视觉supported属性删除 / 分母 | 8/15 | 7/15 |
| 原文视觉hallucinated属性删除 / 分母 | 1/1 | N/A（分母为0） |

20 个 pair 已完成；视觉待处理 0 条。词数仍为 1914 → 908。集成同时含三项修复，统计变化不作单变量因果结论。

本轮合计新增 296 次 API 调用、632433 tokens；其中集成 M3 新调用 3 次、M5 新调用 173 次，缓存复用 43 次。M2 和独立 M3 修复复测新增调用为 0。

[端到端事实迁移表](end_to_end/m6/transitions.csv) · [每图指标及词数](end_to_end/m6/pair_metrics.csv) · [POS 切片](end_to_end/m6/pos_slices.csv) · [完整机器指标](metrics.json)

## 解释边界与下一变量

视觉参考是助手预先整理的候选标签，尚非独立人工 gold；Macro-F1 不是总体准确率。主体定位补齐能处理指代信息缺失，但不能自动解决 large、small、材质等证据边界。下一步应先盲审 uncertain 与 hallucinated 的边界及对应例子，形成独立版本；不在这批结果上修改标签来追求高分，也不同时换模型、换标签和换示例。

工程回归共 18 项通过（修复、缓存/输入隔离、原 pipeline 集成）；上述 9 个冻结 run 的代码与输入哈希复查通过。
