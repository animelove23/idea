# EOS-07 final/SLA readout 反事实分解记录

## 正确实验名称

这是 final-layer 与 SLA early-layer logits readout 的离线反事实分解，不是“两条 VSV 注入路径”实验，也不运行 beam search。

## 设计

- 使用 EOS-05 的 64 图和冻结 M00 prefixes `k={0,1,3,5,10}`。
- 每张图只构造一次 layer-wise VSV。
- 对每个 prefix 做两次完整前向：VSV off 与 VSV on。
- 从 off 前向提取 `F0`（final logits）和 `A0`（layers 26–30 的 SLA mean logits）。
- 从 on 前向提取 `F1` 和 `A1`。
- 离线构造：

```text
C00 = 0.7 F0 + 0.3 A0
C10 = 0.7 F1 + 0.3 A0
C01 = 0.7 F0 + 0.3 A1
C11 = 0.7 F1 + 0.3 A1
```

C00 等价于 SLA-on/VSV-off 的混合输出；C11 是完整 VSV+SLA；C10/C01 不是可独立执行的论文模块配置，而是两次前向后的反事实 readout 拼接。

## 完整性

- 64/64 图完成，零异常。
- 5 个 prefix × 4 个 counterfactual，共 1,280 条记录。
- 每图保存 F0/F1/A0/A1 tensor cache。

## k=0 汇总

| 条件 | EOS logit | Top non-EOS logit | EOS margin | EOS rank | EOS probability |
|---|---:|---:|---:|---:|---:|
| C00 | 8.928 | 24.698 | -15.770 | 242.98 | 1.34e-7 |
| C10 | 9.159 | 19.430 | -10.271 | 70.59 | 3.50e-5 |
| C01 | 9.841 | 23.152 | -13.311 | 121.95 | 1.67e-6 |
| C11 | 10.071 | 17.952 | -7.881 | 37.20 | 2.96e-4 |

从 C00 到 C11，EOS logit 增加约 1.143，而最高非 EOS logit 下降约 6.746，产生 7.889 的 relative-margin 变化。主要变化是竞争 token 被压低，不是 EOS raw logit 同幅暴涨。

## 代数约束

对任意 token 的原始 logit：

```text
C11 - C10 - C01 + C00 = 0
```

这是构造方式保证的。EOS-margin 中 k=0 的 `-0.069` 来自 `max(non-EOS)` 的非线性和最高竞争 token 可能切换，不能当作模块级交互估计。

## 输出

- `outputs/EOS-07_smoke_initial/` 和 `EOS-07_smoke_rerun/`：2 图开发运行。
- `outputs/EOS-07_path_split_64/`：正式配置、1,280 条 JSONL、summary 和 64 图 tensor cache。
