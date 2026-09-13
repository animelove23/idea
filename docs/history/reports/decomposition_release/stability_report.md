# 关闭思考模式后的语义稳定性验证

日期：2026-09-09。模型保留用户配置的 deepseek-v4-pro。

## 最终结果

- 本地单元/集成测试：38 项通过。
- 固定语义案例：14/14 符合预先编写的预期，包括空输出和退化输出的处理。
- 真实 caption：12 条，来自 7 张图片，覆盖 vanilla/VISTA 的三种解码。
- 双次语义一致并接受：8 条，保留 102 条事实。
- 待复核：4 条；技术失败：0 条；未完成：0 条。
- 事实中存在辅助 POS 质量标记：9/102；它们仍保留主语义。
- 导出、原文偏移及 POS 回填检查：通过。

## 本次修正

1. 配置、CLI 和实际请求三处禁止开启思考；请求固定 disabled / temperature=0。
2. 统一实体称呼、持有/骑乘/吃草类别、所有格、场景与实体空间关系边界；保护否定、数量和 OR 的作用范围。
3. 禁止凭常识补 part-of 关系。格式或协议错误时给出具体校验反馈，而非原样盲重试。
4. 每条普通 caption 做两次互不读取对方结果的拆分。语义不同则隔离整个样本，不通过并集/交集掩盖遗漏或新增。
5. 语义一致但核心 token 不一致时保留事实，保存两套候选，确定的 token/POS 留空并标记。
6. POS 改用中型模型并保留小型模型对照。实际 smartphone 误标由模型改善，未手工强制改词性。
7. 所有样本状态保留在 caption_status.csv；复核样本的事实数留空，不能视为零事实或全部信息丢失。

8. 对同主体、同类别、完全相同肯定动作前缀的明确包含关系做保守去重，保留更完整声明与删除日志；否定、推测、OR、显式时间范围不合并。

## 逐条状态

| sample_id | 状态 | 已接受事实数 | 原因 |
|---|---|---:|---|
| 332570_vanilla_greedy | success | 17 |  |
| 352478_vanilla_greedy | success | 21 |  |
| 332570_vista_greedy | success | 5 |  |
| 54627_vista_greedy | success | 12 |  |
| 332570_vanilla_beam5 | success | 17 |  |
| 43324_vanilla_beam5 | needs_review | — | protocol_validation |
| 332570_vista_beam5 | needs_review | — | repetitive_caption |
| 331883_vista_beam5 | success | 6 |  |
| 332570_vanilla_top_p | success | 18 |  |
| 561517_vanilla_top_p | needs_review | — | protocol_validation |
| 332570_vista_top_p | success | 6 |  |
| 116887_vista_top_p | needs_review | — | inconsistent_decomposition |

## POS 质量标记

- `pos_models_disagree`：3 条事实。
- `semantic_anchors_disagree`：6 条事实。

## 证据及适用范围

模型候选来自同一修订 prompt 的一整批独立回归（decomposition_real_final / decomposition_gold_final），再本地执行最终去重及一致性检查，没有额外 API 调用，也未把不同轮次中较好的单条结果拼成成功率。早期目录保留诊断证据；本报告统计 decomposition_release 与 decomposition_gold_release。
固定案例用于已知协议的回归，其中一些与 prompt 示例相近，不能充当留出集准确率。两个同模型请求也可能共同遗漏或误解；接受表示本轮语义声明重复一致，不能证明对所有 caption 的语义完全正确。
主语义已接受的事实可以用于后续人工抽查；有 POS 标记的条目先不进入确定的词性统计。最终论文统计前仍需对更大规模跨图片 caption 做人工标注并报告接受率及排除比例。

- `facts.csv`：已接受事实。
- `review.md`：逐条原文、事实、核心词候选与质量标记。
- `review_samples.jsonl`：未接受样本的候选及分歧。
- `validation_report.json`：结构及回填校验。
- `../decomposition_gold_release/gold_evaluation.json`：固定例句预期对照。
- `../../decomposition/STABILITY_PROTOCOL.md`：接受标准和边界规则。
