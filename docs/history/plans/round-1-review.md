# Round 1 Review

Reviewer: gpt-5.5, xhigh。以下为原始返回，评分仅评估规划，不证明经验结论或发表潜力。

<details>
<summary>完整评审</summary>

结论：**REVISE**。方案没有明显 drift，且很好地收缩到文本 entity/attribute + POS 双粒度、保留 decompose/align、先分析再决定是否改 steer；但还没到 READY，主要卡在新颖性边界和统计承诺。

评分：Problem Fidelity 9.0；Method Specificity 8.2；Contribution Quality 7.4；Frontier Leverage 7.1；Feasibility 8.0；Validation Focus 8.3；Venue Readiness 6.8。加权 Overall = **7.9/10**。

必须修订项：
1. 把主 estimand 写死：例如“实体确定保留条件下的属性保留差异 ΔCAR”，配套 image-level bootstrap、未决上下界、抽取误差传播。parser 门槛只能证明测量可用，不能证明经验现象成立。
2. 对 SumGD / MESA / 2609.01888 做 claim-by-claim 区分表：SumGD 已覆盖 POS/选择性控制，MESA 已覆盖 fixed-prefix EOS 竞争，2609.01888 已覆盖保守输出与信息量权衡；本方案必须明确只 claim “对象条件属性省略 + 停止控制后的文本机制证据 + 最小改动选择规则”。
3. 机制实验需更保守：现有 greedy 文件只有 image_id/caption，无真实 EOS/token trace；因此 early-EOS 只能作为未知停止假设，必须等新 trace。VSV+SLA 文件名只是配置线索，不能替代运行配置核对。

Simplification：把 B 块先压成三件事：长度/位置诊断、固定前缀 logit trace、新生成干预；产物表也可先保留 protocol、units/alignment、pair_metrics、audit、findings。

Modernization：NONE；当前 analysis-first 不需要强行加新模型。

Drift Warning：NONE，但若后续转成“恢复真实视觉细节”，必须补盲评视觉事实核验。

</details>
