# VISTA EOS 实验归档

本目录按实验编号保存从 premature-EOS 现象发现到当前机制诊断的记录、代码快照和原始输出。

## 归档规则

- `EOS-XX_RECORD.md`：实验目的、设计、输入、指标、运行状态和产物索引。
- `EOS-XX_CONCLUSION.md`：只写该实验本身支持与不支持的结论。
- `code/`：该实验直接使用的脚本快照，文件名带相同编号。
- `outputs/`：配置、日志、JSON/JSONL、CSV、tensor cache 等原始产物，目录名带相同编号。
- 原始项目文件均保留不动；这里是独立归档副本，避免破坏旧脚本中的绝对路径和结果引用。

## 实验编号

| 编号 | 实验 | 状态 | 核心问题 |
|---|---|---|---|
| EOS-00 | 研究范围与预注册计划 | 文档归档 | premature EOS 应如何测量和定位？ |
| EOS-01 | 初始 greedy/beam5 复现 | 完成但原 beam run 不完整 | 完整 VISTA 是否在 beam5 下产生大量首 token EOS？ |
| EOS-02 | 10 图模块消融 | 完成，机制富集样本 | VSV-only 或 SLA-only 是否足以产生空输出？ |
| EOS-03 | M00 baseline 与机制 cohort | 完成 | 如何冻结可复现的 collapse/control 对照集？ |
| EOS-04 | no-op、batch、cache 数值控制 | 部分通过 | EOS 现象是否可由 wrapper、batch expansion 或 cache 数值差异解释？ |
| EOS-05 | 64 图 fixed-prefix 2×2 因子实验 | 完成 | beam 之前 VSV、SLA 及交互如何改变 EOS 相对分数？ |
| EOS-06 | 64 图 greedy/beam trace | 完成，beam 原始数据分主跑与恢复跑 | 真实自由解码下，联合方法与 beam 的 outcome 差异是什么？ |
| EOS-07 | final/SLA readout 反事实分解 | 完成 | VSV 引起的 logits 重排主要由 final readout 还是 SLA readout 承载？ |

## 当前总判断

1. 完整 VISTA 在该 LLaVA-1.5-7B 配置下出现可复现的 beam5 首 token EOS/空输出。
2. 在机制富集样本中，VSV-only 和 SLA-only 均没有产生空输出；VSV+SLA 才出现大量空输出。
3. fixed-prefix 实验显示 VSV 会显著提高 EOS relative margin，但该变化不等于 EOS raw logit 被同等幅度推高，也不具有 collapse-specific 模式。
4. 真实解码中 M11 从 greedy 的 2/64 empty 上升到 beam5 的 28/64；beam 是强放大条件，但现有结果还没有定位到 scorer、candidate retention 或 finished-hypothesis 中的唯一因果步骤。
5. EOS-07 不是“两条 VSV 注入路径”实验。它离线拼接 VSV-off/on 前向得到的 final 与 SLA logits 分量；其构造在 token-logit 层面代数可加，不能用来证明或否定模块级协同机制。

## 阅读顺序

建议依次阅读每个编号目录中的 `RECORD` 和 `CONCLUSION`，需要复核数字时再查看同目录 `outputs/` 中的配置和原始 JSONL/CSV。
