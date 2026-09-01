# Research Contract: VISTA 组合干预的 termination instability

## Selected Idea

- **Description**: 审计 VISTA 中 VSV 与 SLA 联合使用时出现的 premature EOS，定位 termination preference shift 在普通 forward、跨层 logits mixing 与 beam search 中的形成和放大过程，并判断 CHAIR 改善是否混入 under-generation gain。
- **Source**: `newest_find_out/basement_by_YE/VISTA_observation_research_goal.md`
- **Selection rationale**: 已有 paired pilot 显示 VSV-only 与 SLA-only 各为 0/10 空输出，而联合 beam5 为 8/10；问题具有明确可复现实例、机制可证伪性和跨方法泛化潜力。

## Core Claims

1. VSV+SLA 的联合效应可能在进入 beam scorer 前就提升 EOS relative margin，beam search 主要保留并放大该偏移。
2. 候选机制是 VSV 同时影响 final path 与 SLA path，以及未校准的跨层 raw-logit mixing；两者需通过 counterfactual path decomposition 验证，不作为预设结论。
3. 结论仅限当前 release/checkpoint/configuration，除非后续跨方法与跨模型实验支持泛化。

## Method Summary

第一组实验使用同图像、同 teacher-forced prefix 的 2×2 factorial：VSV on/off × SLA on/off。逐 prefix 记录 EOS logit/probability/rank/margin、content-token suppression、entropy 和 logit scale，并计算交互项。随后缓存无/有 VSV 的 final logits 与 SLA logits，构造 path-swap counterfactual，定位 VSV 影响进入 mixed logits 的路径。

真实 beam5 trace 只在 fixed-prefix 机制成立后运行，用于判断 EOS 候选何时被保留、finished hypothesis 如何获胜。Strict no-op、batch repeat×5、cached/non-cached consistency 是硬停止门；任何实现性不一致都优先于算法机制解释。

## Experiment Design

- **Datasets**: MSCOCO 2014 validation；100-image 无偏 prevalence cohort 与 64-image mechanism cohort。
- **Baselines**: VSV off/SLA off、VSV-only、SLA-only、VSV+SLA。
- **Metrics**: EOS logit/prob/rank/margin、PTR@1/5/10、empty、token/word length、object coverage、CHAIR-S/I。
- **Key hyperparameters**: LLaVA-1.5-7B；VSV λ=0.17；SLA γ=0.3、layers 26–30；beam5；max_new_tokens=512。
- **Compute budget**: 第一组预计 6–11 RTX 4090 GPU-hours；sanity-first。

## Baselines

| Method | Dataset | Metric | Score | Source |
|---|---|---|---|---|
| VISTA greedy | COCO val subset | empty rate | 2/500 (0.4%) | reproduced artifact |
| VISTA beam5 | COCO val subset | empty rate | 127/407 (31.2%, incomplete run) | reproduced artifact |
| VSV-only beam5 | selected 10 collapse images | empty rate | 0/10 | diagnostic pilot |
| SLA-only beam5 | selected 10 collapse images | empty rate | 0/10 | diagnostic pilot |
| VSV+SLA beam5 | selected 10 collapse images | empty rate | 8/10 | diagnostic pilot |

## Current Results

| Method | Dataset | Metric | Score | Notes |
|---|---|---|---|---|
| VISTA combined beam5 | COCO val subset | empty rate | 31.2% | 407/500 completed，不能作为最终 benchmark |

## Key Decisions

- 第一组先做 fixed-prefix 因果定位，不做大范围参数 sweep 或 nucleus sampling。
- Mechanism cohort 只用于机制灵敏度，发生率只由无偏 prevalence cohort 报告。
- 论文字符串（无末尾句号）和 paper-literal SLA indices 26–30 作为主设置；release default 作为 sensitivity control。
- CHAIR 必须与 empty/PTR/length/coverage 一起报告。

## Status

- [x] Idea selected
- [x] Diagnostic pilot reproduced
- [ ] Sanity instrumentation implemented
- [ ] Mechanism cohort results
- [ ] Prevalence cohort results
- [ ] Full dataset results
- [ ] Ablation studies
- [ ] Paper draft

