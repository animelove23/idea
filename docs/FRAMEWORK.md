# 框架：模块契约与数据用途

版本状态与架构图见[首页](../README.md)。本阶段只把 entity 和 attribute 作为可验证语义事实；POS 是独立的词语统计视角，不能把所有动词、介词自动视为已经分析过的动作和关系事实。

| 模块 | 记录什么 | 后续如何使用 | LLM 参与 | 测评重点 |
|---|---|---|---|---|
| 输入／M0 | pair_id、image_id、同图两段原文、图片路径与 SHA256、caption_id | 锁定输入、排除图文错配；manifest 约束恢复 | 无 | ID 唯一、图片可读、哈希一致、配对完整 |
| M1 词语层 | 原词、lemma、UPOS、字符区间、句子号、相对位置、词数、重复 lemma 计数 | 与 M2 引文跨度连接；统计名词/形容词等净减少和重复提及代理量 | 无，spaCy | 字符回指一致、词数/POS 守恒；POS 不是人工金标准确率 |
| M2 粗粒度 | 实体 ID、名称、重复 mentions、实体属性 slot/value、原文引文及 occurrence、规范化问题 | 主体事实与属性事实都进入 M3；每条属性携带 owner；非法/缺失内容进入质量记录 | Flash，8-shot；每段文本一次 | 实体/属性/joint P/R/F1、引文有效率、覆盖与拒收原因 |
| M3 对齐 | 跨文本主体身份、description_change、事实 retained/removed/added/modified/unresolved、冲突理由 | 决定共享视觉命题是否安全；为真实/幻觉成分的增删改统计提供事件 | Flash，8-shot；每对一次 | 实体映射和事实联合 F1、语义未决、技术未决；逐行合法性 |
| M4 命题队列 | claim_id、refs、类型、命题、原文主体上下文、图像哈希 | 同一可安全共享命题只验证一次；每个引用回填各自事实账本 | 无 | 事实引用完整、无重复/漏记、错误共享率审计 |
| M5 视觉验证 | 主体候选、可辨区域、全图 bbox、可见线索、限制、属性证据、最终标签 | supported/hallucinated/uncertain 回填逐事实账本；属性统计检查 owner | Flash，原 6-shot；每唯一命题一次 | 分类型混淆矩阵、Macro-F1、候选一致率、uncertain 召回、主体属性冲突 |
| 定向复核 | 首轮原记录、独立第二轮证据、判定转移、技术失败 | uncertain 和主体属性冲突触发；保留全图，可加未证实 bbox 的像素裁剪 | Flash，原 6-shot；每选中命题至多额外一次 | U→S/H/U、确定→冲突转移、复核成本；确定率不是正确率 |
| M6／观测 | 逐事实来源与资格、局部未决原因、成分候选状态、矩阵、POS/重复量 | 输出动机候选、可追溯案例与后续消融假设 | 无 | 分母守恒、去重、局部依赖测试、分类覆盖及缺失分布 |

## 类别边界

1. **主体身份与措辞具体程度分开。** 同一条前景狗从 “poodle” 变为 “dog” 是主体对应＋描述泛化；不能仅因上下位词关系就把不同位置的两只动物配成同一主体。集合／部分整体不自动一对一匹配。
2. **属性必须属于同一主体。** “wooden clock”→“clock on a wooden shelf” 是时钟材质属性消失，不能把架子的材质迁移给时钟。
3. **未提及不等于分解缺失。** 对面文本确实存在对应引文而 M2 漏提时，要记录 extraction gap；不能直接当作语义删除。
4. **主体不确定时，属性支持不直接进入严格真实信息统计。** 冲突保留并触发一次复核；不能靠属性“看起来正确”补造主体支持。
5. **语义不确定与技术失败分别记录。** ID 越界、重复映射、违反一对一约束是技术问题；确实无法建立同一主体关系是语义问题。局部隔离只降为未决，不猜测正确答案。

M3 当前 8 个示例与 8 个开发探针见 [align_shots.jsonl](../experiments/coco400_revision_v2/align_shots.jsonl) 和 [align_probes.jsonl](../experiments/coco400_revision_v2/align_probes.jsonl)。M2 提示在 `analysis_skeleton/final_v1/` 与 `analysis_skeleton/shots/`；M5 路由和两种同图示例在 `outputs/final_v1_release/visual_routes.json`。示例不携带待测样本参考答案。

## 端到端输出

`first_pass/` 保存首轮分解、对齐、队列、验证和 manifest；`review/` 保存二轮任务、调用检查点与审计；最终 `pairs.jsonl`、`denominator_ledger.jsonl`、`observation_pairs.jsonl` 和 `summary.json` 保持分层可追踪。

新输入运行所有阶段。历史 400 对修订实验则复用已冻结 M2 和首轮 M5，以控制变量；这两种实验执行方式不能混写。恢复仅支持同一目录、输入、代码、配置与示例，禁止借不同条件缓存混淆比较。
