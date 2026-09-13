# 首次 8-shot 对照测试报告

**结论：few-shot 对部分语义边界有帮助，但本轮没有证明整体准确率提高，尚不能称为稳定拆解。** 32 次逻辑调用已经完成；零示例与 8-shot 主测均为 13/14 条结构有效。数量、子组和指代方面有局部改善，同时仍有遗漏、过度解释及拆分粒度变化。

## 已落实的监督与测试设置

- 冻结 8 条示例、159 条事实。第 19 条一般人群 e4 及其存在事实保留，hand 保留；人物具体类别、一般与具体用途、明确推测行为保留。
- busy/comfortable 等模糊评价暂不计入；为统一该边界，示例中 delicious/refreshing 属性移出，caption 原文不改。至少三人的计数指向 person 类别，不把锚点数量当物理人数。
- 同一套规则分别使用 0-shot 与 8-shot。14 条测试 caption 来自 7 张图片，与示例的 8 张图片完全分离；第 04、14、24、29 条做第二次 8-shot 独立运行。
- 模型 deepseek-v4-pro，官方 https://api.deepseek.com，temperature=0，请求明确设置 thinking.type=disabled；不使用缓存，每次最多一次重试，4 路并发。未在测试中途修改示例或规则。
- 用户已明确授权本次冻结数据包和测试。发送 caption 与示例结构，不发送图片、实验 method/decode 或真假标签。所有 verification 保持 pending。
- 这些测试 caption 已在之前的助手标注过程中看过。因此这是开发集对照，**不是独立人工金标准、不是盲测**。14 条也只覆盖 7 张图片，样本存在图片内关联。

## 执行结果

| 指标 | 0-shot 主测 | 8-shot 主测 |
| --- | ---: | ---: |
| caption 数 | 14 | 14 |
| 首次请求结构通过 | 12/14（85.7%） | 13/14（92.9%） |
| 含一次修复后结构通过 | 13/14（92.9%） | 13/14（92.9%） |
| 最终失败 | 1 | 1 |

另外 4 次重复调用有 3 次结构通过、1 次失败。合计 **29/32 次逻辑调用成功**，实际发出 **36 次 HTTP 请求**（32 次初始请求、4 次重试）。API 返回的累计用量为 256,890 prompt tokens、52,174 completion tokens。本地 39 项单元测试通过；这些软件测试不计作模型语义正确样本。

不要将 92.9% 称为准确率。也不比较两个条件的事实总行数：双方失败的 caption 不同，且多拆一条事实可能是错误。

## 格式失败定位

| 调用 | 具体问题 | 重试结果 |
| --- | --- | --- |
| 08_s0_r1 | f21.source 写成 `her hair`，原文为 `Her hair` | 相同问题未修复，失败 |
| 24_s8_r1 | e7.mention 写成 `the broccoli and rice combination`，原文为 `The broccoli and rice combination` | 相同问题未修复，失败 |
| 24_s8_r2 | e9.mention 出现同一大小写问题 | 相同问题未修复，失败 |
| 05_s0_r1 | `count_eq` 配 `several`，模糊量误用精确比较器 | 修为 `count` 后通过 |

三个最终失败均为逐字溯源校验问题，不是 API 认证、网络或输出截断问题。失败原文保留，未暗中改大小写或把它们混入成功结果。当前修复提示仅给出通用错误，没有指出具体字段路径和错误片段，这很可能是两次仍未修好的原因之一。

## 语义复核：哪些改善，哪些仍失败

按照测试前的 semantic_review_plan.json 对全部 14 条主测做了助手定性复核，详见 [逐条原文、实体和事实对照](REVIEW_CASES.md) 与 [复核记录](semantic_review.json)。它不是独立人工标注，因此不产出伪精确的语义准确率。

较明确的局部改善：

- **05 瓶子子组**：0-shot 把 near sink 和 right side 都挂到一般瓶子组；8-shot 保留 some/others 两个子组，空间范围更忠实。
- **14 三个男人**：8-shot 补出原先遗漏的 `count=3`，将衣服、衣服颜色和 wears 拆开。
- **20 消防车与人群**：8-shot 补 several 计数、street 路径关系及 stand，同时保留人群一般组和具体子组。
- **21 行李箱**：8-shot 补 handle exists，并将丢失 past 含义的 walk 改成 walk_past，重复句没有重复计数。
- **04 / 15 指代**：8-shot 更好复用 man、suitcase 或 himself 对应的锚点，保留 asserted 与 speculative 的区别。

仍需解决的问题和回退：

- **实体化与语义强度**：08 把 smile 当 object；07 将 his reindeer friends 写成 belongs_to，可能把朋友/关联解释为所有权。
- **最小独立单位**：14 首轮将 hands 和 feet crossed 合成一条；26 两种提示都把静态 bowl sits 多拆成 sit 动作。8-shot 的 full_of 也未把满与容纳关系拆开。
- **明确数量遗漏**：29 两种条件均漏 `multiple forks`；24 的 0-shot 漏 `several`，并把大小不同的子组混到同一锚点。24 的 8-shot 没有有效输出，不能算作修复成功。
- **关系参照丢失**：29 的 8-shot 把碗相对 table 的 left/right 改成无参照的属性；20 两种条件均遗漏 float 位于车的 back 这一更具体位置。
- **推测内容被改写**：25 的两种条件都把观察/等待 truck's activities 简化成 truck，把 related to work or daily activities 简化成 related_to(truck,men)。语气保留了，但语义对象和替代分支丢失。
- **存在事实取舍和指代仍漂移**：明确身体部位、一般组与具体成员、the table/the sidewalk 的锚点与 exists 未完全稳定。

这说明问题不能只归因于“没有 few-shot”。人工先验确实有用，但示例覆盖不足、开放谓词的改写空间、类型边界和修复反馈仍会共同影响结果。

## 重复稳定性

| 样本 | 首轮 / 次轮事实数 | 观察 |
| --- | --- | --- |
| 04 | 21 / 20 | 主要动作保留；次轮少一个 sidewalk exists |
| 14 | 17 / 21 | 身体部位存在事实取舍，以及 crossed 的合并/拆分变化 |
| 24 | 失败 / 失败 | 均因 mention 大小写，无法比较有效文档 |
| 29 | 19 / 19 | 主要事实内容接近，但 table/person 指代和 focused 谓词变化 |

三个都有有效输出的重复对中，原始 JSON 完全一致为 **0/3**。这不是“语义一致率 0%”：编号、来源片段和同义表达也会导致 JSON 不同。但是 04/14 确有事实取舍或粒度变化，不能都归因于措辞。

## 下一轮建议（本轮未修改或重跑）

1. 先改结构修复反馈：给出字段路径、错误片段和对应原文，必要时仅对唯一匹配的大小写溯源做可审计修复；不改原句，不改事实含义。
2. 为 multiple/several、显式具体实体存在性增加只报 warning 的本地检查，禁止由锚点个数推算人数、禁止直接自动补事实。
3. 用真实边界案例补强监督：some/others 子组、身体部位分别 crossed、静态 sits、相对 table 的左右、activity 与 truck 的差异。若将本轮样本用于提示调优，下一轮最终评估必须换图片。
4. 后续对齐同时检查语义和参照实体，区分规范化词形变化与真正的事实变化，不能用 JSON 或 predicate 字符串相等替代语义一致性。

原始证据：protocol.json、jobs.json、prompt_0.txt、prompt_8.txt、inputs.jsonl、checkpoints/、results.jsonl、summary.json。运行输入和提示词摘要在完成后复核一致。当前默认 8-shot 为可复现的开发版本，尚未获得语义稳定性验收。
