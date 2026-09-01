# EOS-00 实验范围与计划记录

## 目的

把最初的 beam5 空输出 observation 转化为可审计的 termination 机制实验，区分：

- VSV/SLA 在普通 forward 中已经改变 EOS；
- beam batch expansion 或 cache/reorder 造成实现偏差；
- beam candidate selection、累计分数或 finished hypothesis 放大已有差异；
- 空输出对 CHAIR 等 hallucination 指标造成 under-generation 偏置。

## 预注册指标

- EOS raw logit、probability、rank；
- `EOS margin = EOS logit - max(non-EOS logit)`；
- top non-EOS token/logit、entropy、logit scale；
- empty、首 token EOS、生成长度；
- beam parent、candidate、cache reorder、finished hypothesis 和累计 score。

## 归档文档

- `EOS-00_SOURCE_RESEARCH_GOAL.md`：现象、研究问题和机制假设原文。
- `EOS-00_SOURCE_EXPERIMENT_PLAN.md`：fixed-prefix、数值控制和 beam trace 计划原文。
- `EOS-00_SOURCE_EXPERIMENT_TRACKER.md`：归档时的执行状态快照。

## 注意

计划文件保留了实验开始时的假设，不能当成最终结论；后续结论以 EOS-01 至 EOS-07 的原始结果为准。
