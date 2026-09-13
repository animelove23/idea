# 实现合同与指标口径 v1

本合同与 [模块规划](../refine-logs/MODULE_BUILD_PLAN.md) 对应。粗粒度是词语/POS记录；细粒度是语义事实。只纳入明确肯定的 entity 与 attribute。属性槽固定 color、material、size、shape、state；state 首版只含 open/closed/wet/dry/broken/intact。动作、关系、数量、评价、推测和否定进入排除/审核记录，排除不表示幻觉。

## 身份、证据与词语关联

`caption_id → entity_id → fact_id` 只在对应 caption 内唯一。跨侧连接必须带 `side`，跨图必须带 `pair_id`。实体存在事实由程序从实体锚点生成；属性显式引用 entity_id。

模型输出 `quote + occurrence`，occurrence 是原文中从 0 起的精确匹配次序，程序求 `[start,end)` 字符区间。原词由文本切片验证；引文不存在时局部隔离，不猜偏移。`source_spans` 保存命题来源，`value_spans` 只定位属性值或实体提及；M4 用 value_spans 与 M1 token 区间相交。M6 保存所有位置，后续若使用“首次位置”应取最小值并另记重复提及次数。

`wooden table` 产生 table 实体及 material=wood；wooden 是 ADJ 但属性不是由 ADJ 推断。`table made of wood` 的 wood 是 NOUN，仍属于材质属性。词面重复由 Counter 记录；同一语义实体的多次提及由 M2 锚点合并。当前没有保证所有指代/重复提及都被模型完整抽取。

## 对齐和视觉状态

| 状态 | 合同 |
|---|---|
| retained | 确定同主体，完整等义事实，1:1 |
| removed | 原侧有，对侧未表达，1:0；主体也不确定时不能直接 removed |
| added | 新侧新增，0:1；主体也不确定时不能直接 added |
| modified | 确定同主体、同属性 slot 的明确值变化，1:1；不用于实体类变化 |
| unresolved | 主体、粒度、抽取缺口或技术问题未确定；原因分别记录 |

跨 slot 变化为 removed+added。removed 附 `entity_absent` 或 `attribute_omitted`。同侧 ID 缺失/重复只隔离受影响项，每个剩余 fact 仍分配一次。技术补齐的 unresolved 不得获得“正确未决”分。

M4 对 retained 共享一次视觉验证；modified 分别验证前后。M5 只接收原图、待验命题、必要主体语境和固定图文示例，隐藏方法名、迁移状态及测试参考标签。

| 视觉标签 | 含义 |
|---|---|
| supported | 图像明确支持指定主体和命题 |
| hallucinated | 图像明确否定主体存在或与指定属性矛盾 |
| uncertain | 证据不足、定位不明确等语义未决 |
| pending / 技术失败 | 尚未得到可用视觉判断，独立于三类标签 |

参考 [FaithScore 论文](https://aclanthology.org/2024.findings-emnlp.290/) 的逐原子事实图像核验。三值标签是本项目扩展，不称原版 FaithScore 复现。主体名字和原文提及只是待定位主张，不当作图像真值。多个同类主体的定位语境充分性尚需真实样本测评。

## 计分与固定分母

M2 用主体名的冻结规范化及来源 span 重叠建立主体对应，再检查事实主类、slot、value 和主体的一致性；一对一匹配，每个参考最多得一次 TP。此计分器只有有限同义表，不能等价于人工语义判断。FP/FN 保留完整原事实供审核。

M3 Edge 分数评价两侧 fact ID 组合，联合分数再加入 status；实体对应单独评价。未决和技术失败都保留参考分母。确认误删除只统计候选明确 retained 的事实被预测 removed，不能把它与 1−Removed Precision 混为一谈；复杂 modified/gap 场景仍需人工复核对侧是否表达。

M5 报三类 P/R/F1、混淆矩阵、已决定覆盖率、误判真/假率。无支持样本且无预测的类别记 N/A，Macro-F1 不补零伪造完整覆盖。技术失败单列；uncertain 的覆盖损失与判断错误并列。

M6 中“true/hallucinated”均指视觉模型标签，不是人工事实。对原侧某类被判 supported 且无上下文矛盾的 N 条事实，确认删除下界 D/N，上界 (D+U)/N，其中 U 为迁移 unresolved 数；modified 独立统计。这一区间不覆盖视觉 uncertain 的未知真假。视觉 uncertain、pending 和“属性 supported 但主体 hallucinated”的冲突单独列出，不默默删除或改判。

实体仍有确定对应时，另算真实属性 retained/N 和 (retained+unresolved)/N；同时保留全部原侧属性统计，避免幸存对象偏差。零分母始终 N/A。POS 切片可能一 fact 属多个词性，成员数不能相加当作事实总数。输出词数是 spaCy 非标点、非空白 token 数；没有生成 tokenizer 记录，模型 token 长度和 EOS/停止原因保持 unknown。

## 测评边界

本轮所有参考均为助手事先起草的候选，未经独立人工确认。工程测试通过、模型候选符合度、真实准确率三者分别报告。当前不做 held-out 或稳定性声明；不从文本缩短推断 EOS、抑制或注意力变化的因果机制。完整待实施指标清单保留在模块规划中，本版报告逐项说明缺口。
