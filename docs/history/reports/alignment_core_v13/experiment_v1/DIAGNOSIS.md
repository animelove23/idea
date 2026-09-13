# v1.3 复测诊断（运行后分析，不改冻结参考或指标）

30对均已纳入，58次API调用均有响应；2对实体阶段失败，1对事实绑定阶段失败。其余27对有事实对齐结果。145项本地测试通过，运行期间代码/输入/参考哈希未变。

## 主要退化来自整对技术失败

| pair | 原因 | 受影响的两侧事实数 |
| --- | --- | --- |
| 559550 | 实体 original_only 行使用多个实体，违反当前单实体行接口 | 31 |
| 443218 | 实体 mention 不是对应 caption 的实际连续片段 | 37 |
| 303713 | Fact binding 引用不存在的 s6 / s7，实体 sidecar 只有 s1 至 s5 | 37 |

共105/857事实（12.25%）进入技术失败排除，而非模型正确判定的语义 other。不能将这些失败算成正确 other，也不能从召回率分母剔除。当前整对失败的粒度过大，是后续应优先改进的工程问题；本次没有自动补造ID或循环重试。

## 新口径确实识别了一部分明确变化

- 319726：serves the ball → prepares to serve a ball，modified。
- 142826：several people → a few people，modified。
- 469134：at least nine motorcycles → several motorcycles，modified。
- 46912：significant portion → most of the scene，modified。

与此同时，341389仍把13人总数与12名滑雪者配成 modified；程序因计数范围不同转成 other。新参考是 removed + added，这仍是错配/漏报，不是保护规则使其自动正确。

## 参考标注的迁移还存在需要审核的边界

本次新参考逐项重审了旧 ambiguous/modified 以及旧摩托车计数删除/新增边，但并未人工全面重审全部600余组其他标签。运行后检查发现部分继承的旧标签可能与扩大的 modified 定义不一致：

- 4157：clock above shelf → clock above glasses/bottles，模型为 modified，旧参考继承 removed + added。新规则允许确定主体的同类关系换目标；需要检查实体对应和复合目标，不能直接认定模型错。
- 46912：people scattered around station → throughout train，模型为 modified，参考仍为 removed + added。需裁定是否同一群体同一位置维度。
- 264423：people fly a kite → watch a kite，模型为 modified，参考仍为 removed + added。需统一“同一主体的活动改变”与“两个独立活动”的边界。
- 458778：kitchen → kitchenette，模型为 modified，参考 retained。需裁定场景中的称谓是否语义等价还是类别具体化。

为避免看完预测后追改答案抬分，以上没有回填冻结参考。本次 Precision/F1 都是相对于本轮助手参考的符合度，不能直接当作经人工确认的最终准确率。这些候选差异同时保存在完整原句/参考/预测表，可供用户审阅。

## 排除率与可比性

语义 other 从旧预测104条降到61条；加上技术失败后，总排除从143条升至166条。参考主线818条中，147条被错误排除。只看语义 other 减少会掩盖实际损失。

新旧预测均在同一新参考、同一计分函数下比较；主线 Edge F1 92.02% → 87.52%，modified F1 29.63% → 48.78%。扩大 modified 的识别有所增加，但整体可靠性尚未改善。不得把本轮48.78%直接与旧窄定义33.33%当作同口径增益。
