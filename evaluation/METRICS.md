# Alignment 评估口径（待人工审核 reference）

v1.1：联合对齐指标以主 `fact_alignment` 的组为单位。真正等义重复事实组成的一行只算一个对应，不将多对一展开成多次TP；`related_correspondences` 是限定差异的上下文引用，不计第二次主对齐。原fact的状态覆盖仍逐fact报告。旧版与v1.1若计数单位不同，必须使用相同的新组级reference重算，不能直接将历史行数当准确率比较。

## Ground truth

固定同一批 caption、Coverage 后事实及 ID。人工同时阅读两侧完整原文与事实，标注实体对应、事实对应和状态；允许 ambiguous 多对多，并为 extraction_gap 写出对侧原文证据。不能以模型预测、视觉真假或 VISTA 应该更好的假设决定 reference。助手可以起草标签，但未经用户审核只能称为候选参考，不能称为人工 gold。

测试 Alignment 本身时，预测与 reference 必须使用同一份固定输入事实。Coverage 的漏补/错补另行评价，避免把输入变化当成 Alignment 性能变化。另设端到端评估时明确说明包括 Decomposer 和 Coverage 的误差。

## 主指标

1. **事实对应 + 状态的联合 Precision/Recall/F1**。每个对应表示为 `(pair_id, sorted(original_fact_ids), sorted(steer_fact_ids), status)`，ID 顺序不影响判断。两侧事实集合和状态都与人工 reference 一致才计 TP；多对多不能拆成大量正确链接来抬高分数。P=TP/预测行数，R=TP/reference 行数。对粒度争议单列分析，不自动放宽 gold。
2. **五种状态 Macro-F1**。分别计算 retained/removed/added/modified/ambiguous 的联合 F1 后宏平均。同时给每类 support 与 P/R/F1。没有预测和参考样本的类别为 N/A，报告实际参与宏平均的类别数；不要伪装成完整五类结果。
3. **误报删除率**。在预测 removed 的原侧事实中，人工阅读对侧原文后确认仍被表达的比例。分子包括漏拆、同义表达、粒度变化导致的错误删除；身份本来无法确定的案例另列不可裁决，不能默认为真删除。报告分子/分母，零个 predicted removed 时 N/A。与 `1 − removed precision` 不完全相同，后者还包括其他状态错误。
4. **extraction_gap Precision/Recall/F1**。以 `(pair_id, side, fact_id)` 评估原因标签，人工 reference 必须有对侧原文证据，不能仅因为对侧 fact 列表缺失就标 gap。

主线指标只统计 v6 entity/relation/attribute。含 other 与主线事实的混合 ambiguous 行保留为整体评估，并单列数量，不将它拆成主线正确行；other-only 结果单独报告。

## 辅助指标

- 原侧/Steer 侧各自的状态准确率与混淆矩阵：每个 fact 只计算一次。它不检查配对对象，不能代替联合 F1。
- ambiguous 事实比例和原因分布：按两侧事实分别计数。比例低并不等于质量好。成功判断覆盖率与已判断部分的错误率一起看，防止全部 ambiguous 获得虚假安全感。
- 每个事实恰好分配一次、失败请求、校验拒绝率：工程完整性指标，不是语义准确率。stage_failed / alignment_validation_error 是技术失败，单列；不能因人工 gold 也 ambiguous 就给它语义正确分。
- 重复一致性：未来独立重复调用时，在固定事实输入上比较每个 fact 的状态及对应目标集合。仅换 gN 或 entity 本地 ID 不算变化。缓存回放不算重复实验，本次 16 请求预算不包含重复实验。
- 实体对应正确率：单独人工检查 sidecar，用于定位错误来源；优先报告错误数和受影响事实数。

## 当前 4 对样本

仅属于小样本功能测试。没有人工对齐 gold，因此只能报告模型状态分布、技术失败、具体案例。不得输出名为准确率的自评数字。即使人工审核完 4 对，也仅代表这 4 对；扩大测试集后按 caption pair 为单位估计区间，不能把同一 caption 的多个事实当作独立样本夸大置信度。
