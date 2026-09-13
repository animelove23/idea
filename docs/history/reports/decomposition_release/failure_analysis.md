# 四条待复核 caption：原文、触发记录与原因分析

本报告只分析已有本地记录；未重新调用 API，未修改拆分结果。技术失败为 0，以下四条状态均为 needs_review。

| 样本 | 直接触发原因 | 本轮 API 请求 | 是否完成两次独立拆分 |
|---|---|---:|---|
| 43324_vanilla_beam5 | protocol_validation | 3 | 否 |
| 332570_vista_beam5 | repetitive_caption | 0 | 否 |
| 561517_vanilla_top_p | protocol_validation | 3 | 否 |
| 116887_vista_top_p | inconsistent_decomposition | 2 | 是 |

## 43324_vanilla_beam5

### 完整原文

```text
In the image, a shirtless man is sitting on the ground next to a surfboard. He is wearing a red hooded sweatshirt and appears to be resting or taking a break from surfing. The surfboard is positioned in front of him, occupying a significant portion of the scene.

In the background, another surfboard can be seen leaning against a wall, further emphasizing the surfing theme of the image.
```

### 实际触发点

三次请求均正常返回 JSON，但 f6 和 f15 都写成 `surfboard exists`，subject 都为 `surfboard`。它们引用的原文位置分别为 token 15 与 59。

原文明说 `another surfboard`：这是另一块板。问题是模型没有区分实体身份，当前去重键又只有 type/subtype/subject/fact，缺少实体 ID，于是将两块不同的冲浪板视为重复事实。拦截阻止了含糊实体绑定进入主表，但不能据此说原文存在重复事实。这是模型未遵守实体区分规则与工程表示不足的共同结果。

### 应如何表示

- `surfboard_1`：男子旁边/前方的板。
- `surfboard_2`：背景中、靠墙的另一块板。
- 两者的存在、位置、姿态分别绑定；不能直接删除第二条存在事实来让校验通过。

### 附加发现

原文同时写了 `shirtless` 和 `wearing a red hooded sweatshirt`，按通常理解有潜在矛盾。这不是本次直接触发点，也不应由拆分器擅自修成某一个版本；应保留两条原文声明并标记潜在冲突。三次重试还出现 shirtless 的 state/appearance 子类变化，提示该属性边界仍需固定。

诊断把握：两块板被同名表示是直接证据；原文服装描述仅标为潜在矛盾，未使用图片判断真假。

## 332570_vista_beam5

### 完整原文

```text
Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm
```

### 实际触发点

整条输出由 256 个 `Palm` 组成，命中整段周期重复检测。本轮 API 调用次数为 0，因此与 DeepSeek 网络、JSON 结构或 POS 无关。

### 原因与处理

可以确认上游 VLM 输出已退化。仅凭这份 caption 文件，无法确定是 steering、解码设置、模型本身还是停止条件导致；不能凭长度反推 EOS 或 token 上限。

`Palm` 可有多种词义，不能借助同图其他 caption 或图片补成“手掌/手机存在”。保留为退化生成，仍计入 Caption Table 和样本总数，但不赋成正常的零事实样本。

诊断把握：输入退化确定，上游具体机制未知。

## 561517_vanilla_top_p

### 完整原文

```text
The image features a delicious meal consisting of french toast, fries, and salad on a white plate. The plate has a knife placed alongside the food, and a fork is positioned on the left side. A slice of lemon can be seen on the right side of the plate, adding a refreshing touch to the meal. A fork and a knife are also visible within the image, indicating that the person enjoying the meal will likely use them for cutting and eating.
```

### 实际触发点

三次请求均正常返回 JSON，均因 f16 重复 `fork exists` 被拦截。模型还重复生成了 `knife exists`：

| 物体 | 首次存在事实/核心 token | 再次存在事实/核心 token |
|---|---|---|
| fork | f11 / 32 | f16 / 64 |
| knife | f9 / 24 | f17 / 67 |

与冲浪板例不同，这里最后一句的 fork/knife 更像对前面餐具的再次提及。原文没有 another/additional 明确指示新增实体。仅凭不同 token 位置，既不能认定新增一套餐具，也不能在所有类似文本里无条件认定同一实体。

### 可能的根因

模型在逐句枚举对象时，将“出现了一次名词”近似成“新增一条存在事实”，没有先做跨句实体归并。当前校验器能发现同名重复，但没有实体提及与实体身份之间的中间表示；因此同一条 Duplicate fact 错误同时覆盖了本例的重复提及和冲浪板例的不同实体同名。

### 附加语义问题

- 三次都把 `delicious` 标为 attribute.appearance。它是评价性/味觉判断，应按本项目协议归入 subjective，不能作为外观属性。
- 最后一句处于 `indicating ... will likely ...` 的解释性框架中，模型却单独输出 `person exists`。至少需要明确推测范围，不能自动把推测中的食客当作已观察对象。
- `refreshing touch` 的主语在 meal 与 slice of lemon 之间变化，显示评价归属也有不稳定性。

诊断把握：重复事实和错误分类为日志中的直接观察；fork/knife 属于同一实体是较强文本解释，但仍不是通过图片核实的结论。

## 116887_vista_top_p

### 完整原文

```text
A tennis player in a white uniform with a yellow tennis racquet in hand prepares to serve the ball.
```

### 实际触发点

这是四例中唯一实际完成两次独立拆分后，因集合不一致进入复核的样本。第一次 10 条，第二次 9 条；共有 9 条。

唯一差异：第一次多出 `hand belongs to tennis player`（relation.possession），第二次没有。

第一次给这条所属关系引用 token 3，即 `player in a white uniform` 中的 `in`；这不是手与运动员所属关系的原文依据。

### 原因判断

`racquet in hand` 的手是谁的，可以作自然语言常识解释，但当前“只拆显式关系”的协议尚未把这类省略的身体部位归属定义清楚。模型一次补出该关系，一次不补。按当前严格原文依据约定，我倾向不输出额外的 hand→player 所属事实，更不能使用指向制服的 token 3 作为证据。

### 更重要的共同遗漏

两次都没有单独保留 `tennis player is wearing uniform`，而原文 `player in a white uniform` 提供了这一关系。它的证据恰恰应来自 token 3 的 in。因此，第二次虽然没有那条额外所属关系，也不能直接称为完整正确的参考答案。

两次都正确保留了 `preparing to serve`，没有把它改写成正在发球。这部分属于共同保留的信息。

诊断把握：10/9 条差异及错引 token 是直接证据；是否将省略的身体部位归属纳入协议需要明确定义。共同遗漏也说明双次一致无法发现两次都漏掉的语义。

## 我的结论与修正优先级

1. 首先补齐轻量实体层：entity_id、原文 mention token 范围，以及它是新实体还是前文再提及。事实绑定 entity_id 后再判断重复；不能仅靠对象名称，也不能仅靠 token 是否相同。
2. 明确显式关系与省略/推测的边界，并检查证据 token 是否实际支持关系。不能把另一个短语中的 in 借来支撑任意所属关系。
3. 补充语义覆盖检查，尤其是穿戴、所属、状态与评价性用语。它与两次结果相互比较是不同的检查维度。
4. 细分 needs_review 原因：输入退化、实体身份未解决、重复提及、证据错配、语义分歧。当前整条隔离能保护主表，但会把大量已经正确的事实一起排除，不能把复核率等同于全部内容错误率。

这四条不能证明“DeepSeek 普遍不稳定”，也不能证明“只要两次一致就正确”。更具体的瓶颈是实体身份表示不足、显式/隐式关系的协议边界不清、缺乏独立的原文覆盖校验。优先补这些，比继续用笼统错误提示重复调用更有针对性。

原始审计：同目录 review_samples.jsonl；去重实现：项目 decomposition/schemas.py 第 52–54 行。
