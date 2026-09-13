# 框架持续改进与日志索引（截至保守 v5）

这是依据已有报告补充的导航，不是补造当时的运行日志。历史文件与冻结结果保持原样。旧发布目录的 DEVELOPMENT_HISTORY.md 只写到 revision v2；当前最新实验候选为 `outputs/visual_graph_v5/entity_graph_attribute_frozen`，322/400 可进入矩阵，尚未证明独立准确率超过 90%，尚未晋升为新默认。

## 改进脉络

| 阶段 | 主要问题与修改 | 结果与取舍 |
|---|---|---|
| 骨架与20图开发 | 收缩为实体/属性；词语/POS 独立记录；完善 few-shot 类别、主体 ID、原文引文和属性属主约束 | 小样本指标用于调试，不直接代表400对表现 |
| M2 Flash 迭代 | 群体/实例划分、衣物与身体属主、重复词 occurrence；只在原证据内唯一匹配时修复引用索引 | 早期新示例使联合F1 84.32%→82.54%，未采用；后续独立 final v1 调整达到88.51%候选参考F1 |
| M5 证据与定位 | 从裸名词判断转为带原文语境/完整命题；主体资格传递到属性；复用39图579条旧参考 | final v1 实体434/508=85.43%，属性63/71=88.73%；开发后类型路由，不是独立gold准确率 |
| 400对 revision v2 | 把局部问题传播与整对隔离分开；区分身份与描述变化；处理共享视觉命题绑定与二轮复核 | 原首轮187/400可计入；v2 guard 达269/400。模块事实级F1不等于样本级矩阵覆盖率 |
| 文档建议后的 M2 A/B | 名词中心、逐主体属性槽检查，固定两边模型/结构/后处理，比较prompt与few-shot整体条件 | 112次调用；旧40条属性F1 90.00%→94.87%，实体89.80%→89.23%，整句完全匹配19→16；不晋升 |
| v4 | 简化M3输出、传播未决主体、二选一隔离、M5复核、保守数量上下界 | 完整新M3条件278/400且有退化；保留旧M3并复用严格同命题视觉结果、加入保守数量约束，292/400，较269净增23且无退化 |
| v5 | 锁定已确定对齐，只局部补未决；同图共享区域定位；区分搜寻区域与目标；输出区域预算 | 局部对齐单独304；实体联合视觉+原属性方法组合322/400，较292恢复33、退化3，净增30 |
| 当前分析 | 冻结322版本离线计算矩阵、成分、条件属性、POS与案例 | 不新增模型调用；图表与分析有独立脚本、输入哈希及CSV |

v4 曾有299/400临时值，因未充分隔离群体粒度及抽取缺失而撤销，最终为292。v5完整联合方案可达323，但旧参考属性一致率88.73%→83.10%，因此不以最高覆盖率选它替代整套模块。数字不是一条无退化的准确率上升曲线。

## 日志具体保存了什么

| 层级 | 当前可查文件 | 用途 |
|---|---|---|
| 阶段决策报告 | `outputs/visual_graph_v5/RESULTS.md` | 问题、改动、消融对照、失败方案、取舍、剩余缺口 |
| 冻结清单 | `outputs/visual_graph_v5/calls/manifest.json` | 创建时间、输入/示例/协议/源码哈希；旁边 frozen_code 保存代码副本 |
| 调用结果 | `outputs/visual_graph_v5/calls/results.jsonl` | 逐任务身份、状态、结果、审计及新增调用记录 |
| 响应检查点 | `outputs/visual_graph_v5/calls/checkpoints/` | 原始响应、审计与校验和；支持复算与恢复，避免无记录重跑 |
| 局部变更 | `outputs/visual_graph_v5/search_binding_audit.jsonl` | 搜寻区域适配的逐条证据 |
| 样本状态变化 | `outputs/visual_graph_v5/entity_graph_attribute_frozen/transitions.jsonl` | 每对从旧状态到新状态的变化；恢复与退化均保留 |
| 剩余失败 | `outputs/visual_graph_v5/entity_graph_attribute_frozen/remaining_cases.jsonl` | 78对未决样本及原因 |
| 完整性与调用汇总 | `outputs/visual_graph_v5/final_status.json`、`integrity.json` | 目标状态、检查点检查、输入不变与调用数 |
| 旧参考逐条对照 | `outputs/visual_graph_v5/legacy579/paired_with_fallback.jsonl` | 原预测、新预测、参考及长度回退状态 |
| 分析来源 | `outputs/visual_graph_v5/analysis/metrics.json` | 分母、输入SHA-256、统计及限制 |

v5 共186次新增调用：117次主实验、68次旧参考测试、1次输出长度回退。最终状态文件记录主实验234个检查点、旧参考原运行135个、回退2个的校验；不能把检查点文件数当作请求次数。未获成功响应的调用不会凭空补出响应日志。

## 记录的边界

确实有日志，不只是聊天里的口头记录；但记录分散在多个实验目录，没有一份从首轮到当前自动追加、统一格式的完整总账。旧发布版历史索引也没有自动同步到v5，本文件补足导航。

不同阶段日志结构与完整程度有差异；本次核对了上述报告、v5清单/结果/响应检查点结构，没有重新逐一校验全部历史调用。不能声称每次临时终端操作都留有完整日志，也不能把本地记录存在等同于GitHub已经同步。

## 报告入口

- 早期至revision v2：`publication/idea/docs/DEVELOPMENT_HISTORY.md`
- M2失败示例及独立索引修复：`outputs/decompose_iteration_v1_flash/RESULTS.md`
- final v1：`outputs/final_v1_release/RESULTS.md`
- 文档建议合并审查：`docs/entity_attribute_v3_review.md`
- 名词中心M2 A/B：`outputs/entity_attribute_v3/m2_ab/RESULTS.md`
- v4：`outputs/matrix_recovery_v4_refined/RESULTS.md`
- v5：`outputs/visual_graph_v5/RESULTS.md`
- 当前矩阵分析：`outputs/visual_graph_v5/analysis/REPORT.md`
