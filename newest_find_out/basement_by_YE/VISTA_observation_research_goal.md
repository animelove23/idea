# VISTA Beam Search 提前终止问题：Observation、研究目标与机制泛化方向

## 1. 研究背景

当前研究对象是 VISTA，一种 training-free 的 LVLM hallucination mitigation 方法。VISTA 主要包含两个模块：

- **VSV（Visual Steering Vector）**：在语言模型中间表示上进行视觉方向的 steering。
- **SLA（Self-Logits Augmentation）**：读取若干中间层 hidden states，通过 LM head 得到中间层 logits，再与最终层 logits 混合。

当前复现重点是 LLaVA-1.5 在 CHAIR 图像描述任务上的生成行为，尤其是 greedy decoding 与 beam search 的差异。

本研究暂时不以“证明原论文有问题”为目标，也不预设作者主观利用了指标漏洞。当前目标是进行技术审计：确认现象、定位原因，并判断该现象是否属于更普遍的 training-free hallucination mitigation failure mode。

---

## 2. 当前 Observation

### 2.1 Beam search 下出现大量空输出

在当前复现中：

- VISTA 使用 greedy decoding 时，空输出极少，约为 `2/500`。
- VISTA 使用 beam search（beam size = 5）时，出现大量空输出。
- 当前一次运行中记录到约 `127/407` 个空输出，空输出率约为 `31.2%`。

其中 `407` 不是完整的 500 个有效样本，因此后续正式实验必须重新检查：

- 是否有运行中断；
- 是否有样本缺失；
- 是否有空字符串但记录仍存在；
- 是否有重复 image ID；
- 是否所有设置使用同一批图像。

当前数据只能作为初步 observation，不能直接作为最终论文结果。

---

### 2.2 VSV 与 SLA 单独运行基本正常，组合后才崩溃

当前小规模消融结果：

- VSV only + beam5：`0/10` 空输出；
- SLA only + beam5：`0/10` 空输出；
- VSV + SLA + beam5：`8/10` 空输出。

因此，目前最值得研究的现象不是“某一个模块直接导致 EOS”，而是：

> **VSV 和 SLA 在联合使用时可能出现非加性的耦合效应，而 beam search 又进一步放大了这种耦合。**

当前现象可以概括为：

\[
\text{VSV正常} + \text{SLA正常}
\not\Rightarrow
\text{VSV+SLA正常}
\]

更具体地说：

\[
\text{VSV} \times \text{SLA} \times \text{Beam Search}
\rightarrow
\text{Premature EOS / Empty Generation}
\]

---

### 2.3 Greedy 正常不能证明 beam 路径没有问题

同一套数据、checkpoint 和基本代码在 greedy 下工作正常，只能说明：

- 数据基本可用；
- checkpoint 没有整体损坏；
- VSV 和 SLA 的普通 forward path 基本可以运行；
- 模型具备正常生成能力。

但这不能排除：

- beam-expanded batch 导致的 shape 或 broadcasting 问题；
- cache reorder 或 beam index reorder 问题；
- VSV 与 SLA 在 beam-specific 路径中的状态耦合；
- 微小 logit ranking 变化被 beam search 放大；
- EOS 在 beam candidate 中被保留，并因累计分数或长度归一化最终获胜。

因此需要区分：

1. **真正的算法耦合；**
2. **联合代码路径或数值实现问题；**
3. **beam search 对已有异常的放大；**
4. **beam search 本身的实现兼容性问题。**

---

### 2.4 CHAIR 可能把“提前闭嘴”误判成“更少幻觉”

当前评价代码中，空 caption 不包含任何生成物体，因此不会被标记为 hallucinated，但它仍可能被计入 CHAIR-S 的 caption 总数。

这意味着：

\[
\text{Empty Caption}
\rightarrow
\text{No Hallucinated Object}
\rightarrow
\text{Favorable CHAIR-S Contribution}
\]

但是：

\[
\text{不说任何内容}
\neq
\text{视觉 grounding 更准确}
\]

因此，VISTA 在 beam search 下表现更好的 CHAIR 指标，可能混合了两部分：

\[
\text{Observed CHAIR Gain}
=
\text{Genuine Grounding Improvement}
+
\text{Generation Suppression Gain}
\]

其中第二部分指的是：

- 完全空输出；
- 很早输出 EOS；
- caption 变短；
- 提到的 object 数量减少；
- 回答变得更保守、更 generic；
- hallucination 降低，但 coverage / recall 也下降。

本研究不能只研究 empty caption。空输出只是 under-generation 最极端的一种表现。

---

## 3. 核心研究目标

### 总目标

找出 VISTA 中 VSV 与 SLA 联合使用时导致 premature termination 的真实原因，并判断这一机制能否扩展为更普遍的 training-free hallucination mitigation 现象。

完整目标链条为：

\[
\text{Hallucination Intervention}
\rightarrow
\text{Representation / Logit Interaction}
\rightarrow
\text{Termination Preference Shift}
\rightarrow
\text{Beam Amplification}
\rightarrow
\text{Under-Generation}
\rightarrow
\text{Metric Bias}
\]

---

## 4. 第一阶段目标：解释 VISTA 内部为什么出问题

第一阶段只研究 VISTA，不急于扩展其他方法。

需要回答以下问题。

### RQ1：问题的起点在哪里？

需要确定 premature EOS 是在以下哪个阶段产生的：

- 普通 batch=1 forward 中已经出现；
- beam input expansion 后出现；
- cache/reorder 后出现；
- beam candidate selection 时出现；
- finished hypothesis 与 length normalization 阶段才出现。

重点不是只看最终空输出，而是定位：

> EOS 的竞争优势究竟从哪一步开始形成。

---

### RQ2：EOS 是真的被增强，还是其他正常 token 被压低？

不能只记录 EOS raw logit。

需要考虑：

\[
M_{\text{EOS}}
=
z_{\text{EOS}}
-
\max_{v\neq \text{EOS}} z_v
\]

即 EOS 相对最强非 EOS token 的 margin。

可能出现两种情况：

#### 情况 A：EOS 本身上升

\[
z_{\text{EOS}}\uparrow
\]

#### 情况 B：EOS 不变，但正常内容 token 下降

\[
z_{\text{content}}\downarrow
\]

两种情况都会让 EOS rank 上升并进入 beam candidate。

因此核心研究对象应该是：

- EOS logit；
- EOS probability；
- EOS rank；
- EOS margin；
- top content token logits；
- distribution entropy；
- logit scale / variance。

---

### RQ3：VSV 是否通过两条路径被重复注入？

当前最重要的机制假设是：

1. VSV 修改中间层 hidden states；
2. 这些中间层继续传播并影响 final logits；
3. SLA 又读取已经被 VSV 修改过的中间层 hidden states；
4. SLA 将这些中间层 logits 再次混入最终 logits；
5. 因此 VSV 的影响可能通过两条路径进入最终输出。

表示为：

```text
VSV → modified intermediate hidden → final logits ─────────┐
                                                           ├→ mixed logits
VSV → modified intermediate hidden → SLA intermediate logits┘
```

这可能形成一种 **double injection / intervention dependency**。

需要判断：

- 问题主要来自 VSV 对 final path 的影响；
- 问题主要来自 VSV 对 SLA path 的影响；
- 两条路径单独都正常，只有同时存在才发生非线性耦合；
- 或者该现象只是实现层面的重复修改、hook 顺序或 inplace operation。

---

### RQ4：SLA 的跨层 logits 是否存在尺度失配？

SLA 将多个中间层 hidden states 直接通过同一个 LM head，再对 raw logits 求平均并与 final logits 混合。

潜在问题包括：

- 不同层 hidden norm 不一致；
- 不同层 logit variance 不一致；
- 中间层没有经过与最终层一致的 normalization；
- VSV 改变 hidden norm、方向或分布后，SLA 对这种变化高度敏感；
- 某些层的 EOS 偏置被 raw-logit averaging 放大。

因此需要判断：

> premature EOS 是否来自“未校准的跨层 logit 混合”，而不是 VSV 本身。

如果对中间层 logits 做 normalization、standardization 或 scale calibration 后问题消失，这会成为一个重要的机制结论。

---

### RQ5：VSV 在 \(\lambda=0\) 时是否严格等于关闭？

当前 VSV wrapper 可能不仅执行 steering，还涉及：

- float conversion；
- normalize；
- norm rescaling；
- half conversion。

因此：

\[
\lambda=0
\]

未必严格等价于：

\[
\text{VSV completely off}
\]

微小数值变化在 greedy 下可能没有影响，但在 beam search 下可能改变 token rank。

需要区分：

- 完全不安装 VSV；
- 安装 VSV，但 \(\lambda=0\)；
- strict no-op：\(\lambda=0\) 时直接返回原 tensor；
- 正常 VSV。

如果 no-op 路径仍然改变 EOS 行为，则问题可能是数值实现或 wrapper side effect，而不是算法意义上的 steering coupling。

---

### RQ6：beam search 是问题来源，还是放大器？

需要区分两种结论：

#### 结论 1：Beam 产生了问题

普通 forward 中 EOS 没有异常，只有 beam-expanded state、cache、reorder 或 scorer 才导致异常。

#### 结论 2：Beam 只是放大器

VSV+SLA 在普通 forward 中已经让 EOS rank 或 EOS margin 上升，但 greedy 只选择 top-1，仍然可以正常生成；beam5 会保留 top-5 路径，因此提前结束路径得以存活并最终获胜。

目前更合理但尚未验证的假设是：

\[
\text{VSV+SLA}
\rightarrow
\text{EOS进入候选区域}
\rightarrow
\text{Beam保留并放大}
\]

需要通过 fixed-prefix forward、beam trace、cache 对比和 duplicated batch control 将两种情况分开。

---

## 5. 第二阶段目标：判断机制能否泛化

VISTA 只是第一个 case study。

后续真正希望研究的不是：

> VISTA 是否存在一个特殊 bug。

而是：

> Training-free hallucination mitigation 是否普遍存在 under-generation bias，以及这些方法是否通过相似的 termination-margin shift 与 decoding dynamics 发生耦合。

---

### 5.1 泛化对象

后续计划收集多个顶会 training-free hallucination mitigation 方法，覆盖不同技术类型，例如：

- input / image contrastive decoding；
- logit contrastive decoding；
- activation steering；
- intermediate-layer decoding；
- attention intervention；
- beam-specific decoding；
- 多模块组合方法。

不能只挑表现异常的方法。需要建立相对统一的评估框架，比较：

- 原论文默认 decoding；
- greedy decoding；
- beam search；
- 不同 beam size；
- 不同模型；
- 不同 benchmark；
- 不同回答长度与任务类型。

---

### 5.2 泛化时研究的现象不应只定义为空输出

统一关注以下 under-generation 表现：

- Empty generation；
- EOS@step 1；
- EOS@step 5；
- PTR@1 / PTR@5 / PTR@10；
- 平均和中位生成长度下降；
- object mention 数下降；
- recall / coverage 下降；
- generic response 增多；
- hallucination score 变好，但语义信息量变少；
- EOS relative margin 上升。

核心假设应写为：

> Training-free hallucination mitigation may improve faithfulness partly by suppressing generation rather than solely by improving visual grounding.

而不能写成：

> 所有 training-free 方法都会直接增强 EOS。

后者过于狭窄，也容易被反例推翻。

---

### 5.3 希望找到的共同机制

VISTA 中可能发现的具体机制是：

- 多模块 intervention dependency；
- hidden-state effect 被重复注入；
- 跨层 logits 尺度失配；
- EOS relative margin 上升；
- beam candidate retention 放大提前终止。

向其他方法扩展时，希望寻找更高层的共同机制：

\[
\text{Intervention-induced distribution shift}
\rightarrow
\text{Content token suppression or EOS advantage}
\rightarrow
\text{Termination instability}
\]

即使其他方法不产生完全空输出，只要它们出现：

- caption 显著变短；
- object coverage 明显下降；
- EOS rank 系统性上升；
- beam search 下退化更严重；

也可以认为属于同一类 failure mode。

---

## 6. 预期研究贡献

如果后续证据成立，研究贡献可以分为三个层次。

### 贡献 1：现象层

揭示 hallucination reduction 和 genuine visual grounding improvement 不是同一个概念。

部分 training-free 方法可能通过降低输出信息量来获得更好的 hallucination 指标。

---

### 贡献 2：机制层

解释 training-free intervention 如何改变 EOS relative margin，并与 beam search 或其他 decoding dynamics 发生耦合。

VISTA 中的候选机制包括：

- VSV 对 final path 与 SLA path 的双重影响；
- 中间层 logits 未校准混合；
- 数值 wrapper side effect；
- beam candidate retention；
- cache 或 batch expansion 问题。

---

### 贡献 3：泛化与修复层

如果类似 termination instability 出现在多个方法中，则进一步提出：

- 统一的 under-generation audit protocol；
- termination-aware calibration；
- calibrated cross-layer logit mixing；
- decoupled intervention composition；
- beam-stable hallucination mitigation。

最终方法应尽量是通用修复，而不是只对 VISTA 写一个特殊规则。

---

## 7. 当前不能提前下的结论

在完成正式实验前，不应直接声称：

- 原论文造假；
- 作者故意利用空输出；
- VISTA 的全部结果无效；
- 所有 CHAIR improvement 都来自空输出；
- beam search 本身一定有 bug；
- VSV 与 SLA 的数学机制一定是双重注入；
- 该现象一定能泛化到所有 training-free 方法。

当前只能说：

> 初步复现观察到 VISTA 在 beam5 下存在明显的空输出和提前终止现象；该问题主要出现在 VSV 与 SLA 联合开启时，可能涉及模块耦合、termination preference shift 与 beam amplification。现有 CHAIR 评价方式可能无法充分惩罚这种 under-generation，因此有必要进行系统的机制分析与跨方法审计。

---

## 8. 给 Codex 的任务说明

请基于上述 observation 和研究目标设计实验，不要预设最终机制成立。

实验设计需要至少覆盖：

1. VSV、SLA、decoder 的 factorial comparison；
2. 同一批图像上的严格配对；
3. 完整性、missing output、empty output 和 short output 的区分；
4. fixed-prefix forward 分析；
5. EOS logit、rank、margin 和 content-token suppression；
6. VSV final path 与 SLA path 的拆解；
7. raw-logit mixing 与 calibrated mixing 对比；
8. batch expansion、cache、beam reorder 和 strict no-op controls；
9. beam search 内部路径追踪；
10. 从 VISTA 机制出发，提出后续跨方法泛化的统一日志格式与评估接口。

实验设计应优先回答：

> 问题究竟在哪里产生，为什么两个模块单独正常但组合后异常，以及 beam search 到底是根因还是放大器。

不要只进行参数扫描。参数扫描只能展示“哪里出现问题”，不能替代机制验证。
