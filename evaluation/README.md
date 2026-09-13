# v6 downstream evaluation

Coverage → Entity Alignment → Fact Alignment → Pending Verifier。

当前 Alignment v1.2 的校验调整见 [VALIDATION_V12.md](VALIDATION_V12.md)：结构错误、语义待审、辅助字段告警分别记录。v1.1 的同义关系与重复对应边界保留在 [BOUNDARY_RULES.md](BOUNDARY_RULES.md) 作为历史说明；与v1.2不一致处以新说明为准。旧输出不回写。

本模块直接消费现有 v6 独立拆分结果，不修改 Decomposer、few-shot 或已有文档。输入提示中旧版 entity graph / 五类示例与“保持 v6 格式”冲突时，采用后者：保留 `entity/relation/attribute/other`，实体对应信息另存 sidecar。动作仍属于 relation，数量仍属于 attribute；other 保留记录但不进入主线统计。

## 输入与运行

在项目根目录运行。pairs.jsonl 每行：

```json
{"pair_id":"pair_01","original":{"id":"original_caption_id","text":"...","facts":[]},"steer":{"id":"steer_caption_id","text":"...","facts":[]}}
```

original / steer 应替换为完整原生 v6 document，必须先独立拆分。

```powershell
.venv\Scripts\python.exe -m evaluation.run prepare --pairs outputs/downstream_v1/pairs.jsonl --output outputs/downstream_v1/real_run
.venv\Scripts\python.exe -m evaluation.run execute --output outputs/downstream_v1/real_run
.venv\Scripts\python.exe -m evaluation.run report --output outputs/downstream_v1/real_run
```

使用现有私密 API 配置，限官方 DeepSeek 地址，temperature=0，thinking=disabled。一次 Coverage 请求只包含一条 caption 的文本与语义事实；不传图片、真假标签或方法优劣标签。两步 Alignment 各一次请求。没有自动修复/重试；首次结果保留供审查。

prepare 冻结输入、代码和提示词；execute 检查哈希。每步先保存 started 标记，再保存完整响应与校验结果。续跑复用已完成步骤；若进程中断导致请求是否完成不明，会拒绝重复调用。每个不同输入文档仅进行一次 Coverage。

## 约束与输出

- `coverage.jsonl`：每 caption 的 added_facts、拒绝候选、状态和 augmented_document。新 fact 用原生 v6 字段，并添加 `added_by_coverage=true`；ID 为 `cov_fN`。所有原始 facts 保持原样。只校验格式与原文出处，不能据此保证语义蕴含；语义错误候选需人工审查。
- `coverage_augmented.jsonl`：追加后的完整原生文档。
- `entity_alignment.jsonl`：基于完整语境识别的 referent sidecar；matched 分配共享 gN，ambiguous 不强行赋予共享 ID。sidecar 不写回原文档，也不新增事实。
- `alignment.jsonl`：每条事实恰好分配一次；保留五种状态。modified 必须同实体、同窄语义槽位；只有部分重合、粒度不同、身份不确定都应 ambiguous。对侧原文表达但漏拆时使用 `ambiguous/extraction_gap` 并附对侧原文引文。结构校验失败或漏分配一律 ambiguous，不自动当作 removed/added。
- `verification_pending.jsonl`：原/steer 各事实独立预留 claim；全部 pending。`VisualVerifier.verify_claim(image, fact, entity_context)` 可被未来 verifier 实现替换，本版不读取图片。
- `summary.json` / `TEST_REPORT.md`：主线和全量的状态行数、每侧事实计数、补充内容、对应关系与失败记录。多对多 ambiguous 的行数不等于事实数。

原始请求、响应、模型与 usage 在各中间文件 audit 中留存，不保存 API key。输入/中间件是研究数据，不应直接公开。

状态计数不是准确率，pending 不是图像支持。LLM 判断仍可能漏检或误配；原文引文验证不能证明其语义判断正确。本轮真实样本仅用于功能检查，需要人工参考标注才能报告 precision/recall。

## 测试

```powershell
.venv\Scripts\python.exe -m unittest tests.test_evaluation -v
.venv\Scripts\python.exe -m unittest discover -s tests
```

本地测试使用受控响应，覆盖所有对齐状态和 extraction_gap。真实报告中未出现的状态明确记为 0，不以受控案例冒充真实 API 结果。
# 当前版本：v1.3

默认 `evaluation.run` 已使用 retained / removed / added / modified / other。参见 [CORE_CHANGE_V13.md](CORE_CHANGE_V13.md)。other 保留审计并排除主线增减、后续验证队列；实体 sidecar 的 ambiguous 仍保留。下文旧版记录用于追溯，当前协议以 v1.3 文档为准。
