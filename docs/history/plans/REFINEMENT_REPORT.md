# 规划评审摘要

本轮完成2次评审。最终评审8.86/10、REVISE；这是研究假设与方法价值仍待实验证实，不是论文已经验证或可以发表。

| 轮次 | 主要问题 | 收紧结果 | 尚待验证 |
|---|---|---|---|
| 1 | 主比较、误差传播、文献边界、EOS证据 | 固定ΔCAR与全属性分母；增加未决区间和原文审核；核对原始500对字段；明确与已有工作的有限区别 | 新机制是否存在 |
| 2 | 文字层面没有新的关键缺口 | 保留最小计划，停止为分数扩项目 | 停止控制后属性效应；方法是否超过统一减弱 |

用户当前询问研究规划，未请求启动实验。故不执行GPU/API实验，也不为达到技能默认9分门槛重复无实质文字修订。保留REVISE原结论；下一次有实验证据后再评价贡献。

原始评审见round-1-review.md和round-2-review.md；完整修订见round-1-refinement.md；交付版本为FINAL_PROPOSAL.md。

# Score Evolution

| Round | Problem Fidelity | Method Specificity | Contribution Quality | Frontier Leverage | Feasibility | Validation Focus | Venue Readiness | Overall | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 9.0 | 8.2 | 7.4 | 7.1 | 8.0 | 8.3 | 6.8 | 7.87（评审返回7.9） | REVISE |
| 2 | 9.4 | 9.1 | 8.7 | 8.6 | 8.8 | 9.3 | 8.2 | 8.86 | REVISE |

评分只评价方案。未把规划完成混同于科研结论成立。

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

# Round 2 Review

Reviewer: gpt-5.5, xhigh。

<details>
<summary>完整评审</summary>

7维评分：Problem Fidelity **9.4**；Method Specificity **9.1**；Contribution Quality **8.7**；Frontier Leverage **8.6**；Feasibility **8.8**；Validation Focus **9.3**；Venue Readiness **8.2**。

加权 Overall：**8.86/10**。Verdict：**REVISE**，但这是“论文级把握仍待实验验证”的 REVISE，不是“规划文字还缺关键结构”的 REVISE。修订案已经足够进入执行验证，不建议为冲分继续扩项目。

剩余阻塞最多两项：

1. **贡献强度仍是待验证假设**：对象条件属性省略在停止控制、共同锚点、固定全属性分母和人工误差对照后是否仍稳定存在，只能由后续实验回答；不是再写几段文献区分能解决的文字问题。

2. **venue readiness 依赖机制结果是否超过强基线**：若停止控制或统一减弱已解释/修复主要差异，项目应收缩为诊断论文或负结果；若 oracle/local intervention 明确超过统一减弱，才有方法贡献空间。当前规划已经正确把它写成继续/停止判据。

</details>
