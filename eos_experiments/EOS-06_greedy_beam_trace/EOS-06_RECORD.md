# EOS-06 真实 greedy/beam 解码记录

## 目的

在相同 64 图机制 cohort 上运行 M00/M10/M01/M11 自由生成，对比 greedy 与 beam5，并记录每步 EOS 与 beam 内部候选信息。

## 完整性

- greedy：256/256 方法×图记录完成，无异常。
- beam 主运行包含成功记录和 27 条 OOM exception；M11 缺失部分随后单独恢复。
- M11 beam5 恢复运行：26/26 完成，无异常。
- image 116521 由单图 smoke rerun 恢复。因此 M11 beam5 的最终 64 图由主运行 37 个成功记录、26 图恢复运行和 1 图单独恢复组成，三者 image ID 不重复。
- 因此 beam 原始证据分布在三个记录集合中，不能只读取任一单文件，也不能把主运行的 OOM 与恢复后的成功记录重复计数。

## 结果汇总

| 方法 | Greedy empty | Beam5 empty |
|---|---:|---:|
| M00 | 0/64 | 0/64 |
| M10（VSV-only） | 0/64 | 0/64 |
| M01（SLA-only） | 0/64 | 0/64 |
| M11（VSV+SLA） | 2/64 | 28/64 |

M11 beam5 的 28 个 empty 中，26 个来自 32 个 historical collapse 样本，2 个来自 32 个 matched controls。

## 输出

- `outputs/EOS-06_greedy_trace_64/`：四方法 greedy trace。
- `outputs/EOS-06_beam_trace_64/`：beam smoke、失败主跑、成功记录及 M11 恢复运行。
