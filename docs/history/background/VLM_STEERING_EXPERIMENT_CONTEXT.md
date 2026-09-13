# VLM Steering 语义变化评估实验：目标、上下文与实施计划

> **用途**：这是给服务器端模型 / Codex / Agent 的项目上下文文件。
> 在继续修改代码、设计模块或分析结果前，请先阅读本文件。
> 当前优先级不是把系统做复杂，而是先得到**稳定、准确、可追踪**的语义拆解与 Vanilla–Steer 对齐结果。

---

## 1. 项目背景

本项目研究 **VLM（当前主要是 LLaVA-1.5）在 hallucination mitigation / steering 之后，输出语义到底发生了什么变化**。

已有实验观察到：使用 VISTA 等 steering 方法后，输出通常会变短，同时幻觉指标可能改善。但仅看：

- caption length
- CHAIR hallucinated object
- real object count
- ACC / recall

无法回答一个更细的问题：

> **Steering 到底删掉了什么？**

输出变短可能来自多种原因：

1. 删除了 hallucinated information；
2. 删除了真实但不必要的重复表达；
3. 删除了真实 attribute；
4. 删除了真实 action；
5. 删除了真实 relation；
6. 删除了 count / instance distinction；
7. 只是语言表达变简洁，但核心语义仍然存在。

因此，不能简单把 `length ↓` 等同于 `generation capability ↓`，也不能只用 object-level 指标解释语义变化。

---

## 2. 核心研究问题

本项目当前最核心的问题是：

> **When hallucination mitigation shortens VLM responses, what semantic information is actually removed, retained, modified, or added?**

希望最终区分：

- **True Information Retained**
- **True Information Removed**
- **Hallucination Removed**
- **Hallucination Retained**
- **Hallucination Corrected**
- **Truth Corrupted**
- **True Information Added**
- **New Hallucination**

并进一步按语义类别统计：

- Object / Entity existence
- Attribute
- Action
- Relation
- Count

最终目标不是只得到一个 overall hallucination score，而是得到：

\[
\text{semantic component}
\times
\text{semantic change}
\times
\text{visual truth}
\]

例如未来希望回答：

> VISTA 是否能大量删除 hallucinated relation，但同时也过度删除 truthful relation？

如果这个现象稳定存在，后续再研究 **component-aware / selective training-free steering**。

---

## 3. 当前阶段的第一性目标

当前不要急着设计新的 steering 方法。

当前第一目标是：

> **稳定、完整地把 Vanilla / Steer caption 中明确表达的语义拆出来，并可靠判断两边哪些语义相同、消失、新增或变化。**

优先级：

1. **语义拆解完整性**
2. **Vanilla–Steer 对齐准确性**
3. **结果可追踪、可人工检查**
4. 之后才是 hallucination verification
5. 最后才是新的 mitigation 方法

不要为了追求复杂度增加不必要模块。

---

## 4. 当前实验对象

当前主要实验设置：

- 模型：LLaVA-1.5
- 数据：COCO2014
- 对比：
  - Vanilla output
  - VISTA / steering output
- decoding 可能包括：
  - greedy
  - beam
  - top-p
- 当前语义拆解模型：
  - DeepSeek API
- 当前 v6 测试：
  - 8-shot
  - temperature = 0
  - thinking disabled

当前 v6 在简单合成句上表现很好，但真实长 caption 仍然存在：

- 漏拆 attribute；
- 一个 fact 内合并多个原子语义；
- 复杂修饰语未独立化；
- 同一句重复运行时部分 attribute 有时出现、有时消失；
- 某些语义整段漏掉；
- speculation scope 存在不稳定；
- 真实 caption 的高复杂度不能被简单合成集分数掩盖。

因此当前不应把合成集高 F1 当作真实语义拆解已经解决。

---

## 5. 当前语义表示目标

### 5.1 概念上的五类语义

最终分析希望统一为五类：

### Object / Entity existence
表示实体存在。

例：

```text
There is a bench.
There are giraffes.
```

### Attribute
表示单个实体的属性、状态、材质、颜色、形状等。

例：

```text
bench.material = wood
grass.height = tall
shirt.color = white
```

### Action
表示主体执行的动作、行为或姿态。

例：

```text
person.stand
giraffe.look
dog.sleep
```

### Relation
表示实体之间的空间、持有、穿戴、包含等关系。

例：

```text
person holds hot_dog
vase on table
giraffe behind giraffe
```

### Count
表示明确的数量信息。

例：

```text
giraffe count = 2
shoe_pair count = 2
```

---

## 5.2 与当前 v6 schema 的关系

**不要为了五类概念重新推翻当前 v6 Decomposer。**

当前 v6 可能仍使用：

```text
type = entity / attribute / relation / other
category = action / spatial / counting / material ...
```

这属于当前工程 schema。

后续可以在统计阶段把它映射到五个概念类，例如：

```text
relation/action -> Action
relation/spatial -> Relation
attribute/counting -> Count
entity/* -> Object / Entity existence
```

当前阶段优先保持 parser 稳定，不要因为 schema 美观而重新设计所有 few-shot。

---

## 6. 整体流水线

当前正式计划：

```text
Vanilla Caption
      │
      ▼
Existing v6 Decomposer
      │
      ▼
Coverage Audit
      │
      ├──────────────────────┐
                             │
Steer Caption                │
      │                      │
      ▼                      │
Existing v6 Decomposer       │
      │                      │
      ▼                      │
Coverage Audit               │
      │                      │
      └──────────┬───────────┘
                 ▼
        Joint Pair Alignment
                 │
                 ▼
        Aligned Semantic Facts
                 │
                 ▼
     Visual Verifier Interface
          （当前只留接口）
                 │
                 ▼
        Semantic Transition
          （后续阶段实现）
```

核心原则：

\[
\boxed{
\text{Independent Extraction}
+
\text{Joint Alignment}
}
\]

Vanilla 与 Steer 的拆解必须彼此独立。

对齐阶段可以同时看两边。

---

# 7. Module 1：Existing Decomposer

## 目的

回答：

> **这个 caption 明确说了什么？**

Decomposer 的职责是语言解析，不是视觉判断。

## 规则

Decomposer：

- 只看当前 caption；
- 不看另一侧 caption；
- 不看图片；
- 不判断 hallucination；
- 不因为句子矛盾而自动修正；
- 不用世界知识补充 caption 没明确表达的信息；
- 尽量拆成可以独立变化的 atomic semantic claims。

### 例子

原句：

```text
The field is filled with tall grass.
```

理想语义至少包括：

```text
field contains grass
grass is tall
```

而不是只保留：

```text
field is filled with tall grass
```

因为 steering 之后可能保留 `contains grass`，但丢失 `tall`。

---

# 8. Module 2：Coverage Audit

## 为什么需要

当前真实 caption 中存在 **共同遗漏**：

一个语义如果 Decomposer 没有拆出来，后面：

- Alignment 看不到；
- Visual Verifier 看不到；
- 最终统计也看不到。

更危险的是，如果 Vanilla 拆出来而 Steer 没拆出来，可能被错误统计为：

```text
semantic removed
```

但其实只是：

```text
extraction failure
```

因此需要一个非常轻量的 Coverage Audit。

---

## Coverage Audit 的唯一职责

回答：

> **原句中是否还有明确表达、但现有 facts 没覆盖的视觉语义？**

Coverage 是 **recall checker**，不是第二个 Decomposer。

---

## 例子 1：Tall grass

原句：

```text
The field is filled with tall grass.
```

已有：

```text
field contains grass
```

Coverage 发现：

```text
grass is tall
```

未覆盖。

只补：

```text
attribute(grass, height, tall)
```

---

## 例子 2：Natural light

真实 caption 中：

```text
The vase is positioned near a window,
allowing natural light to illuminate the scene.
```

如果当前 facts 只有：

```text
vase near window
```

而完全没有：

```text
natural light illuminates scene
```

Coverage 应把后者标记为 uncovered semantic content。

---

## Coverage 禁止做的事情

Coverage **不能**：

- 修改已有 fact；
- 删除已有 fact；
- 合并已有 fact；
- 重新拆整句；
- 判断 fact 是否真实；
- 根据图片修正；
- 解决矛盾；
- 推理 caption 没明确说的信息；
- 自动重复调用直到“完美”。

每条 caption 只运行一次。

---

## Coverage 输出

建议：

```json
{
  "caption_id": "...",
  "added_facts": [
    {
      "id": "...",
      "type": "...",
      "category": "...",
      "fact": "...",
      "assertion": "...",
      "polarity": "...",
      "source": "...",
      "added_by_coverage": true
    }
  ]
}
```

没有遗漏：

```json
{
  "caption_id": "...",
  "added_facts": []
}
```

程序只负责把 `added_facts` 追加到已有结果。

---

# 9. 当前不单独实现 Semantic Dedup

当前阶段**不要增加一个 LLM semantic dedup 模块**。

原因：

- 又增加一个模型判断步骤；
- 可能错误合并不同信息；
- 会增加 pipeline 不稳定性；
- 当前首要问题是 recall 和 alignment。

如果将来同一 semantic claim 出现多次，可以优先在统计阶段使用结构化 key 做合并，而不是让额外 LLM 决定。

原则：

> **先完整保留，再结构化统计；不要在早期阶段过度“聪明地清理”。**

---

# 10. Module 3：Joint Entity Alignment

## 为什么需要

Vanilla 和 Steer 是独立拆解的，因此：

```text
Vanilla e1
Steer e3
```

可能实际上是同一个语义实体。

而同一个 caption 中也可能有多个：

```text
person
dog
plate
surfboard
```

所以不能只用 canonical name 对齐。

---

## 对齐阶段允许同时看两边

输入：

- Vanilla raw caption
- Steer raw caption
- Vanilla entities / facts
- Steer entities / facts

**这里可以同时看两边。**

这是设计要求，不是 information leakage。

真正需要独立的是 extraction，不是 alignment。

---

## Entity Alignment 判断依据

当有多个同类实体时，要结合：

- mention
- attribute
- action
- relation
- surrounding entities
- 原句中的局部上下文

构造实体的 semantic signature。

### 例子

Vanilla：

```text
person_1 = red shirt + holds cup
person_2 = standing + beside table
```

Steer：

```text
person_a = wearing red + holds cup
person_b = standing + near table
```

应：

```text
person_1 <-> person_a
person_2 <-> person_b
```

---

## 无法确定时

不能强行对齐。

输出：

```text
ambiguous
```

例如：

Vanilla：

```text
Two men are standing beside a car.
```

Steer：

```text
One man is looking at the car.
```

无法知道 Steer 的 man 对应 Vanilla 的哪一个 man。

不要猜。

---

# 11. Module 4：Fact Alignment

## 目的

回答：

> **Steering 后这个语义发生了什么？**

事实状态固定为：

- retained
- removed
- added
- modified
- ambiguous

---

## retained

两边表达完整等价的语义。

允许同义表达。

例如：

```text
beside(person, bicycle)
next_to(person, bicycle)
```

可判 retained。

---

## removed

Vanilla 明确表达，但 Steer 没有表达。

例如：

```text
Vanilla:
grass is tall

Steer:
A grassy field with giraffes.
```

如果 Steer 原文和 facts 都没有 tall：

```text
tall -> removed
```

---

## added

Steer 出现 Vanilla 没有的语义。

例如：

```text
Vanilla:
two pairs of shoes on bench

Steer:
two pairs of black shoes on bench
```

如果 Vanilla 没有 black：

```text
black -> added
```

---

## modified

只用于：

> **同一个实体、同一个 semantic slot、值发生改变。**

例如：

```text
shirt.color:
white -> blue
```

判：

```text
modified
```

但是：

```text
shoes.state = old
shoes.color = black
```

不是同一个 slot。

因此：

```text
old -> removed
black -> added
```

而不是 modified。

---

## ambiguous

用于：

- entity correspondence 不确定；
- 两边只部分语义重合；
- decomposition 粒度不一致；
- 无法安全判断；
- 对侧原文其实表达了某事实，但 decomposition / coverage 没提取出来。

最后一种情况使用：

```text
reason = extraction_gap
```

这样可以避免：

\[
\text{parser error}
\rightarrow
\text{fake semantic removal}
\]

---

# 12. 对齐模块的重要限制

Alignment：

- 不看图片；
- 不判断真假；
- 不新增 fact；
- 不删除 fact；
- 不重新 decomposition；
- 不因为 VISTA 理论上“应该更好”而影响判断；
- 不为了降低 ambiguous 强行匹配。

Alignment 的职责只有：

> **判断两个已经存在的 semantic claims 如何对应。**

---

# 13. Alignment 输出建议

```json
{
  "pair_id": "...",

  "entity_alignment": [
    {
      "original_entity": "o_e1",
      "steer_entity": "s_e3",
      "global_entity": "g1",
      "status": "matched"
    }
  ],

  "fact_alignment": [
    {
      "original_fact_ids": ["o_f3"],
      "steer_fact_ids": ["s_f4"],
      "semantic_type": "attribute",
      "status": "retained",
      "reason": "same entity and same material claim"
    },

    {
      "original_fact_ids": ["o_f8"],
      "steer_fact_ids": [],
      "semantic_type": "relation",
      "status": "removed",
      "reason": "no corresponding semantic relation in steer"
    }
  ]
}
```

要求：

- 每个 main fact 都有去向；
- 避免同一 fact 被重复用于多个主要 alignment；
- unmatched 必须显式保留；
- ambiguous 不隐藏。

---

# 14. Module 5：Visual Verifier Interface（当前不实现）

## 最终目的

之后用 Qwen-VL / Qwen3-VL 或其他多模态模型判断 atomic fact：

```text
supported
hallucinated
uncertain
```

但**当前阶段暂不做视觉判断**。

只留接口。

---

## 为什么幻觉判断放在 Alignment 之后

如果 Vanilla 和 Steer 有同一个 semantic claim：

```text
bench is wooden
```

先对齐以后，可以构造一个 shared claim。

未来视觉模型只需要判断一次：

```text
material(bench, wood)
```

避免 Vanilla / Steer 分别调用两次 verifier 导致 judge fluctuation。

同时，Alignment 不知道视觉真假，因此不会出现：

> “这个事实是假的，所以我不愿意把它和另一边匹配”

这种 bias。

---

## 接口建议

```python
verify_claim(
    image,
    fact,
    entity_context
) -> verification_result
```

当前 placeholder：

```json
{
  "claim_id": "...",
  "fact_ids": ["..."],
  "label": "pending",
  "evidence": null
}
```

未来支持：

```text
supported
hallucinated
uncertain
```

当前全部：

```text
pending
```

---

# 15. 后续的 Semantic Transition 分析

视觉验证完成后，Alignment × Verification 才形成最终结果。

例如：

| Vanilla fact truth | Alignment | Steer truth | 最终含义 |
|---|---|---|---|
| supported | retained | supported | True Information Retained |
| supported | removed | — | True Information Loss |
| hallucinated | removed | — | Hallucination Removed |
| hallucinated | retained | hallucinated | Hallucination Retained |
| hallucinated | modified | supported | Hallucination Corrected |
| supported | modified | hallucinated | Truth Corrupted |
| — | added | supported | True Information Added |
| — | added | hallucinated | New Hallucination |

未来最终统计按五类 semantic component 分开：

```text
Object
Attribute
Action
Relation
Count
```

---

# 16. 当前阶段暂时不要做的事情

当前不要：

1. 实现视觉 hallucination verifier；
2. 设计新的 component-aware steering；
3. 加复杂 semantic dedup 模型；
4. 用图片帮助文本拆解；
5. 让 Alignment 回写 Decomposer；
6. 为了降低 ambiguous 强行猜；
7. 自动修改 prompt 追求更漂亮数字；
8. 根据少量案例提前得出 steering 的论文结论。

先看真实实验结果。

---

# 17. 当前阶段需要实现的工程产物

至少生成：

```text
coverage.jsonl
alignment.jsonl
verification_pending.jsonl
TEST_REPORT.md
```

其中：

### coverage.jsonl
记录每个 caption：

- 原始 fact 数；
- coverage 新增 fact；
- source span。

### alignment.jsonl
记录每个 Vanilla–Steer pair：

- entity mapping；
- fact mapping；
- retained / removed / added / modified / ambiguous；
- extraction_gap。

### verification_pending.jsonl
只建立未来视觉验证需要的数据接口：

```text
label = pending
```

### TEST_REPORT.md

需要展示：

- Coverage 补了多少事实；
- 具体补了什么；
- retained / removed / added / modified / ambiguous 数量；
- 实际成功对齐例子；
- 实际失败例子；
- extraction_gap；
- 多同类实体导致的 ambiguous；
- 当前模块的明显错误。

---

# 18. 当前实验策略

先跑小规模真实 Vanilla–Steer pair。

不要先大规模跑。

流程：

```text
1. 跑 v6 decomposition
2. 跑一次 Coverage
3. 人工抽查 Coverage
4. 跑 Joint Alignment
5. 人工抽查 Alignment
6. 总结 error pattern
7. 再决定是否改 prompt / schema
```

重点不是立即提高一个总体 F1，而是确认：

> **错误到底发生在哪个模块。**

因此所有中间结果必须保存。

---

# 19. 当前评估关注点

需要特别观察：

### Coverage
- 是否能补长句漏拆？
- 是否开始过度拆解？
- 是否添加原文没有的信息？

### Entity Alignment
- 多个 person / dog / surfboard 时是否稳定？
- 是否错误强制一对一？
- 是否能正确保留 ambiguous？

### Fact Alignment
- synonym 是否能 retained？
- attribute slot 是否正确？
- removed / added 是否被 extraction gap 污染？
- modified 是否过度使用？
- 一个 fact 是否被重复匹配？

---

# 20. 研究的长期方向

如果后续实验验证：

```text
Object retention 很高
Attribute retention 明显下降
Relation retention 明显下降
```

同时 hallucination removal 确实发生，那么可以形成核心 observation：

> Steering does not uniformly shorten VLM generation; it selectively suppresses specific semantic components.

之后再研究：

### Component-aware steering

例如：

- component-specific alpha；
- component-preserving projection；
- component-aware logit rescue；
- component-aware contrastive decoding；
- protection of truthful relation / attribute subspaces。

但这些都属于**下一阶段**。

当前不要提前实现。

---

# 21. 给后续服务器模型的工作原则

在继续项目时，请始终遵守：

### 1. 不改变研究问题

研究重点不是“让 caption 更长”，而是：

> **解释 steering 到底删除了什么语义，以及删除的是 hallucination 还是真实信息。**

### 2. 不把 parser 能力当成 VLM 能力

DeepSeek 可以帮助结构化 VLM 输出，但不能替 VLM：

- 补全没说的信息；
- 修复模糊表达；
- 修正事实错误；
- 猜真实场景。

目标是：

> **normalize wording, preserve meaning, preserve ambiguity, never repair the caption.**

### 3. Extraction 与 Alignment 分开

```text
Independent Extraction
Joint Alignment
```

不要根据 Vanilla 的结构去指导 Steer decomposition。

### 4. 当前简单优先

如果一个新模块不能明确解决当前真实错误，不要增加。

### 5. 所有判断必须可追踪

任何：

```text
removed
modified
ambiguous
extraction_gap
```

都必须能回到：

- 原 caption；
- source span；
- 原 fact；
- 对侧 fact。

### 6. 先保存失败案例

不要自动调 prompt 消灭错误。

先记录 error pattern，再决定是否值得修改。

---

# 22. 当前一句话任务定义

当前服务器端任务可以概括为：

> **在不修改现有 v6 Decomposer 主体的前提下，为 Vanilla / Steer 独立拆解结果增加一次只查漏的 Coverage Audit，然后构建能够联合查看两边原文和结构、先对齐实体再对齐事实的 Pair Alignment 模块；准确输出 retained / removed / added / modified / ambiguous，并识别 extraction_gap；视觉 hallucination 判断当前只留接口，不实现。先在少量真实 pair 上运行并报告真实错误，再决定下一步。**

---

## 23. 当前最重要的判断标准

如果必须在“复杂”与“可靠”之间选择：

\[
\boxed{\text{可靠优先}}
\]

如果必须在“强行给出答案”与“保留不确定性”之间选择：

\[
\boxed{\text{保留 ambiguous}}
\]

如果必须在“自动修复 VLM 表达”与“忠实保存 VLM 表达”之间选择：

\[
\boxed{\text{忠实保存}}
\]

整个评估系统的可信度依赖于这三个原则。
