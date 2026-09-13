# 最新 eight-shot：原文与实际对齐结果

主体展示第3轮最终输出，未进行人工纠正。校验失败的单边 ambiguous 不表示系统已匹配两条事实，也不表示原文语义真的模糊。每对末尾列出三轮变化。other保留显示，但不进入主线统计。

## 415015 花瓶与花

**Vanilla 原文**

> The image features a vase filled with a variety of dried flowers, including daisies and sunflowers. The vase is placed on a table, and the flowers are arranged in a visually appealing manner. The vase is positioned near a window, allowing natural light to illuminate the scene. The combination of the vase, flowers, and the window creates a pleasant and inviting atmosphere.

**Steer 原文**

> The image depicts a glass vase filled with various types of flowers and grasses. The vase is placed on a table next to a window. The flowers and grasses are arranged in such a way that they create a visually appealing bouquet.

**第3轮实际最终结果**

| Vanilla fact | Steer fact | status | reason |
| --- | --- | --- | --- |
| f1 [entity; asserted; positive] There is a vase. | f1 [entity; asserted; positive] There is a glass vase. | retained | same_fact |
| f2 [entity; asserted; positive] There are dried flowers. | f2 [entity; asserted; positive] There are flowers. | retained | same_fact |
| f3 [entity; asserted; positive] There are daisies. | — | removed | not_expressed |
| f4 [entity; asserted; positive] There are sunflowers. | — | removed | not_expressed |
| f5 [entity; asserted; positive] There is a table. | f4 [entity; asserted; positive] There is a table. | retained | same_fact |
| f6 [entity; asserted; positive] There is a window. | f5 [entity; asserted; positive] There is a window. | retained | same_fact |
| f7 [relation; asserted; positive] The vase is filled with dried flowers. | f7 [relation; asserted; positive] The vase is filled with flowers and grasses. | ambiguous | partial_overlap |
| f8 [relation; asserted; positive] The dried flowers include daisies and sunflowers. | — | removed | not_expressed |
| f9 [relation; asserted; positive] The vase is placed on the table. | f8 [relation; asserted; positive] The vase is placed on the table. | retained | same_fact |
| f10 [relation; asserted; positive] The vase is positioned near the window. | f9 [relation; asserted; positive] The table is next to the window. | ambiguous | partial_overlap |
| f11 [other; asserted; positive] The flowers are arranged in a visually appealing manner. | f10 [other; asserted; positive] The flowers and grasses are arranged in such a way that they create a visually appealing bouquet. | ambiguous | partial_overlap |
| f12 [other; asserted; positive] The combination of the vase, flowers, and the window creates a pleasant and inviting atmosphere. | — | removed | not_expressed |
| — | f6 [attribute; asserted; positive] The vase is made of glass. | added | not_expressed |
| — | f3 [entity; asserted; positive] There are grasses. | ambiguous | alignment_validation_error |

**三轮差异**

- original f2 There are dried flowers.：第1轮 ambiguous/partial_overlap → f2；第2轮 ambiguous/granularity → f2；第3轮 retained/same_fact → f2
- steer f2 There are flowers.：第1轮 ambiguous/partial_overlap → f2；第2轮 ambiguous/granularity → f2；第3轮 retained/same_fact → f2

**第3轮校验拒绝记录**

- 模型原提议 [] ↔ ['f3']：added；拒绝原因：unresolved source requires ambiguous status。

## 299573 长颈鹿

**Vanilla 原文**

> The image features two giraffes standing in a grassy field, with one giraffe positioned slightly behind the other. They are both facing the same direction, possibly looking at something in the distance. The giraffes are standing close to each other, creating a sense of companionship. The field is filled with tall grass, providing a natural habitat for the giraffes.

**Steer 原文**

> Two giraffes stand side by side in a grassy field.

**第3轮实际最终结果**

| Vanilla fact | Steer fact | status | reason |
| --- | --- | --- | --- |
| f1 [entity; asserted; positive] There are two giraffes. | f1 [entity; asserted; positive] There are giraffes. | retained | same_fact |
| f2 [entity; asserted; positive] There is a grassy field. | f3 [entity; asserted; positive] There is a grassy field. | retained | same_fact |
| f3 [attribute; asserted; positive] There are two giraffes. | f2 [attribute; asserted; positive] There are two giraffes. | retained | same_fact |
| f4 [attribute; asserted; positive] The field is grassy. | f4 [attribute; asserted; positive] The field is grassy. | retained | same_fact |
| f5 [relation; asserted; positive] The giraffes are standing. | f5 [relation; asserted; positive] The giraffes are standing. | retained | same_fact |
| f6 [relation; asserted; positive] The giraffes are in the grassy field. | f7 [relation; asserted; positive] The giraffes are in the grassy field. | retained | same_fact |
| f7 [relation; asserted; positive] One giraffe is positioned slightly behind the other. | f6 [relation; asserted; positive] The giraffes are side by side. | modified | value_changed |
| f8 [relation; asserted; positive] Both giraffes are facing the same direction. | — | removed | not_expressed |
| f9 [relation; speculative; positive] The giraffes are possibly looking at something in the distance. | — | removed | not_expressed |
| f10 [relation; asserted; positive] The giraffes are standing close to each other. | — | removed | not_expressed |
| f11 [other; asserted; positive] The giraffes create a sense of companionship. | — | removed | not_expressed |
| f12 [attribute; asserted; positive] The field is filled with tall grass. | — | removed | not_expressed |
| f13 [other; asserted; positive] The field provides a natural habitat for the giraffes. | — | removed | not_expressed |
| cov_f1 [attribute; asserted; positive] The grass is tall. | — | removed | not_expressed |

**三轮差异**

- original f7 One giraffe is positioned slightly behind the other.：第1轮 ambiguous/alignment_validation_error → —；第2轮 ambiguous/alignment_validation_error → —；第3轮 modified/value_changed → f6
- original f10 The giraffes are standing close to each other.：第1轮 ambiguous/alignment_validation_error → —；第2轮 ambiguous/alignment_validation_error → —；第3轮 removed/not_expressed → —
- steer f6 The giraffes are side by side.：第1轮 ambiguous/alignment_validation_error → —；第2轮 ambiguous/alignment_validation_error → —；第3轮 modified/value_changed → f7

## 581451 热狗

**Vanilla 原文**

> The image features a hot dog with a bun, topped with ketchup and green peppers. The hot dog is placed on a piece of paper, which is likely a napkin. The hot dog is positioned in the center of the image, and the peppers are scattered around it, adding a colorful and appetizing touch to the dish.

**Steer 原文**

> A person is holding a hot dog with ketchup and peppers on it.

**第3轮实际最终结果**

| Vanilla fact | Steer fact | status | reason |
| --- | --- | --- | --- |
| f1 [entity; asserted; positive] There is a hot dog. | f2 [entity; asserted; positive] There is a hot dog. | retained | same_fact |
| f2 [entity; asserted; positive] There is a bun. | — | removed | not_expressed |
| f3 [entity; asserted; positive] There is ketchup. | f3 [entity; asserted; positive] There is ketchup. | retained | same_fact |
| f4 [entity; asserted; positive] There are green peppers. | f4 [entity; asserted; positive] There are peppers. | retained | same_fact |
| f5 [entity; asserted; positive] There is a piece of paper. | — | removed | not_expressed |
| f6 [entity; speculative; positive] There is a napkin. | — | removed | not_expressed |
| f7 [relation; asserted; positive] The hot dog has a bun. | — | removed | not_expressed |
| f10 [attribute; asserted; positive] The peppers are green. | — | removed | not_expressed |
| f11 [relation; asserted; positive] The hot dog is placed on the piece of paper. | — | removed | not_expressed |
| f12 [relation; speculative; positive] The piece of paper is likely a napkin. | — | removed | not_expressed |
| f13 [relation; asserted; positive] The hot dog is positioned in the center of the image. | — | removed | not_expressed |
| f14 [relation; asserted; positive] The peppers are scattered around the hot dog. | — | removed | not_expressed |
| f15 [other; asserted; positive] The peppers add a colorful and appetizing touch to the dish. | — | removed | not_expressed |
| — | f1 [entity; asserted; positive] There is a person. | added | not_expressed |
| — | f5 [relation; asserted; positive] The person is holding the hot dog. | added | not_expressed |
| f8 [relation; asserted; positive] The hot dog is topped with ketchup. | — | ambiguous | alignment_validation_error |
| f9 [relation; asserted; positive] The hot dog is topped with green peppers. | — | ambiguous | alignment_validation_error |
| — | f6 [relation; asserted; positive] The hot dog has ketchup on it. | ambiguous | alignment_validation_error |
| — | f7 [relation; asserted; positive] The hot dog has peppers on it. | ambiguous | alignment_validation_error |

**三轮差异**

三轮在事实对应、状态和原因上相同。

**第3轮校验拒绝记录**

- 模型原提议 ['f8'] ↔ ['f6']：retained；拒绝原因：different semantic slots cannot be retained/modified。
- 模型原提议 ['f9'] ↔ ['f7']：retained；拒绝原因：different semantic slots cannot be retained/modified。

## 417586 长椅与鞋

**Vanilla 原文**

> The image features a wooden bench with two pairs of shoes placed on it. The shoes are positioned close to each other, with one pair located towards the left side of the bench and the other pair on the right side. The bench appears to be made of wood and is situated in a grassy area, possibly a park or a garden. The shoes seem to be old and worn, suggesting that they have been used for a long time.

**Steer 原文**

> The image depicts two pairs of shoes resting on a wooden bench. One pair of shoes is positioned on the left side of the bench, while the other pair of shoes is on the right side. Both pairs of shoes are black in color.

**第3轮实际最终结果**

| Vanilla fact | Steer fact | status | reason |
| --- | --- | --- | --- |
| f1 [entity; asserted; positive] There is a bench. | f2 [entity; asserted; positive] There is a bench. | retained | same_fact |
| f2 [entity; asserted; positive] There are shoes. | f1 [entity; asserted; positive] There are shoes. | retained | same_fact |
| f4 [attribute; asserted; positive] There are two pairs of the described shoes. | f3 [attribute; asserted; positive] There are two pairs of the described shoes. | retained | same_fact |
| f5 [relation; asserted; positive] The shoes are on the bench. | f5 [relation; asserted; positive] The shoes are on the bench. | retained | same_fact |
| f6 [relation; asserted; positive] The shoes are positioned close to each other. | — | removed | not_expressed |
| f7 [relation; asserted; positive] One pair of shoes is located towards the left side of the bench. | f6 [relation; asserted; positive] One pair of shoes is on the left side of the bench. | retained | same_fact |
| f8 [relation; asserted; positive] The other pair of shoes is on the right side of the bench. | f7 [relation; asserted; positive] The other pair of shoes is on the right side of the bench. | retained | same_fact |
| f10 [relation; asserted; positive] The bench is situated in a grassy area. | — | removed | not_expressed |
| f11 [other; speculative; positive] The grassy area is possibly a park or a garden. | — | removed | not_expressed |
| f12 [attribute; speculative; positive] The shoes seem to be old. | — | removed | not_expressed |
| f13 [attribute; speculative; positive] The shoes seem to be worn. | — | removed | not_expressed |
| f14 [other; speculative; positive] The shoes suggest that they have been used for a long time. | — | removed | not_expressed |
| — | f8 [attribute; asserted; positive] Both pairs of shoes are black. | added | not_expressed |
| f3 [attribute; asserted; positive] The bench is wooden. | — | ambiguous | alignment_validation_error |
| f9 [attribute; speculative; positive] The bench appears to be made of wood. | — | ambiguous | alignment_validation_error |
| — | f4 [attribute; asserted; positive] The bench is wooden. | ambiguous | alignment_validation_error |

**三轮差异**

三轮在事实对应、状态和原因上相同。

**第3轮校验拒绝记录**

- 模型原提议 ['f3'] ↔ ['f4']：retained；拒绝原因：fact assigned more than once。
- 模型原提议 ['f9'] ↔ ['f4']：ambiguous；拒绝原因：fact assigned more than once。
