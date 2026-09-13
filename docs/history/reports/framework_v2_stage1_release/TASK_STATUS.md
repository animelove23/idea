# 计划执行状态

| 任务 | 状态 | 产物/证据 |
|---|---|---|
| E0结构异常隔离、通用入口、恢复、缓存模式 | done | framework_v2；84项回归；259检查点恢复 |
| E1固定计分、生产与参考分母、缺口记录 | done | score_contract_v2.md；264生产事实与300参考账本 |
| 原20图全链及独立M3保存响应复测 | done | replay_equivalence.json；新增API调用0 |
| 类别合同草案、24边界候选、示例覆盖与审核包 | prepared_pending_human_review | evaluation_contract_v2.md、fewshot_review.md及JSONL/CSV |
| 人工裁决及真实gold | pending_reference | 本轮无人工作出裁决 |
| D1新开发集与T1确认集 | pending_data_and_reference | 未创建；旧20图不改名为独立测试 |
| 三次fresh重复 | not_run_first_stage_zero_LLM | 评价器及字段已实现，不把replay冒充独立调用 |
| X2/X3/X4/X5单因素模型改进 | not_run | 保留模型、prompt、shot、窗口及旧参考 |

本交付对应计划要求首先完成并交付的E0/E1及第5节材料准备，不宣称整份科研验收计划已经完成。下一阶段从参考审核和fresh重复基线开始。
