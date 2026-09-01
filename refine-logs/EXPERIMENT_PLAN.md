# 第一组实验计划：VISTA 提前终止起点与双路径耦合诊断

**问题**：VSV 与 SLA 单独使用时基本正常，但联合使用在 beam search 下出现大量 premature EOS；需要判断异常是在普通 forward 中已经形成，还是由 beam expansion/cache/scorer 产生，并区分算法耦合、跨层 logit 尺度失配和 wrapper 数值副作用。  
**方法论主线**：在相同图像和相同 token prefix 上做 2×2 因子实验，直接分解 final path 与 SLA path 对 EOS relative margin 的贡献，再用真实 beam trace 验证 beam 是根因还是放大器。  
**日期**：2026-08-30

## 对现有材料的判断

`newest_find_out/basement_by_YE/VISTA_observation_research_goal.md` 的研究问题是成立的，而且比“VISTA 有空输出 bug”更有论文价值。最有潜力的机制主线是：

1. VSV 先改变 intermediate hidden states；
2. 改变后的表示同时进入 final-logit path 和 SLA intermediate-logit path；
3. raw-logit mixing 可能把这种影响重复带入最终分布；
4. EOS 相对 content token 的 margin 进入候选区；
5. beam search 保留并放大提前终止路径；
6. CHAIR 对 under-generation 惩罚不足，指标可能被“少说”改善。

但现有 10 张空输出样本是按 outcome 选择的，只适合机制诊断，不能估计真实发生率。第一组实验必须把以下两个用途分开：

- **Mechanism cohort**：富集已知 collapse 样本，提高定位机制的灵敏度；
- **Prevalence cohort**：不按输出筛选，用于估计空输出和短输出发生率。

第一组暂不做 nucleus sampling 或大范围超参数 sweep。随机采样会增加归因噪声，而参数扫描只能告诉我们“哪里坏”，不能告诉我们“为什么坏”。

## Claim Map

| Claim | 为什么重要 | 最低可信证据 | 对应实验块 |
|---|---|---|---|
| C1：VSV+SLA 在进入 beam scorer 之前已产生正的 EOS interaction effect，beam 主要是放大器 | 决定问题是算法组合还是 beam 实现 bug | 在 batch=1 fixed-prefix forward 中，联合配置的 EOS margin interaction term 显著大于 0；真实 beam trace 显示 EOS 随后被保留并获胜 | B1、B3 |
| C2：异常主要来自 VSV 对 final path 与 SLA path 的共同影响，且 raw-logit scale mismatch 是候选放大机制 | 支撑 double-injection / intervention-dependency 机制 | counterfactual path swap 能定位哪条路径贡献 EOS 优势；校准 intermediate logits 后 EOS margin/empty rate 明显下降 | B2、B4 |
| Anti-claim A：只是 VSV wrapper 的数值副作用 | 若成立，算法机制结论无效 | VSV completely-off、wrapper λ=0、strict no-op 三者逐 token logits 一致到预设容差 | B1 |
| Anti-claim B：只是 batch expansion、cache 或 beam reorder 错误 | 若成立，应先修代码而不是写算法机制 | batch1 与五份重复 batch 的 logits 一致；cached/non-cached fixed-prefix 一致；beam parent/cache trace 无异常 | B1、B3 |

## 第一组实验范围

### Cohort P：无偏发生率集

- 从当前 greedy 500-image manifest 中按固定 seed 冻结 **100 个 image ID**；禁止根据 beam 输出或 caption 长度筛选。
- 所有方法配置复用完全相同的 100 个 ID 和顺序。
- 用途：报告 empty、EOS@1/5/10、PTR@1/5/10、长度与 coverage；这是第一组唯一可用于发生率结论的 cohort。

### Cohort M：机制富集集

- **64 张图**：32 个已知 beam-collapse 样本 + 32 个非 collapse 对照。
- 对照按 baseline greedy caption length decile 配对，避免“collapse 组本来就是短描述图片”的混杂。
- 用途：fixed-prefix、path decomposition、beam trace；不得从该 cohort 推断总体空输出率。

### 统一配置

- Backbone/checkpoint：当前本地 `LLaVA-1.5-7B`，记录绝对路径与 checkpoint/config hash。
- Dataset：MSCOCO 2014 val；保存 image-ID manifest 与 SHA256。
- Prompt：第一组主实验采用论文字符串（无末尾句号）；带句号版本只做一项 sensitivity control。
- VSV：`lambda=0.17`，all layers。
- SLA：主实验采用 paper-literal `w=5`，code indices `26,30`，`gamma=0.3`。
- Release-default `25,30` 只作为 sensitivity control，不进入完整 factorial。
- Generation：`max_new_tokens=512`、temperature 1.0；显式记录 EOS/pad、early_stopping、length_penalty、min_new_tokens。
- 精度：保留当前 FP16 主设置；关键 fixed-prefix logits 额外以 FP32 投影/统计，避免 rank 边界只由 FP16 读数决定。

## Experiment Blocks

### B0：完整性与可重复性冻结

- **Claim tested**：所有配置确实使用同一批图像、prompt、checkpoint 和 generation defaults。
- **为什么存在**：当前 407/500 beam 文件不完整，且旧 loader 依赖未排序的 `os.listdir`。
- **任务**：生成 Cohort P/M manifest；每个 run 写入 config hash、code commit、checkpoint hash、image IDs、完成状态和 stopping reason。
- **必须区分**：`missing_record`、`exception`、`empty_after_decode`、`eos_at_step1`、`short_nonempty`。
- **成功标准**：每个 run 的 ID 集完全一致、无重复、无隐式缺失；manifest hash 相同。
- **失败解释**：任何 ID/配置不一致都先修数据管线，不进入机制结论。
- **优先级**：MUST-RUN。

### B1：2×2 fixed-prefix factorial 与 strict no-op

- **Claim tested**：EOS 优势是否在普通 batch=1 forward 中已经形成，以及它是否是 VSV×SLA 的非加性交互。
- **数据**：Cohort M 64 张图。
- **方法因子**：
  - `M00`：VSV off，SLA off；
  - `M10`：VSV on，SLA off；
  - `M01`：VSV off，SLA on；
  - `M11`：VSV on，SLA on。
- **固定 prefix**：使用 `M00` greedy 输出作为 teacher-forced prefix，在 `k={0,1,3,5,10}` token 处比较所有配置，避免不同生成轨迹造成混淆。
- **no-op controls**：完全不安装 wrapper；安装 wrapper 且 λ=0；λ=0 时直接返回原 tensor 的 strict no-op。
- **batch/cache controls**：batch=1；相同输入重复五份；cached one-token step；non-cached full-prefix step。
- **核心指标**：
  - `z_eos`、`p_eos`、`rank_eos`；
  - `margin_eos = z_eos - max(z_non_eos)`；
  - strongest content-token logit；
  - entropy、logit mean/std/RMS；
  - hidden norm 与各 SLA layer 的 logit scale。
- **交互量**：对每个 image/prefix 计算
  `I_margin = margin(M11)-margin(M10)-margin(M01)+margin(M00)`。
- **统计**：paired bootstrap 95% CI；同时报告中位数、IQR 和 collapse/non-collapse 分层结果。
- **成功标准**：如果 `I_margin > 0` 且 bootstrap CI 不跨 0，说明联合效应在 beam 之前已经形成；如果只有 repeated-batch/cache 条件出现差异，则转向实现 bug。
- **硬停止门**：
  - strict no-op 与完全关闭的 max absolute logit diff 超过 FP16 容差 `2e-3`；或
  - batch1 与 repeated-batch 对应行 diff 超过 `2e-3`；
  则暂停后续 block，先修数值/广播路径。
- **优先级**：MUST-RUN。

### B2：final path / SLA path counterfactual decomposition

- **Claim tested**：VSV 的影响是否通过 final path 和 SLA path 双重进入 mixed logits。
- **数据**：复用 B1 的 Cohort M 与 fixed prefixes，不重复生成 VSV。
- **需要缓存的张量**：
  - `F0`：无 VSV 的 final logits；
  - `F1`：有 VSV 的 final logits；
  - `A0`：无 VSV 的 SLA augmented logits；
  - `A1`：有 VSV 的 SLA augmented logits。
- **离线 counterfactual**：
  - `C00=(1-γ)F0+γA0`；
  - `C10=(1-γ)F1+γA0`（只让 final path 感受 VSV）；
  - `C01=(1-γ)F0+γA1`（只让 SLA path 感受 VSV）；
  - `C11=(1-γ)F1+γA1`（完整 VISTA）。
- **判定**：比较四者的 EOS margin、rank 与 content suppression。如果 `C10`、`C01` 均轻微，而 `C11` 明显跳变，支持 intervention dependency；如果仅 `C01` 异常，主因在 SLA path；如果仅 `C10` 异常，SLA 主要只是读取已有 final-path shift。
- **生成验证**：只在 Cohort M 中 16 个最稳定 collapse + 16 个对照上，运行 `C10/C01/C11` 的 beam5 decode，避免把离线 logit 现象误当生成结论。
- **优先级**：MUST-RUN。

### B3：真实 beam 路径追踪

- **Claim tested**：beam search 是异常来源还是放大器。
- **数据**：B2 的 32 张验证子集。
- **配置**：`M00/M10/M01/M11`，greedy 与 beam5；不加入 nucleus sampling。
- **逐 step/beam 日志**：
  - beam parent index、beam score、sequence length；
  - EOS logit/prob/rank/margin；
  - EOS 是否进入 top-2×beam candidates；
  - hypothesis finished step、length-normalized score；
  - cache reorder index 和 stopping reason。
- **判定模式**：
  - batch1 fixed-prefix 已有 EOS margin shift，beam 只保留/放大：支持 C1；
  - fixed-prefix 正常，beam expansion 后立即偏移：怀疑 broadcast/expanded state；
  - logits 正常，只有 finished hypothesis 评分选择 EOS：定位 scorer/length normalization；
  - cache 前正常、reorder 后异常：定位 cache/reorder path。
- **优先级**：MUST-RUN。

### B4：raw-logit calibration probe

- **Claim tested**：跨层 raw-logit 尺度失配是否放大 EOS 偏好。
- **数据**：Cohort M fixed-prefix 全部样本；生成验证使用 B3 的 32 张。
- **比较**：
  1. 原始 raw-logit mixing；
  2. 将 `A` 的 mean/std 匹配到 `F` 后再 mixing；
  3. RMS-only scale matching（不平移均值）。
- **约束**：gamma 固定 0.3，不做 gamma sweep；这是机制 probe，不是调参。
- **成功标准**：校准显著降低 EOS interaction margin 和 beam premature termination，同时不显著压低非 EOS top-token margin、caption length 或 object coverage。
- **失败解释**：若校准无效，则 scale mismatch 不是主要机制；保留 double-path 或 beam scoring 解释。
- **优先级**：MUST-RUN，但只在 B1/B2 无实现性失败后执行。

## 统一日志格式

每个 image/config/prefix/step 写一条 JSONL，至少包含：

```json
{
  "run_id": "E1_B1_M11",
  "image_id": 123,
  "cohort": "M",
  "method": {"vsv": true, "sla": true, "lambda": 0.17, "gamma": 0.3, "layers": [26, 30]},
  "decoder": {"type": "beam", "num_beams": 5, "length_penalty": 1.0, "early_stopping": false},
  "prefix_source": "M00_greedy",
  "prefix_len": 3,
  "beam_id": 0,
  "step": 0,
  "eos_id": 2,
  "eos_logit": 0.0,
  "eos_prob": 0.0,
  "eos_rank": 0,
  "eos_margin": 0.0,
  "top_non_eos_id": 0,
  "top_non_eos_logit": 0.0,
  "entropy": 0.0,
  "logit_std": 0.0,
  "beam_score": null,
  "parent_beam": null,
  "finished": false,
  "stop_reason": null,
  "record_status": "ok"
}
```

最终 summary 必须同时报告：完成数、缺失数、异常数、unique image IDs、empty、EOS@1/5/10、PTR@1/5/10、word/token length mean/median/P10/P90、object mentions、CHAIR-S/I。CHAIR 不得单独出现。

## Run Order and Milestones

| Milestone | 目标 | Runs | Decision Gate | 估算成本 | 风险 |
|---|---|---|---|---|---|
| M0 | 冻结 Cohort P/M 与配置 | manifest + 4-image dry run | ID/config/hash 完全一致 | <0.2 GPU-h | loader 顺序不稳定 |
| M1 | 排除 no-op、batch、cache 实现问题 | B1，先 4 图，再 64 图 | 任一硬停止门失败则先修代码 | 0.5–1 GPU-h | FP16 边界噪声 |
| M2 | 定位 double-path 贡献 | B2 fixed-prefix + 32 图生成验证 | path swap 能解释 EOS margin/termination 差异 | 1–2 GPU-h | counterfactual 实现需避免 inplace |
| M3 | 验证 beam 是来源还是放大器 | B3 32 图 × 4 方法 × 2 decoder | trace 可定位首次 divergence | 1–2 GPU-h | 日志量较大 |
| M4 | 检验 scale mismatch | B4 两种 calibration probe | EOS 改善且 coverage 不退化才进入下一阶段 | 1–2 GPU-h | 校准可能只掩盖症状 |
| M5 | 无偏发生率确认 | Cohort P 100 图，保留关键 4 方法和必要 decoder | paired incidence 与机制结论方向一致 | 2–4 GPU-h | 样本量仍不足以做最终 benchmark |

第一组总预算约 **6–11 RTX 4090 GPU-hours**，取决于 VSV tensor 缓存能否跨配置复用。禁止为每个 counterfactual 重复计算 image-specific VSV。

## Stop / Go 规则

- **STOP-IMPLEMENTATION**：strict no-op、duplicated batch 或 cache consistency 失败。结论改为实现路径异常，先修再跑。
- **GO-COUPLING**：batch=1 fixed-prefix 已出现正的 `I_margin`，且 path decomposition 显示 `C11` 非加性增强。进入 B3/B4。
- **GO-BEAM-BUG**：fixed-prefix 完全正常，但 expanded/cache/reorder 后首次偏移。集中修 beam compatibility。
- **GO-SCORER**：直到 logits 都正常，finished-hypothesis ranking 才选择 EOS。集中研究 length normalization/early stopping。
- **GO-CALIBRATION**：校准同时降低 EOS/PTR 且不损害 coverage。第二组实验再做完整 500 图与 gamma robustness。
- **NO-GO-MECHANISM**：interaction CI 跨 0，且 path swap/trace 不能复现稳定差异。停止 double-injection 叙事，回到 release VSV 实现和 checkpoint/version 差异。

## 第一组之后怎么做

1. **第二组：修复验证**——只测试第一组支持的机制修复，例如 calibrated mixing 或 decoupled SLA path；做完整 500 图、3 seeds（随机 decoder 才需要）和 CHAIR+coverage 联合评价。
2. **第三组：跨 decoding robustness**——greedy、beam2/3/5、nucleus；此时才加入 sampling variance 和多 seed。
3. **第四组：跨方法泛化**——选择 2–3 个技术家族，不预筛异常方法；复用统一 termination audit schema。

## 最大风险与缓解

- **选择偏差**：Mechanism cohort 富集 collapse；所有发生率结论只使用 Cohort P。
- **运行轨迹混杂**：不同方法自由生成会产生不同 prefix；B1/B2 使用 M00 teacher-forced fixed prefix。
- **重复算 VSV 导致成本膨胀**：每图缓存 VSV 与原始 hidden/logits，counterfactual mixing 离线完成。
- **只修 empty、不修 under-generation**：所有 block 同时报告 PTR、长度、coverage、object mentions 与 CHAIR。
- **校准只是强行阻止 EOS**：不能仅报告 empty 降低，必须检查 content-token margin、coverage 和语义信息量。

## Final Checklist

- [x] 第一组直接回答“问题在哪里产生”
- [x] 2×2 VSV/SLA 因子设计使用相同图像和 prefix
- [x] 区分 missing、exception、empty 与 short output
- [x] 包含 EOS logit/rank/margin/content suppression
- [x] 包含 final path / SLA path counterfactual decomposition
- [x] 包含 raw 与 calibrated mixing
- [x] 包含 strict no-op、batch expansion、cache/reorder controls
- [x] 包含真实 beam 内部 trace
- [x] 输出格式可直接扩展到其他 training-free 方法
- [x] nucleus 与大范围参数扫描被推迟到机制确认之后
