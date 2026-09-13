# framework_v2 首轮改进与测试报告

已完成计划E0/E1：可恢复通用运行入口、逐请求/逐pair故障隔离、固定计分与分母账本；同时准备类别覆盖和人工复核材料。旧语义规则、模型、8/8/6-shot及候选参考未修改。

## 实际测试

- 回归测试结果另存test_results.json。
- 原20图全链重放：40个M2、20个M3、199个M5响应，共259个请求检查点；新增API调用0。
- 20对文档、对齐、词语记录、199条视觉回填与M6统计均与repair_v1完全一致。
- 再次恢复：复用259个完成检查点，新增调用0。
- 独立M3的20组保存响应也通过完全一致性检查。合法响应未因工程改造改变语义。

## 分母不再隐藏匹配缺口

- 生产账本保留264条有效事实；参考账本始终保留300条候选事实。
- 固定词形口径匹配228条；72条未匹配参考记录为extraction_missing，36条预测额外项另列复核。
- 未匹配不自动等于真实漏抽：可能涉及命名、范围、绑定或参考错误，已生成108条逐项复核记录。
- technical unresolved、semantic unresolved、visual uncertain、pending及父子绑定疑点各有独立字段。原M6分母保持原口径，严格父主体筛选只作旁路审计。

## 准确率与稳定性边界

- 本轮没有换模型/提示/示例，没有重新生成答案；M2约80.9%、M3约93.1%是保存结果的原口径，不是新准确率提升。
- 历史同输入视觉判断仍有10/60标签变化。新增三重复评价器明确pairwise翻转率、完整重复覆盖、S↔H翻转及可决错误率，并拒绝把缓存结果当独立重复；本轮没有运行fresh三重复。
- 已提供24组完整边界候选（20组分解对照、4组对齐控制）及示例覆盖表。它们经过结构验证，不是LLM通过率或独立人工gold。
- 新开发/确认集、人工裁决及后续单变量模型实验尚未执行。

## 文件

- integration_replay/denominator_ledger.csv：264条生产事实、迁移、真假及各轴状态。
- reference_denominator_ledger.csv：300条候选参考全集与抽取缺口。
- m2_disagreement_review.jsonl：36个未匹配预测与72个未匹配参考的原文、证据及待裁决字段。
- boundary_cases.jsonl、shot_coverage_matrix.csv：完整候选例子与当前覆盖缺口。
- review_visual_answer_hidden.jsonl：60条遮蔽答案的旧开发集复核输入；候选答案在独立key文件，不能称新的盲测。
- BASELINE_LOCK.json、replay_equivalence.json、test_results.json、TASK_STATUS.json：来源锁、重放证据、测试与阶段状态。
