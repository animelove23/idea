# EOS-05 fixed-prefix 2×2 因子实验记录

## 设计

- 64 图机制 cohort：32 collapse + 32 matched controls。
- 冻结 M00 greedy prefixes：`k={0,1,3,5,10}`。
- batch=1、non-cached、teacher-forced forward；不运行 beam。
- `M00`：VSV off、SLA off。
- `M10`：VSV on、SLA off。
- `M01`：VSV off、SLA on。
- `M11`：VSV on、SLA on。
- 指标：EOS logit/prob/rank/margin、top non-EOS、entropy、logit scale；同时保存 release-native 和 FP32 projection。

## 运行完整性

- 64/64 完成，无异常。
- 2,560 条 factorial 指标记录。
- native 与 FP32 EOS-margin mean absolute difference：0.00506。

## 关键结果

collapse cohort 在 `k=0` 的 FP32 效应：

- VSV effect `M10-M00 = +7.854`，95% bootstrap CI `[7.564, 8.155]`；
- SLA effect `M01-M00 = -0.811`，CI `[-0.854, -0.766]`；
- interaction `+0.294`，CI `[0.144, 0.451]`。

交互只在最早 prefix 较小幅为正；在 `k=3,5,10` 显著为负。control cohort 呈现相似模式，collapse-control interaction difference 没有可靠区分度。

## 输出

`outputs/EOS-05_fixed_prefix_64/` 包含配置、原始 JSONL、summary、方法均值、bootstrap effects 和分析报告。
