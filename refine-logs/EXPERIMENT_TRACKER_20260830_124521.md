# 第一组实验 Tracker：VISTA termination onset

| Run ID | Milestone | Purpose | System / Variant | Cohort | Metrics / Artifact | Priority | Status | Notes |
|---|---|---|---|---|---|---|---|---|
| E1-M0-001 | M0 | 冻结无偏发生率集 | deterministic 100-image manifest | P | IDs、顺序、SHA256 | MUST | DONE | 已冻结 100 IDs；禁止按输出筛选 |
| E1-M0-002 | M0 | 冻结机制富集集 | 32 collapse + 32 matched controls | M | IDs、配对变量、SHA256 | MUST | DONE | M00 160/160；32+32 匹配完成，平均长度差 0.34 词 |
| E1-M0-003 | M0 | 数据/配置 dry run | M00/M10/M01/M11，4 images | M-mini | record status、config/checkpoint hash | MUST | FAILED | 执行完成；原 2e-3 数值门槛失败 |
| E1-B1-001 | M1 | strict no-op 检验 | off vs wrapper λ=0 vs strict λ=0 | M-mini→M | max abs/relative logit diff | MUST | DONE | 所有位置和精度路径 max diff=0 |
| E1-B1-002 | M1 | batch expansion control | batch1 vs repeat×5 | M-mini→M | per-row logit diff、EOS metrics | MUST | FAILED | FP16/GEMM all-vocab max diff 至 0.078 |
| E1-B1-003 | M1 | cache consistency | cached one-step vs full-prefix | M-mini→M | logit diff、EOS rank/margin | MUST | FAILED | k>0 all-vocab max diff 至 0.03125；k=0 通过 |
| E1-B1-004 | M1 | 2×2 fixed-prefix factorial | M00/M10/M01/M11，k=0/1/3/5/10 | M | EOS logit/prob/rank/margin、entropy、scale | MUST | DONE | 64/64；result-to-claim=partial |
| E1-B2-001 | M2 | 缓存两条路径 logits | F0/F1/A0/A1 | M | tensor cache + metadata | MUST | TODO | 每图 VSV 只算一次 |
| E1-B2-002 | M2 | counterfactual path mixing | C00/C10/C01/C11 | M | EOS/content metrics | MUST | TODO | 离线计算，不重复 forward |
| E1-B2-003 | M2 | path-swap 生成验证 | C10/C01/C11 beam5 | M-32 | empty、PTR@k、length、coverage | MUST | TODO | 16 collapse + 16 controls |
| E1-B3-001 | M3 | greedy reference trace | M00/M10/M01/M11 greedy | M-32 | per-step EOS metrics | MUST | TODO | 与 beam 同配置 |
| E1-B3-002 | M3 | beam5 internal trace | M00/M10/M01/M11 beam5 | M-32 | parent/cache/candidate/finished/score | MUST | TODO | 定位首次 divergence |
| E1-B4-001 | M4 | mean/std calibration probe | raw vs affine-calibrated A | M | EOS interaction、content margin | MUST | TODO | gamma 固定 0.3 |
| E1-B4-002 | M4 | RMS calibration probe | raw vs RMS-matched A | M | EOS interaction、content margin | MUST | TODO | 不做 gamma sweep |
| E1-B4-003 | M4 | calibration generation check | raw/affine/RMS beam5 | M-32 | empty、PTR、coverage、CHAIR | MUST | TODO | 仅 B1/B2 通过后执行 |
| E1-M5-001 | M5 | 无偏发生率验证 | M00/M10/M01/M11 beam5 | P | empty、EOS@k、PTR@k、length、coverage | MUST | TODO | 同一 100 IDs |
| E1-SENS-001 | M5 | release layer-window sensitivity | M11 `25,30` vs `26,30` | P | EOS/length/coverage | NICE | TODO | 不进入完整 factorial |
| E1-SENS-002 | M5 | prompt punctuation sensitivity | with/without terminal period | P | paired EOS/length diff | NICE | TODO | 仅 full method |

## 状态约定

- `TODO`：尚未启动
- `RUNNING`：进程已验证、输出持续写入
- `DONE`：目标样本全部完成且完整性检查通过
- `FAILED`：运行或完整性检查失败
- `BLOCKED`：被前置 stop gate 阻止

## 首先启动的三个 run

1. `E1-M0-001/002`：生成并冻结 Cohort P/M manifests。
2. `E1-M0-003`：4 图、四方法 dry run，验证统一日志与输出完整性。
3. `E1-B1-001/002/003`：先用 4 图排除 no-op、batch expansion 和 cache 问题；全部通过后再扩展到 64 图。
