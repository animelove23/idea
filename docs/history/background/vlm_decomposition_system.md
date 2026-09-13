> 实现更新（2026-09-09）：当前采用用户截图指定的 Minimal Decomposer v1，五类事实与 caption 层 POS 独立统计。以 [当前说明](decomposition/README.md) 和 [当前协议](decomposition/STABILITY_PROTOCOL.md) 为准。下文保留原始设计作为历史记录。

# VLM 输出语义拆分系统设计

## 1. 目标

本系统用于分析 **VLM 在 hallucination mitigation / steering 前后，句子缩短时具体丢失了什么语义信息，以及丢失的信息是真实信息还是幻觉信息**。

核心研究关系：

\[
\Delta \text{Length}
\leftrightarrow
\Delta \text{Semantic Facts}
\leftrightarrow
\text{True / Hallucinated}
\]

系统只保留两类核心数据：

1. **Caption-level**：记录长度、句子数、EOS、空输出等整体生成行为。
2. **Fact-level**：把 caption 拆成 Object、Attribute、Action、Relation、Count、Scene、Subjective 等语义事实。

**POS 不单独构成一套评估系统，只作为每条 semantic fact 的辅助语言学属性。**

```text
Caption
   │
   ├──→ Caption Table
   │      length / sentence_num / EOS / empty
   │
   ↓
DeepSeek 拆 semantic facts
   │
   ↓
spaCy 给 fact 对应原文 token 标 POS
   │
   ↓
Fact Table
   │
   ├──→ Verifier：supported / hallucinated / unknown
   │
   └──→ Aligner：retained / removed / added / modified
```

---

## 2. Caption Table

**一行 = 一条模型输出。**

建议字段：

| 字段 | 含义 |
|---|---|
| `sample_id` | 唯一样本 ID |
| `image_id` | 图片 ID |
| `method` | vanilla / vista / other |
| `decode` | greedy / beam5 / top_p |
| `caption` | 原始模型输出 |
| `char_len` | 字符长度 |
| `word_len` | 单词数 |
| `token_len` | VLM tokenizer 生成 token 数 |
| `sentence_num` | 句子数 |
| `empty` | 是否为空输出 |
| `eos_step` | EOS 出现位置，可选 |

示例：

```json
{
  "sample_id": "54627_vanilla_greedy",
  "image_id": 54627,
  "method": "vanilla",
  "decode": "greedy",
  "caption": "A red car is beside a blue bus.",
  "char_len": 31,
  "word_len": 8,
  "token_len": 10,
  "sentence_num": 1,
  "empty": false,
  "eos_step": 10
}
```

Caption Table 主要回答：

> steering 后整句话缩短了多少？

---

## 3. Fact Table

**一行 = 一个 semantic fact。**

例如：

```text
A red car is beside a blue bus.
```

拆成：

```text
f1: car exists
f2: car is red
f3: bus exists
f4: bus is blue
f5: car is beside bus
```

最终 Fact Table：

| fact_id | type | subtype | subject | fact | POS |
|---|---|---|---|---|---|
| f1 | object | existence | car | car exists | NOUN |
| f2 | attribute | color | car | car is red | ADJ |
| f3 | object | existence | bus | bus exists | NOUN |
| f4 | attribute | color | bus | bus is blue | ADJ |
| f5 | relation | spatial | car | car is beside bus | ADP |

后续再加入：

```text
truth
change
```

例如：

| type | subtype | fact | POS | truth | change |
|---|---|---|---|---|---|
| object | existence | car exists | NOUN | supported | retained |
| attribute | color | car is red | ADJ | supported | removed |
| relation | spatial | car beside bus | ADP | supported | retained |

Fact Table 主要回答：

> steering 后具体丢掉了什么信息？

---

## 4. Semantic Fact 分类协议

第一版固定使用 7 个大类。

### 4.1 Object

描述某个对象存在。

```text
a horse
a car
a traffic light
```

结构：

```json
{
  "type": "object",
  "subtype": "existence",
  "subject": "car",
  "fact": "car exists"
}
```

### 4.2 Attribute

描述对象属性。

推荐 subtype：

```text
color
size
material
shape
state
appearance
other
```

例如：

```text
a red car
a wooden table
a large dog
an open door
```

结构：

```json
{
  "type": "attribute",
  "subtype": "color",
  "subject": "car",
  "fact": "car is red"
}
```

### 4.3 Action

描述对象动作或姿态。

推荐 subtype：

```text
motion
pose
interaction
other
```

例如：

```text
a man running
a horse grazing
a person riding a bicycle
a dog sitting
```

### 4.4 Relation

描述两个对象之间的关系。

推荐 subtype：

```text
spatial
possession
comparison
other
```

例如：

```text
car beside bus
cat under table
man holding umbrella
```

### 4.5 Count

描述明确或近似数量。

推荐 subtype：

```text
exact
approximate
group
```

例如：

```text
five horses
several people
a group of birds
```

注意：普通冠词 `a/an` 不自动转换成 count=1。

### 4.6 Scene

描述整个画面或环境。

推荐 subtype：

```text
location
weather
lighting
environment
```

例如：

```text
the scene is outdoors
it is a cloudy day
the image is taken at night
the setting is a beach
```

### 4.7 Subjective

描述不能直接等同于客观视觉事实的解释性内容。

推荐 subtype：

```text
emotion
intention
aesthetic
inference
```

例如：

```text
the horse looks happy
the scene feels peaceful
the people appear to be enjoying themselves
```

这类内容必须单独保留，因为句子缩短可能主要删除它们，但这不能直接算作“真实视觉信息损失”。

---

## 5. DeepSeek Semantic Decomposer

DeepSeek **只负责把 caption 拆成 semantic facts**。

DeepSeek 不负责：

```text
判断 hallucination
判断图片是否支持
比较 vanilla 和 steer
计算 POS
决定 steering 是否有效
```

输入只包含：

```text
caption
+
spaCy 分好的 token 编号
```

不要提供：

```text
图片
COCO reference
method=vanilla/vista
truth label
```

---

## 6. spaCy Token 结构

先对 caption 使用 spaCy：

```text
A red car is beside a blue bus.
```

得到：

```json
[
  {"id": 0, "text": "A", "pos": "DET"},
  {"id": 1, "text": "red", "pos": "ADJ"},
  {"id": 2, "text": "car", "pos": "NOUN"},
  {"id": 3, "text": "is", "pos": "AUX"},
  {"id": 4, "text": "beside", "pos": "ADP"},
  {"id": 5, "text": "a", "pos": "DET"},
  {"id": 6, "text": "blue", "pos": "ADJ"},
  {"id": 7, "text": "bus", "pos": "NOUN"}
]
```

建议保存：

```text
id
text
lemma
pos
start
end
sentence_id
```

其中真正关键的是：

- `id`：供 DeepSeek fact 引用。
- `pos`：最终附加到 semantic fact。
- `start/end`：以后如需对齐 LLaVA tokenizer / logits，可以继续使用。

---

## 7. DeepSeek 输出结构

推荐每个 fact 固定输出：

```json
{
  "fact_id": "f2",
  "type": "attribute",
  "subtype": "color",
  "subject": "car",
  "fact": "car is red",
  "semantic_token_ids": [1]
}
```

最重要的字段：

```text
fact_id
type
subtype
subject
fact
semantic_token_ids
```

### `fact_id`

当前 caption 内唯一编号。

### `type`

主语义类别：

```text
object
attribute
action
relation
count
scene
subjective
```

### `subtype`

更细的语义类别，例如：

```text
attribute.color
attribute.size
relation.spatial
action.interaction
scene.weather
```

### `subject`

说明事实是关于谁的。

例如：

```text
red car
blue bus
```

必须保留：

```text
car is red
bus is blue
```

不能只保存 `red`、`blue`。

### `fact`

将原 caption 中的信息规范化成一句简短、明确、独立的声明。

这是后续 vanilla / steer fact alignment 的主要语义单位。

### `semantic_token_ids`

记录：

> 原句中真正承担该 fact 新增语义信息的核心词。

这是连接 semantic fact 和 POS 的关键。

---

## 8. semantic_token_ids 规则

### Object

记录对象核心词：

```text
red car
→ car
```

### Attribute

只记录属性值核心词：

```text
red car
→ red

large dog
→ large

wooden table
→ wooden
```

### Action

记录动作核心词：

```text
man is running
→ running

horse is grazing
→ grazing
```

### Relation

记录关系核心词：

```text
car beside bus
→ beside

cat under table
→ under
```

### Count

记录数量核心词：

```text
five horses
→ five

several people
→ several
```

### Scene

记录整体场景判断的核心表达：

```text
cloudy day
→ cloudy

scene is outdoors
→ outdoors
```

### Subjective

记录主观判断核心词：

```text
horse looks happy
→ happy

scene feels peaceful
→ peaceful
```

这样避免所有 semantic 类型都被对象名词重复污染。

---

## 9. POS 如何附加到 Fact

不需要新的模型。

DeepSeek 输出：

```json
{
  "fact_id": "f2",
  "type": "attribute",
  "subtype": "color",
  "subject": "car",
  "fact": "car is red",
  "semantic_token_ids": [1]
}
```

spaCy 已知：

```text
token 1 = red
POS = ADJ
```

Python 直接查询：

```python
fact["pos"] = [
    token_map[i]["pos"]
    for i in fact["semantic_token_ids"]
]
```

最终：

```json
{
  "fact_id": "f2",
  "type": "attribute",
  "subtype": "color",
  "subject": "car",
  "fact": "car is red",
  "semantic_token_ids": [1],
  "pos": ["ADJ"]
}
```

即：

```text
DeepSeek：
判断“这是什么语义信息”

spaCy：
判断“承担这条语义信息的核心词是什么词性”
```

两者最终存进同一条 fact。

---

## 10. 最终 facts.csv

建议字段：

```text
sample_id
image_id
method
decode

fact_id
type
subtype
subject
fact

semantic_token_ids
pos

truth
change
```

示例：

| image_id | method | fact_id | type | subtype | subject | fact | POS | truth | change |
|---|---|---|---|---|---|---|---|---|---|
| 54627 | vanilla | f1 | object | existence | car | car exists | NOUN |  |  |
| 54627 | vanilla | f2 | attribute | color | car | car is red | ADJ |  |  |
| 54627 | vanilla | f3 | object | existence | bus | bus exists | NOUN |  |  |
| 54627 | vanilla | f4 | attribute | color | bus | bus is blue | ADJ |  |  |
| 54627 | vanilla | f5 | relation | spatial | car | car beside bus | ADP |  |  |

拆分阶段：

```text
truth = 空
change = 空
```

后面的模块再填。

---

## 11. 后续 Verifier 接口

Verifier 判断：

```text
supported
hallucinated
unknown
not_applicable
```

然后写入：

```text
truth
```

Semantic Decomposer 和 Verifier 必须分开。

这样可以区分：

```text
事实拆错了
```

和：

```text
事实真假判错了
```

---

## 12. 后续 Vanilla / Steer Aligner

同一张图片：

```text
Vanilla facts
vs
Steer facts
```

判断：

```text
retained
removed
added
modified
```

然后写入：

```text
change
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

---

## 13. 最终核心分析

主分析不是 POS，而是：

```text
Semantic Type
×
Truth
×
Change
```

目标表：

| Semantic | True retained | True removed | Hall retained | Hall removed |
|---|---:|---:|---:|---:|
| Object |  |  |  |  |
| Attribute |  |  |  |  |
| Action |  |  |  |  |
| Relation |  |  |  |  |
| Count |  |  |  |  |
| Scene |  |  |  |  |
| Subjective |  |  |  |  |

回答：

> steering 到底删除了什么？

以及：

> 删除的是幻觉，还是原本正确的信息？

---

## 14. POS 的作用

POS 只作为辅助解释变量。

例如先发现：

```text
Attribute true removal = 35%
```

再进一步：

```text
Attribute + ADJ:
true removal = 45%

Attribute + other POS:
true removal = 20%
```

这样才有理由讨论：

> Attribute loss 是否与 adjective-like lexical realization 有关。

因此：

```text
Semantic = 主分析
POS = 辅助解释
```

---

## 15. 推荐工程目录

```text
decomposition/
├── config.py
├── schemas.py
├── caption_parser.py
├── pos_parser.py
├── semantic_decomposer.py
├── fact_builder.py
├── run_decomposition.py
└── prompts/
    └── semantic_decompose_v1.txt

outputs/
├── captions.csv
├── decomposed.jsonl
├── facts.csv
└── failed_samples.jsonl
```

后续：

```text
verification/
└── fact_verifier.py

alignment/
└── vanilla_steer_aligner.py

analysis/
├── semantic_analysis.py
├── length_analysis.py
└── pos_analysis.py
```

---

## 16. 推荐执行顺序

```text
Step 1
读取 vanilla / steer captions

Step 2
生成 Caption Table

Step 3
spaCy 对 caption 分词并标 POS

Step 4
把 caption + token IDs 交给 DeepSeek

Step 5
DeepSeek 输出 semantic facts

Step 6
Python 用 semantic_token_ids 查询 POS

Step 7
生成 facts.csv

Step 8
人工抽查 100–200 条 caption

Step 9
冻结 prompt 和 schema

Step 10
构建 fact verifier

Step 11
填入 True / Hallucinated

Step 12
构建 Vanilla / Steer fact aligner

Step 13
分析：
ΔLength
vs
Semantic Fact Loss
vs
True / Hallucinated
```

---

## 17. 第一阶段暂时不要做

第一版先不要加入：

```text
复杂 knowledge graph
完整 subject-predicate-object-value ontology
在线 steering
复杂视觉核验
复杂 coreference 模型
logit 对齐
semantic embedding matching
```

第一阶段只要求稳定实现：

```text
Caption
→ Semantic Facts
→ POS 属性
→ facts.csv
```

先把 decomposition 做稳定，再进入 verifier 和 aligner。

---

## 18. 相关工作定位

### 粗粒度语言层

**SumGD — Summary-Guided Decoding for Mitigating Hallucinations in Large Vision-Language Models, Findings of NAACL 2025**

参考：

```text
POS-level analysis
spaCy POS tagging
不同词性的视觉依赖差异
```

### 细粒度语义层

**FaithScore — Evaluating Hallucinations in Large Vision-Language Models, Findings of EMNLP 2024**

参考：

```text
自由文本 → atomic facts
decomposition 与 visual verification 分离
```

**CAPTURE**

参考：

```text
Object
Attribute
Relation
```

**SC-Captioner, ICCV 2025**

参考：

```text
生成文本前后的 semantic element 增删分析
```

本系统扩展为：

```text
Object
Attribute
Action
Relation
Count
Scene
Subjective
```

---

## 19. 一句话定义

> 本系统首先使用 DeepSeek 将 VLM caption 拆解为 Object、Attribute、Action、Relation、Count、Scene 和 Subjective 七类原子语义事实，并通过 spaCy 将每条事实的核心原文 token 映射到 POS；最终以“一行一个 semantic fact”的结构保存数据，后续分别加入真实性标签和 steering 前后变化标签，从而分析句子缩短究竟来自幻觉删除、真实视觉信息损失，还是主观/非核心描述减少。

核心数据关系：

\[
oxed{
Caption

ightarrow
Semantic Fact

ightarrow
POS

ightarrow
Truth

ightarrow
Change
}
\]

最终研究：

\[
oxed{
\Delta Length
\leftrightarrow
\Delta Semantic Components
\leftrightarrow
True/Hallucinated
}
\]
