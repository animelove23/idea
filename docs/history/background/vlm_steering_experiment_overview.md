# VLM Steering 语义信息损失实验设计

## 1. 研究背景

现有 VLM hallucination mitigation / steering 方法通常以降低幻觉率为主要目标，但实际生成过程中经常伴随输出缩短、提前 EOS、空输出或信息量下降。

例如：

```text
Vanilla:
A small red car is parked beside a building.

Steered:
A car is beside a building.
```

object-level 指标可能变化很小，因为 `car` 和 `building` 都还存在，但实际上已经丢失：

```text
small   → attribute
red     → attribute
parked  → action / state
```

因此，本实验希望回答：

> **当 hallucination mitigation 使 VLM 输出变短时，模型究竟少说了什么？**

并进一步研究 steering 是否存在 **selective semantic suppression**：

> **steering 是否在删除幻觉的同时，也选择性删除某些真实语义信息？**

---

## 2. 实验核心目标

本实验主要研究：

\[
\Delta Length
\leftrightarrow
\Delta Semantic\ Information
\leftrightarrow
True / Hallucinated
\]

核心问题分三层：

### Question 1：输出发生了什么变化？

观察：

```text
Length ↓
Sentence Number ↓
EOS 提前
Empty Output ↑
ADJ ↓
VERB ↓
...
```

这一层描述 generation behavior。

### Question 2：具体少掉了什么语义信息？

将 VLM 输出拆成五种最核心、可以直接视觉验证的事实：

```text
Object
Attribute
Action
Relation
Count
```

然后比较 vanilla 和 steered 输出中的：

```text
retained
removed
added
```

从而知道输出缩短具体来自哪类 semantic component。

### Question 3：被删除的信息是好的还是坏的？

对每条 semantic fact 判断：

```text
supported
hallucinated
unknown
```

最终区分：

```text
真实信息被保留
真实信息被删除
幻觉被保留
幻觉被删除
```

目标统计形式：

| Semantic Type | True Retained | True Removed | Hall Retained | Hall Removed |
|---|---:|---:|---:|---:|
| Object |  |  |  |  |
| Attribute |  |  |  |  |
| Action |  |  |  |  |
| Relation |  |  |  |  |
| Count |  |  |  |  |

---

## 3. 整体实验原则

整个系统遵循一个原则：

> **不要让一个模块同时完成“拆分语义、判断真假、比较变化”等多个任务。**

整体流程：

```text
Image
  │
  ├───────────────┐
  ↓               ↓
Vanilla Caption   Steered Caption
  │               │
  └───────┬───────┘
          ↓
   Caption Analyzer
          ↓
Length / EOS / POS
          │
          ↓
 Semantic Decomposer
          ↓
     Semantic Facts
          │
     ┌────┴────┐
     ↓         ↓
  Verifier   Aligner
     ↓         ↓
True/Hall   Retain/Remove/Add
     └────┬────┘
          ↓
   Semantic Analysis
          ↓
Length × Semantic × Truth
```

---

## 4. Module 1：Caption / Generation Analyzer

### 目的

回答：

> **steering 后整句话发生了什么变化？**

不进行 semantic decomposition，也不判断 hallucination。

记录：

```text
caption
token_len
word_len
sentence_num
empty
EOS position
repetition / degeneration
```

同时使用 spaCy 做 caption-level POS 统计：

```text
NOUN
ADJ
VERB
ADP
NUM
...
```

例如：

```text
Vanilla:
ADJ = 8
NOUN = 12
VERB = 6

Steer:
ADJ = 3
NOUN = 11
VERB = 4
```

这可以观察语言形式变化，但第一版不要求把每个 POS 精确绑定到某条 fact。

### 输出

Caption Table：

```text
sample_id
image_id
method
decode
caption
token_len
word_len
sentence_num
empty
eos_step
NOUN_count
ADJ_count
VERB_count
ADP_count
NUM_count
```

### 作用

提供：

\[
\Delta Length
\]

以及：

\[
\Delta POS
\]

用于解释后续 semantic loss。

---

## 5. Module 2：Minimal Semantic Decomposer

### 目的

回答：

> **Caption 实际表达了哪些独立视觉事实？**

使用 DeepSeek 将 caption 拆成最小 semantic facts。

第一版只保留：

```text
object
attribute
action
relation
count
```

不构建复杂知识图谱，不做：

```text
entity ID
复杂 coreference
隐含关系补全
part-of
ownership
intent inference
复杂 subtype taxonomy
```

### 示例

输入：

```text
A red car is parked beside a building.
```

输出：

```json
{
  "facts": [
    {
      "fact_id": "f1",
      "type": "object",
      "fact": "car exists"
    },
    {
      "fact_id": "f2",
      "type": "attribute",
      "fact": "car is red"
    },
    {
      "fact_id": "f3",
      "type": "action",
      "fact": "car is parked"
    },
    {
      "fact_id": "f4",
      "type": "object",
      "fact": "building exists"
    },
    {
      "fact_id": "f5",
      "type": "relation",
      "fact": "car is beside building"
    }
  ]
}
```

### 核心规则

只提取：

> **caption 明确表达，并且原则上可以通过图片判断的事实。**

禁止根据常识补充：

```text
part-of
ownership
implicit possession
identity
intention
commonsense relation
```

例如：

```text
a tennis racquet in hand
```

不额外增加：

```text
hand belongs to tennis player
```

### 多实体与数量

例如：

```text
a surfboard ... another surfboard ...
```

不需要构建：

```text
surfboard_1
surfboard_2
```

可以拆成：

```text
surfboard exists
at least two surfboards exist
```

其中第二条作为 `count`。

### 重复描述

同一个事实重复多次，只保留一次规范化事实。

### 退化输出

例如：

```text
Palm Palm Palm Palm ... × 256
```

不强行调用 DeepSeek 拆事实。

直接标记：

```text
generation_status = degenerate_repetition
```

该样本仍进入 generation-level 分析，但：

```text
semantic_facts = N/A
```

### 输出

Fact Table 第一阶段：

```text
sample_id
image_id
method
decode
fact_id
type
fact
```

后续再加入：

```text
truth
change
```

---

## 6. Module 3：Fact Verifier

### 目的

Semantic Decomposer 只回答：

> **Caption 说了什么？**

Verifier 单独回答：

> **这条 fact 在图片中是真的吗？**

输出：

```text
supported
hallucinated
unknown
```

例如：

```text
car exists
→ supported

car is red
→ supported

car is beside bus
→ hallucinated
```

### 作用

把 semantic information 与 hallucination 连接起来。

最终每条 fact 都具有：

```text
type
fact
truth
```

从而区分：

> steering 删除的是错误信息，还是原本正确的信息。

---

## 7. Module 4：Vanilla–Steer Fact Aligner

### 目的

回答：

> **Vanilla 中的某条 semantic fact，在 steering 后发生了什么？**

比较同一图片、同一 decoding setting 下：

```text
Vanilla Facts
vs
Steered Facts
```

第一版只使用：

```text
retained
removed
added
```

例如：

```text
Vanilla:
car exists
car is red
bus exists
car beside bus

Steer:
car exists
bus exists
car beside bus
```

得到：

```text
car exists       → retained
car is red       → removed
bus exists       → retained
car beside bus   → retained
```

如果：

```text
Vanilla:
car is red

Steer:
car is blue
```

第一版直接处理为：

```text
car is red  → removed
car is blue → added
```

不额外定义 `modified`。

---

## 8. Module 5：Semantic Behavior Analyzer

### 目的

把以下信息连接起来：

```text
Generation Behavior
+
Semantic Type
+
Truth
+
Change
```

最终主分析：

\[
Semantic\ Type
\times
Truth
\times
Change
\]

核心表：

| Semantic | True Retained | True Removed | Hall Retained | Hall Removed |
|---|---:|---:|---:|---:|
| Object |  |  |  |  |
| Attribute |  |  |  |  |
| Action |  |  |  |  |
| Relation |  |  |  |  |
| Count |  |  |  |  |

再与：

```text
Δ token_len
Δ sentence_num
Δ POS
```

做联合分析。

---

## 9. 各模块如何合作

### Caption Analyzer

告诉我们：

> **句子短了多少？**

例如：

```text
90 tokens → 60 tokens
```

### Semantic Decomposer

告诉我们：

> **具体少了哪些类型的信息？**

例如：

```text
Object:    5 → 5
Attribute: 6 → 3
Action:    3 → 2
Relation:  4 → 2
Count:     1 → 0
```

### Verifier

告诉我们：

> **少掉的信息是真是假？**

例如：

```text
3 个 Attribute 被删除

其中：
2 个是真实信息
1 个是 hallucination
```

### Aligner

告诉我们：

> **每条具体 fact 是 retained、removed 还是 added？**

### Analyzer

把结果连接起来：

```text
Length ↓
      ↓
Attribute / Relation ↓
      ↓
部分真实 Attribute / Relation 被删除
      ↓
部分 Hallucinated Attribute / Relation 也被删除
```

最终判断 steering 的收益和副作用。

---

## 10. 最终两张核心表

### 10.1 Caption Table

一行一个 caption：

```text
sample_id
image_id
method
decode
caption
token_len
word_len
sentence_num
empty
eos_step
NOUN_count
ADJ_count
VERB_count
ADP_count
NUM_count
```

回答：

> **输出形式如何变化？**

### 10.2 Fact Table

一行一个 semantic fact：

```text
sample_id
image_id
method
decode
fact_id
type
fact
truth
change
```

例如：

| sample | type | fact | truth | change |
|---|---|---|---|---|
| vanilla_1 | object | car exists | supported | retained |
| vanilla_1 | attribute | car is red | supported | removed |
| vanilla_1 | relation | car beside bus | hallucinated | removed |

回答：

> **语义内容如何变化？变化的是正确事实还是幻觉事实？**

---

## 11. 第一版暂时不做

为了控制工程复杂度，第一版暂时不做：

```text
Fact-level POS alignment
Entity ID
复杂 coreference
subject-predicate-object-value graph
part-of relation
implicit possession
complex relation taxonomy
subjective / aesthetic taxonomy
token-level logit alignment
online semantic steering
```

这些内容只有第一阶段发现明确现象后再加入。

---

## 12. 第一阶段实验目标

第一阶段不是直接设计新 steering 方法，而是先证明：

> **steering 的输出缩短是否具有语义选择性。**

重点观察：

```text
Object 是否基本保留？
Attribute 是否明显减少？
Relation 是否明显减少？
Action 是否明显减少？
Count 是否容易消失？
```

并区分：

```text
True Fact Removal
vs
Hallucinated Fact Removal
```

如果发现：

```text
Object retention 高
Attribute / Relation true retention 明显低
```

则说明：

> steering 并不是单纯“少说一些”，而是在选择性压制某些 semantic information。

---

## 13. 第二阶段实验目标

如果第一阶段发现明确的 selective semantic suppression，再进一步分析：

```text
是否只是因为句子变短？
是否只是因为 Attribute / Relation 通常出现在后半段？
是否由提前 EOS 导致？
是否与特定 POS 有关？
是否与 steering strength 有关？
```

此时再加入：

```text
length-matched control
EOS control
position control
fact-level POS alignment
teacher forcing / logit analysis
```

---

## 14. 第三阶段方法目标

如果确认：

> 某些真实 semantic components 被 steering 过度删除，

再构建 training-free mitigation。

目标不是无条件让模型说更多，而是：

> **在不明显增加 hallucination 的情况下，恢复被 steering 误伤的真实语义信息。**

可以进一步探索：

```text
candidate-based regeneration
local weaker steering
semantic-aware decoding
verified fact recovery
```

---

## 15. 最终研究问题

> **When hallucination mitigation shortens VLM responses, what semantic information is actually removed?**

进一步：

> **Are the removed components hallucinated information, redundant description, or visually supported information?**

最后：

> **Can the unwanted semantic information loss be mitigated without bringing hallucinations back?**

---

## 16. 一句话总结

本实验不再只研究：

```text
Hallucination ↓
Length ↓
```

而是将输出缩短拆开：

\[
oxed{
\Delta Length
\rightarrow
\Delta Semantic Components
\rightarrow
True / Hallucinated
}
\]

通过 Caption Analyzer、Semantic Decomposer、Fact Verifier、Vanilla–Steer Aligner 和 Semantic Behavior Analyzer 的协作，最终判断：

> **steering 到底删掉了什么，以及这些删除到底是有益还是有害。**
