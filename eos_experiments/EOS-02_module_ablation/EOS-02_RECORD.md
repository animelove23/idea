# EOS-02 模块消融记录

## 目的

在 EOS-01 中最先出现空输出的 10 张图上，比较完整方法、VSV-only 和 SLA-only，判断任一单模块是否足以复现 beam5 空输出。

## 条件

- 完整 VISTA，SLA `25,30`（代码默认，6 个 states）；
- 完整 VISTA，SLA `26,30`（论文 literal w=5）；
- VSV-only，`lambda=0.17`；
- SLA-only，`alpha=0.3`，layers `26,30`；
- 全部使用 beam5、seed 1994、相同 checkpoint/data/prompt。

## 结果

| 条件 | Empty | 平均解码词数 |
|---|---:|---:|
| 完整 VISTA，25–30 | 8/10 | 50.6 |
| 完整 VISTA，26–30 | 8/10 | 82.5 |
| VSV-only | 0/10 | 131.7 |
| SLA-only | 0/10 | 92.7 |

## 输出

- `EOS-02_SOURCE_OBSERVATION.md`：当时的表格和逐图记录。
- `outputs/EOS-02_full_method_w6_recheck/`：默认窗口复查。
- `outputs/EOS-02_full_method_w5/`：论文 literal w=5。
- `outputs/EOS-02_vsv_only/`：VSV-only。
- `outputs/EOS-02_sla_only/`：SLA-only。

## 抽样限制

10 张图由已发生 collapse 的结果中选择，是机制富集样本，不是无偏 prevalence 样本。
