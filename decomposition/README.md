# Semantic Core Decomposer v6

当前入口为 `python -m decomposition.run_v6`。按最新要求，主输出为 **entity / relation / attribute / other**，action 并入 relation，counting 并入 attribute 并保留细标签。模型一次输出带 category 的自然语言原子事实，程序固定归并；不再先生成冻结实体图。

详细规则与删减说明见 [v6 标注与实现说明](../annotation/v6/POLICY.md)，示例见 [8-shot 原始数据](v6/shots.json) 和 [程序整理后的示例](../annotation/v6/example_documents.json)。other 表示范围或拆分歧义，不表示幻觉；推测、否定和具体数量仍保留主线。模型不输出未经校准的置信度分数。

```powershell
.venv/Scripts/python.exe -m decomposition.run_v6 --input outputs/stability_inputs/captions.jsonl --output outputs/v6_prepare --prepare-only
.venv/Scripts/python.exe -m decomposition.run_v6 --input outputs/stability_inputs/captions.jsonl --output outputs/v6_run --shots 8 --spacy-model en_core_web_md
.venv/Scripts/python.exe -m unittest tests.test_v6 -v
```

沿用原 API 配置，思考始终关闭。prepare-only 不读密钥、不联网。真实执行默认一次请求，顶层格式/截断/可重试网络错误至多再试一次；局部异常保留待审，不反复改写。输出 facts.csv、main_facts.csv、other.csv、captions.csv、samples.jsonl、ready_samples.jsonl 与 summary.json。other 分流比例按 method/decode 导出；局部结构错误与 other 分开统计。主类候选表仍含带标记的待审记录，不是金标。

`--spacy-model` 可选；省略时 POS 明确记为不可用。原始 caption 和图片/method/decode 元数据始终保留，但只把 caption 文本发送给拆分模型。修改协议或从 prepare 转 execute 必须使用新输出目录；同一协议可 --resume。独立稳定性测试使用新目录。

本次是代码改版及本地回归，不宣称已经提高 DeepSeek 语义准确率；历史 v5 指标不能直接当作 v6 的基线同口径成绩。

## 历史 v5

新版运行入口为 `python -m decomposition.run_v5 --input ... --output ...`。v5 采用实体/引用解析、冻结实体表、五维事实提取两阶段，保留具体人物类别与身体部位，统一 count 的 subject/comparator/unit，增加动作参数角色、否定、集合成员关系和可审计原文偏移。详细说明见 [v5 标注规范](../annotation/v5/ANNOTATION_POLICY.md)，全部示例/参考标注见 [审核包](../annotation/v5/ANNOTATIONS_REVIEW.md)。

```powershell
.venv/Scripts/python.exe -m decomposition.run_v5 --input outputs/fewshot_v1_pilot/inputs.jsonl --output outputs/v5_prepare --prepare-only
.venv/Scripts/python.exe -m decomposition.run_v5 --input outputs/fewshot_v1_pilot/inputs.jsonl --output outputs/v5_run --shots 8
```

沿用 `api_config.local.json`，无需重新输入密钥；思考始终关闭。v5 导出完整 JSONL、entities.csv、facts.csv，以及保留 caption 层独立 POS 统计的 captions.csv；未决、排除、局部修复和未知谓词均保留。准备与真实执行使用不同输出目录。相同配置下可 `--resume` 读取已有检查点；独立稳定性测试使用新目录，不用缓存。v5 实验入口为 `python -m tests.run_v5_experiment prepare/execute/report`，本轮冻结记录在 `outputs/five_dim_v5/experiment_v1`。

首次 v5 真实实验已完成：严格参考匹配 F1，0-shot 为 53.1%，8-shot 为 65.9%，参考标注尚未经独立人工审核。完整指标、失败与稳定性限制见 [v5 实验报告](../outputs/five_dim_v5/experiment_v1/TEST_REPORT.md)。当前代码 v5.0.1 的局部工程修复仅作离线回放，不冒充已重跑 API 的结果。

以下为仍可复现的旧 v4 入口说明；旧数据与新 schema 不混用。

## 历史 v4

当前运行提示词已更新到 **v4.1 / eight-shot-v1**：默认读取冻结的 8 条示例；`--shots 0` 使用相同规则、不带示例的对照。保留 hand、明确人物类别、一般/具体信息与推测用途；busy/comfortable 等模糊评价本版暂不计入事实。原文不删改。规则见 `prompts/entity_facts_v4_1_rules.txt`，示例见 `prompts/entity_facts_v4_1_shots.jsonl`。

首次真实 API 对照测试已完成：32 次逻辑调用，零示例与 8-shot 主测均有 13/14 条结构通过；few-shot 有局部语义改善，但重复运行仍存在拆分粒度变化，尚未通过语义稳定性验收。完整结果见 `../outputs/fewshot_v1_pilot/TEST_REPORT.md`，逐条原文与输出见 `../outputs/fewshot_v1_pilot/REVIEW_CASES.md`。结构通过率不是语义准确率。

当前输出为 `id / text / entities / facts`，按用户最新规则替换 v3 平面 fact。只做拆解，图像验证和 vanilla/steer 对齐留给独立模块。DeepSeek 强制关闭思考，temperature=0；原 API 配置无需重填。

## 流程与边界

原文 → 一次结构化模型提取 → 字段/实体引用/原文片段校验 → 同实例结构精确去重 → 导出。格式错误有界修复；网络与认证失败保留记录。保留 speculative 和矛盾主张，verification 统一 pending；不做图像真假判定。

同类不同实例不合并。属性和关系分开，动作与位置分开；holds/wears 属于 relation。count 使用 target（类别名或实体 ID 数组），不使用 subject；模糊数量保留文字。源文本和 mention/source 必须逐字匹配。完整规则与示例见 `../annotation/v4/ENTITY_FACT_RULES.md`。

旧版类级覆盖补充和文本规范化未接入本版，避免把实例 ID 合并或误配。旧实现及测试归档在 `../legacy/three_rules_v3/`；目录中旧 normalizer/object_coverage/protocol/extraction_schema 文件仅供历史参考，不在当前执行链中。旧 flat-fact 评估工具禁止读取本版输出，不得将跨 caption 的 e1/e2 当成同一实例比较。

## 输出

- samples.jsonl：标准四字段样本，可直接用于人工标注/后续模块。
- entities.csv：sample_id, entity_id, mention, canonical。
- facts.csv：sample_id, fact_id, type, subject, predicate, object, target, value, assertion, source, verification。各类型不使用的列为空；target 数组是 JSON。
- captions.csv：image/method/decode、长度和独立 POS 统计。模型看不到这些实验标签；模型请求中使用中性 ID，程序保存时绑定真实 sample_id。
- decomposed.jsonl/checkpoints：完整运行记录；audit.jsonl：原始响应、结构修复、精确去重记录。失败或疑难不会混进成功样本表。

ready 只代表结构校验完成，不代表语义正确或图像支持。空 caption、重复退化、失败与无范围内事实分别记状态。缓存冻结输出但不是模型独立稳定性证据；独立重复时用 --bypass-cache。

## 运行

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe -m decomposition.run_decomposition --input outputs/stability_inputs/captions.jsonl --output outputs/new_entity_v4_prepare --prepare-only
.venv/Scripts/python.exe -m decomposition.run_decomposition --input outputs/stability_inputs/captions.jsonl --output outputs/new_entity_v4_run --bypass-cache
.venv/Scripts/python.exe -m annotation.v4.build_entity_examples
```

prepare-only 不读取 API 密钥，也不联网。调用 API 的运行使用原 api_config.local.json；不要将它上传。版本/代码/提示词进入缓存和续跑指纹，旧输出不能在原目录续跑成新版。

本次本地测试记录见 ENTITY_SCHEMA_TEST_REPORT.md；结构通过不等于语义准确率提升。
