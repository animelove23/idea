# 三组样本真实输入测试

使用原授权20图中的326667、195269、317188，6条caption。样本按明显缩短、多主体、颜色属性预选；未更改模型、提示、示例、输入文本及参考。fresh模式实际调用官方DeepSeek，未使用响应缓存。

实际请求：36；成功/失败状态：{'complete': 36}。生产事实36条，视觉命题27条；待完成视觉0条；异常pair 0组。

视觉命题标签：{'supported': 23, 'uncertain': 4}。共享命题会回填多个事实，不能混用两个分母。

M2对旧候选参考的联合F1：86.8%；同3图旧输出为83.8%。匹配33/40条候选参考，预测额外项3条。参考未经人工裁决，差异不能直接视作准确率变化。

与历史保存结果可精确匹配输入及请求身份的视觉命题25条，其中1条标签变化。这是历史诊断比较，不是受控三重复稳定性实验。

以下展示本轮模型输出，不把视觉模型标签视作人工真值。

## 样本 326667

词数：70 → 7；事实数：4 → 2。

**原文**

The image features a large bird, possibly a heron, flying over a body of water. The bird is captured in mid-flight, with its wings spread wide, as it soars above the water. The scene is set against a backdrop of rocks, adding to the natural ambiance of the location. The bird's wings are spread out, creating a sense of motion and grace as it glides through the air.

**Steer文本**

A bird is flying above a lake.

| 侧 | 主体 | 类型/槽位 | 值 | 对齐 | 视觉 | 原文证据 |
|---|---|---|---|---|---|---|
| original | bird | entity/existence | bird | retained | supported | bird; bird; bird |
| original | water | entity/existence | water | unresolved | supported | water; water |
| original | rocks | entity/existence | rocks | removed | supported | rocks |
| original | bird | attribute/size | large | removed | supported | large bird |
| steer | bird | entity/existence | bird | retained | supported | bird |
| steer | lake | entity/existence | lake | unresolved | supported | lake |

**未决与隔离记录**

- {"side": "original", "value": "water", "status": "unresolved", "reason": "granularity_mismatch", "alignment_axis": "semantic_unresolved", "visual_axis": "decided"}
- {"side": "steer", "value": "lake", "status": "unresolved", "reason": "granularity_mismatch", "alignment_axis": "semantic_unresolved", "visual_axis": "decided"}

## 样本 195269

词数：80 → 56；事实数：8 → 8。

**原文**

The image features a man and a young boy standing on a sandy beach, flying a kite together. The man is holding the kite string, while the boy is watching and enjoying the activity. The kite is soaring high in the sky, adding a sense of excitement to the scene.

In the background, there are several houses and a car parked nearby, indicating that the beach is likely a popular spot for families and friends to gather and have fun.

**Steer文本**

The image depicts a beach scene where two people are enjoying themselves. One person is holding a kite string, while another person is holding a kite string. They both stand on the sandy beach, with one person wearing a hoodie and the other person wearing shorts. The kite is flying high in the sky above them.

| 侧 | 主体 | 类型/槽位 | 值 | 对齐 | 视觉 | 原文证据 |
|---|---|---|---|---|---|---|
| original | man | entity/existence | man | unresolved | supported | man; man |
| original | boy | entity/existence | boy | unresolved | supported | boy; boy |
| original | beach | entity/existence | beach | retained | supported | beach; beach |
| original | kite | entity/existence | kite | retained | supported | kite; kite |
| original | kite string | entity/existence | kite string | retained | uncertain | kite string |
| original | houses | entity/existence | houses | removed | supported | houses |
| original | car | entity/existence | car | removed | uncertain | car |
| original | beach | attribute/material | sandy | retained | supported | sandy beach |
| steer | person | entity/existence | person | unresolved | supported | people; person; person; person; person |
| steer | kite string | entity/existence | kite string | retained | uncertain | kite string; kite string |
| steer | beach | entity/existence | beach | retained | supported | beach; sandy beach |
| steer | hoodie | entity/existence | hoodie | added | supported | hoodie |
| steer | shorts | entity/existence | shorts | added | supported | shorts |
| steer | kite | entity/existence | kite | retained | supported | kite |
| steer | sky | entity/existence | sky | added | supported | sky |
| steer | beach | attribute/material | sand | retained | supported | sandy beach |

**未决与隔离记录**

- {"side": "original", "value": "man", "status": "unresolved", "reason": "identity_unclear", "alignment_axis": "semantic_unresolved", "visual_axis": "decided"}
- {"side": "original", "value": "boy", "status": "unresolved", "reason": "identity_unclear", "alignment_axis": "semantic_unresolved", "visual_axis": "decided"}
- {"side": "original", "value": "kite string", "status": "retained", "reason": "same subject and slot", "alignment_axis": "decided", "visual_axis": "uncertain"}
- {"side": "original", "value": "car", "status": "removed", "reason": "same subject and slot", "alignment_axis": "decided", "visual_axis": "uncertain"}
- {"side": "steer", "value": "person", "status": "unresolved", "reason": "identity_unclear", "alignment_axis": "semantic_unresolved", "visual_axis": "decided"}
- {"side": "steer", "value": "kite string", "status": "retained", "reason": "same subject and slot", "alignment_axis": "decided", "visual_axis": "uncertain"}

## 样本 317188

词数：70 → 19；事实数：8 → 6。

**原文**

The image features a woman wearing glasses, standing on a beach and holding a cell phone in her hand. She appears to be looking at the screen of the phone, possibly checking messages or browsing the internet. The woman is dressed in a pink sweater, which adds a pop of color to the scene. The beach setting suggests a relaxed and leisurely atmosphere, with the woman enjoying her time outdoors.

**Steer文本**

The woman is wearing glasses and is holding a purple cell phone. She is standing on a sandy beach.

| 侧 | 主体 | 类型/槽位 | 值 | 对齐 | 视觉 | 原文证据 |
|---|---|---|---|---|---|---|
| original | woman | entity/existence | woman | retained | supported | woman; She; woman; woman |
| original | glasses | entity/existence | glasses | retained | supported | glasses |
| original | beach | entity/existence | beach | retained | uncertain | beach; beach |
| original | cell phone | entity/existence | cell phone | retained | supported | cell phone; phone |
| original | hand | entity/existence | hand | removed | supported | hand |
| original | screen | entity/existence | screen | removed | uncertain | screen |
| original | sweater | entity/existence | sweater | removed | supported | sweater |
| original | sweater | attribute/color | pink | removed | supported | pink sweater |
| steer | woman | entity/existence | woman | retained | supported | woman; She |
| steer | glasses | entity/existence | glasses | retained | supported | glasses |
| steer | cell phone | entity/existence | cell phone | retained | supported | cell phone |
| steer | beach | entity/existence | beach | retained | uncertain | beach |
| steer | cell phone | attribute/color | purple | added | supported | purple cell phone |
| steer | beach | attribute/material | sand | added | supported | sandy beach |

**未决与隔离记录**

- {"side": "original", "value": "beach", "status": "retained", "reason": "same subject and slot", "alignment_axis": "decided", "visual_axis": "uncertain"}
- {"side": "original", "value": "screen", "status": "removed", "reason": "same subject and slot", "alignment_axis": "decided", "visual_axis": "uncertain"}
- {"side": "steer", "value": "beach", "status": "retained", "reason": "same subject and slot", "alignment_axis": "decided", "visual_axis": "uncertain"}

## 本轮发现及处理顺序

1. **漏抽会制造伪新增。** 195269原文明确有“high in the sky”，M2未提取sky；Steer侧提取后，M3标为added。参考账本留下原文sky的extraction_missing，但生产M6仍会出现新增。需要在下一次单因素改动中检验实体覆盖及跨侧缺口审计，不能直接把这条解释成Steer产生新内容。
2. **多主体被合并。** 195269的two people、one person、another person被归入同一person；两个kite string也合并。M3把man/boy/person保留为identity_unclear，避免强行对齐，但无法分析两人的分别消退。下一步应先冻结个体/群体规则及成对例子。
3. **属性规范形式不一致。** 同为sandy beach，原文输出sandy、Steer输出sand；M3将材质判为retained，但固定M2计分对原文不给匹配。该候选差异需要审核，不能临时修改计分器抬分。
4. **主体不确定时属性仍支持。** 317188的beach为uncertain，sand为supported。新账本已经标记binding_unconfirmed=True，strict_parent_supported_eligible=False；原M6依旧保留原口径。研究分析应明确采用哪个分母。
5. **历史标签变化。** 可精确匹配的25条视觉输入中，317188的beach从supported变为uncertain。仅一次新调用，不能据此估计稳定性。

建议按“实体覆盖 → 个体/群体 → 属性规范值 → 视觉绑定”逐项实验，保留本轮输出作为基线，避免一次修改多个模块。

恢复检查：禁用网络后复用36个检查点，新增调用0；文档、视觉、分母账本和M6输出哈希保持一致。

## 输出与解释范围

- fresh/：请求及响应检查点、完整bundles、视觉队列、POS记录、分母账本及M6统计。
- fresh_metrics.json保留首次36次调用；fresh/metrics.json在恢复后反映该次恢复调用数0，完整调用证据在检查点。M6自身无LLM调用，不代表上游无调用。
- sample_metrics.json：调用、模型身份、计分及历史比较。
- m2_scores.jsonl、reference_ledger.jsonl、prediction_extras.jsonl：逐caption计分与未匹配项。
- same_query_visual_comparison.jsonl：只比较请求身份与视觉输入完全相同的命题。
- resume_check.json、sample_validation.json：恢复与9项样本结果完整性检查。
- 仅3图单轮样本测试；没有独立人工视觉gold，不报告视觉准确率或跨调用稳定性结论。
