# 对齐 v1.3：四类可判定变化 + other

默认下游入口 `python -m evaluation.run` 使用 `alignment_core.PairAligner`。历史 `alignment.py` 校验/分组实现保留，供旧实验和兼容测试使用。v6 Decomposer、caption 和 facts 不改写。

- retained：同一完整命题，仅同义表达。
- modified：同一确定主体/事件、同一信息维度，值、具体程度、事件阶段、语气或关系目标改变；一对一。人物身份确定时，类别指定的具体化/泛化也可计入。
- removed / added：完整对侧 caption 不再/新表达该命题。颜色不再提及是颜色 removed，而不是 modified；材质转为颜色是不同信息的删除/新增。
- other：身份不明、拆分遗漏、粒度不兼容、来源不可靠、或事实类型为 other。保留审计，不计入事实增减主线。

实体 sidecar 的 ambiguous 仍表示身份候选不确定；它与公开的 Fact Alignment 状态分开。程序不会把整个 caption 因某个未知人物而全部排除，新增属性可以在不确定人物身份时照常判 added。

保留程序的来源/ID/唯一主计数校验。对于同一主体的同维度关系修改，允许参照目标变化；不允许 retained 偷换目标。数字变化仍要求计数范围相同。程序触发的 other 带 semantic_guard/model_proposal；技术错误带 stage_failed/alignment_validation_error，均不当作模型成功判断。

8-shot 新版在 `examples/alignment_core.jsonl`；旧版不覆盖。新示例只用合成 caption，未加入本次真实测试 caption。新参考在 `annotation/alignment_v13`，逐项修订记录可查；它是助手标注，不是完整人工金标准。

## 评估与排除

同时报告：

1. 主线四类 Edge P/R/F1、联合 Edge+Status F1、四类状态 Macro-F1。
2. 全量五类指标，包含 other；技术失败不能作为 other 的正确预测得分。
3. 模型 other 排除率，区分语义排除与技术失败；参考 other 比例。
4. 参考可判定但被模型排除的数量/比例。模型排除不能从 gold 分母中删除：仍是主线漏报；把 gold-other 硬判为主线也计入误报。
5. Removed Precision、确认 FRR 及部分保留上界。

因此不会用“只在双方都没有 other 的小集合上评分”的方式美化性能。主线四类 Macro-F1 与旧五类 Macro-F1 不是同一个指标；对照时统一使用新参考、新计分函数。旧预测仅将 ambiguous 机械映射到 other，不能按新 gold 改成 modified。
