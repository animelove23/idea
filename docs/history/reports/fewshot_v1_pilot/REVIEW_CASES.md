# 首次 few-shot 测试逐条复核

以下包含原文、两个条件的原始结构化输出与助手复核意见。失败调用只列诊断，不视为有效输出。verification 均为 pending，表内省略该列。

## 04 — 43098_vanilla_greedy

原始 caption：

> The image features a man walking down a sidewalk, passing by a blue suitcase that is placed on the ground. The suitcase is positioned near a black street light, which is located on the sidewalk. The man appears to be walking away from the suitcase, possibly leaving it behind or preparing to pick it up. The scene takes place in an urban setting, with the man and the suitcase being the main focus of the image.

**0-shot 复核：** 明确指代被拆为多个人/箱子锚点（e1/e7/e10/e13；e3/e8/e9/e11/e14），且 main_focus 被写成 man 与 suitcase 之间的关系。具体 walk/pass_by 及三种推测行为保留。

**8-shot 复核：** 人物和箱子的指代复用改善；推测离开、留下、准备拿起仍分别保留，未变成已经拿起。main_focus 分别附于人物/箱子。

**仍存问题：** 两个条件仍将 a sidewalk / the sidewalk 分为两个锚点。8-shot 又给 urban_setting 加 exists，并将场景层设置转成 man in urban_setting；抽象场景锚点与存在事实边界未稳定。

### 04_s0_r1 — success

原始记录：[JSON](checkpoints/04_s0_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | man | a man |
| e2 | sidewalk | a sidewalk |
| e3 | suitcase | a blue suitcase |
| e4 | ground | the ground |
| e5 | street_light | a black street light |
| e6 | sidewalk | the sidewalk |
| e7 | man | the man |
| e8 | suitcase | the suitcase |
| e9 | suitcase | the suitcase |
| e10 | man | the man |
| e11 | suitcase | the suitcase |
| e12 | image | the image |
| e13 | man | the man |
| e14 | suitcase | the suitcase |
| e15 | image | the image |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | a man |
| f2 | object | e2 | exists |  | asserted | a sidewalk |
| f3 | object | e3 | exists |  | asserted | a blue suitcase |
| f4 | object | e4 | exists |  | asserted | the ground |
| f5 | object | e5 | exists |  | asserted | a black street light |
| f6 | object | e6 | exists |  | asserted | the sidewalk |
| f7 | action | e1 | walk |  | asserted | a man walking down a sidewalk |
| f8 | relation | e1 | on | e2 | asserted | walking down a sidewalk |
| f9 | action | e1 | pass_by | e3 | asserted | passing by a blue suitcase |
| f10 | attribute | e3 | color | blue | asserted | blue suitcase |
| f11 | relation | e3 | on | e4 | asserted | placed on the ground |
| f12 | relation | e3 | near | e5 | asserted | positioned near a black street light |
| f13 | attribute | e5 | color | black | asserted | black street light |
| f14 | relation | e5 | on | e6 | asserted | located on the sidewalk |
| f15 | action | e7 | walk_away_from | e8 | speculative | appears to be walking away from the suitcase |
| f16 | action | e7 | leave_behind | e9 | speculative | possibly leaving it behind |
| f17 | action | e10 | prepare_to_pick_up | e11 | speculative | or preparing to pick it up |
| f18 | attribute | e12 | setting | urban | asserted | urban setting |
| f19 | relation | e13 | main_focus | e14 | asserted | the man and the suitcase being the main focus of the image |

### 04_s8_r1 — success

原始记录：[JSON](checkpoints/04_s8_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | man | a man |
| e2 | sidewalk | a sidewalk |
| e3 | suitcase | a blue suitcase |
| e4 | ground | the ground |
| e5 | street_light | a black street light |
| e6 | sidewalk | the sidewalk |
| e7 | urban_setting | an urban setting |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | a man |
| f2 | object | e2 | exists |  | asserted | a sidewalk |
| f3 | object | e3 | exists |  | asserted | a blue suitcase |
| f4 | object | e4 | exists |  | asserted | the ground |
| f5 | object | e5 | exists |  | asserted | a black street light |
| f6 | object | e6 | exists |  | asserted | the sidewalk |
| f7 | object | e7 | exists |  | asserted | an urban setting |
| f8 | action | e1 | walk |  | asserted | a man walking down a sidewalk |
| f9 | relation | e1 | on | e2 | asserted | a man walking down a sidewalk |
| f10 | action | e1 | pass_by | e3 | asserted | passing by a blue suitcase |
| f11 | attribute | e3 | color | blue | asserted | a blue suitcase |
| f12 | relation | e3 | on | e4 | asserted | a blue suitcase that is placed on the ground |
| f13 | relation | e3 | near | e5 | asserted | The suitcase is positioned near a black street light |
| f14 | attribute | e5 | color | black | asserted | a black street light |
| f15 | relation | e5 | on | e6 | asserted | a black street light, which is located on the sidewalk |
| f16 | action | e1 | walk_away_from | e3 | speculative | The man appears to be walking away from the suitcase |
| f17 | action | e1 | leave_behind | e3 | speculative | possibly leaving it behind |
| f18 | action | e1 | prepare_to_pick_up | e3 | speculative | or preparing to pick it up |
| f19 | relation | e1 | in | e7 | asserted | The scene takes place in an urban setting |
| f20 | attribute | e1 | visual_prominence | main_focus | asserted | the man and the suitcase being the main focus of the image |
| f21 | attribute | e3 | visual_prominence | main_focus | asserted | the man and the suitcase being the main focus of the image |

### 04_s8_r2 — success

原始记录：[JSON](checkpoints/04_s8_r2.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | man | a man |
| e2 | sidewalk | a sidewalk |
| e3 | suitcase | a blue suitcase |
| e4 | ground | the ground |
| e5 | street_light | a black street light |
| e6 | sidewalk | the sidewalk |
| e7 | urban_setting | an urban setting |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | a man |
| f2 | object | e2 | exists |  | asserted | a sidewalk |
| f3 | object | e3 | exists |  | asserted | a blue suitcase |
| f4 | object | e4 | exists |  | asserted | the ground |
| f5 | object | e5 | exists |  | asserted | a black street light |
| f6 | object | e7 | exists |  | asserted | an urban setting |
| f7 | action | e1 | walk |  | asserted | a man walking down a sidewalk |
| f8 | relation | e1 | on | e2 | asserted | a man walking down a sidewalk |
| f9 | action | e1 | pass_by | e3 | asserted | passing by a blue suitcase |
| f10 | attribute | e3 | color | blue | asserted | a blue suitcase |
| f11 | relation | e3 | on | e4 | asserted | a blue suitcase that is placed on the ground |
| f12 | relation | e3 | near | e5 | asserted | The suitcase is positioned near a black street light |
| f13 | attribute | e5 | color | black | asserted | a black street light |
| f14 | relation | e5 | on | e6 | asserted | a black street light, which is located on the sidewalk |
| f15 | action | e1 | walk_away_from | e3 | speculative | The man appears to be walking away from the suitcase |
| f16 | action | e1 | leave_behind | e3 | speculative | possibly leaving it behind |
| f17 | action | e1 | prepare_to_pick_up | e3 | speculative | or preparing to pick it up |
| f18 | relation | e1 | in | e7 | asserted | The scene takes place in an urban setting |
| f19 | attribute | e1 | visual_prominence | main_focus | asserted | the man and the suitcase being the main focus of the image |
| f20 | attribute | e3 | visual_prominence | main_focus | asserted | the man and the suitcase being the main focus of the image |

## 05 — 295574_vanilla_greedy

原始 caption：

> The image features a man standing in a bathroom, taking a picture of himself in the mirror using a cell phone. He is positioned near the sink, which is located in the center of the bathroom. The bathroom appears to be well-equipped, with a toilet situated on the left side of the room and a shower on the right side.
>
> There are several bottles scattered around the bathroom, with some placed near the sink and others on the right side of the room. Additionally, there is a vase located on the right side of the bathroom, adding a decorative touch to the space.

**0-shot 复核：** 瓶子的 some/others 子组被并到 e8，使 near sink 与 on right side 都附于一般瓶子组；take_picture 的 object=e3(mirror)，改变了自拍宾语。模糊计数初次用 count_eq(several)，重试修复。

**8-shot 复核：** 保留瓶子一般组和两个子组 e10/e11/e12，几处空间关系分开；count(several) 首次有效；自拍结构比零示例更完整。

**仍存问题：** himself 仍另建 man 锚点，未复用 e1；sink 位于 bathroom center 弱化为无参照的 location=center；decorative_role 等评价边界仍不清楚。

### 05_s0_r1 — success

原始记录：[JSON](checkpoints/05_s0_r1.json)

第 1 次请求错误：Invalid API response: vague counts use count without a numeric comparator

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | man | man |
| e2 | bathroom | bathroom |
| e3 | mirror | mirror |
| e4 | phone | cell phone |
| e5 | sink | sink |
| e6 | toilet | toilet |
| e7 | shower | shower |
| e8 | bottle | several bottles |
| e9 | vase | vase |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | man |
| f2 | object | e2 | exists |  | asserted | bathroom |
| f3 | object | e3 | exists |  | asserted | mirror |
| f4 | object | e4 | exists |  | asserted | cell phone |
| f5 | object | e5 | exists |  | asserted | sink |
| f6 | object | e6 | exists |  | asserted | toilet |
| f7 | object | e7 | exists |  | asserted | shower |
| f8 | object | e8 | exists |  | asserted | several bottles |
| f9 | object | e9 | exists |  | asserted | vase |
| f10 | action | e1 | stand |  | asserted | standing |
| f11 | action | e1 | take_picture | e3 | asserted | taking a picture |
| f12 | relation | e1 | in | e2 | asserted | in a bathroom |
| f13 | relation | e1 | using | e4 | asserted | using a cell phone |
| f14 | relation | e1 | near | e5 | asserted | positioned near the sink |
| f15 | relation | e5 | located_in_center_of | e2 | asserted | located in the center of the bathroom |
| f16 | attribute | e2 | appears_well_equipped | true | speculative | appears to be well-equipped |
| f17 | relation | e6 | situated_on_left_side_of | e2 | asserted | situated on the left side of the room |
| f18 | relation | e7 | on_right_side_of | e2 | asserted | on the right side |
| f19 | relation | e8 | scattered_around | e2 | asserted | scattered around the bathroom |
| f20 | relation | e8 | near | e5 | asserted | some placed near the sink |
| f21 | relation | e8 | on_right_side_of | e2 | asserted | others on the right side of the room |
| f22 | relation | e9 | located_on_right_side_of | e2 | asserted | located on the right side of the bathroom |
| f23 | count | bottle | count | several | asserted | several bottles |

### 05_s8_r1 — success

原始记录：[JSON](checkpoints/05_s8_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | man | a man |
| e2 | bathroom | a bathroom |
| e3 | picture | a picture |
| e4 | man | himself |
| e5 | mirror | the mirror |
| e6 | phone | a cell phone |
| e7 | sink | the sink |
| e8 | toilet | a toilet |
| e9 | shower | a shower |
| e10 | bottle | several bottles |
| e11 | bottle | some |
| e12 | bottle | others |
| e13 | vase | a vase |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | a man |
| f2 | object | e2 | exists |  | asserted | a bathroom |
| f3 | object | e3 | exists |  | asserted | a picture |
| f4 | object | e5 | exists |  | asserted | the mirror |
| f5 | object | e6 | exists |  | asserted | a cell phone |
| f6 | object | e7 | exists |  | asserted | the sink |
| f7 | object | e8 | exists |  | asserted | a toilet |
| f8 | object | e9 | exists |  | asserted | a shower |
| f9 | object | e10 | exists |  | asserted | several bottles |
| f10 | object | e13 | exists |  | asserted | a vase |
| f11 | action | e1 | stand |  | asserted | a man standing in a bathroom |
| f12 | relation | e1 | in | e2 | asserted | a man standing in a bathroom |
| f13 | action | e1 | take_picture | e3 | asserted | taking a picture of himself in the mirror using a cell phone |
| f14 | relation | e3 | of | e4 | asserted | a picture of himself |
| f15 | relation | e4 | in | e5 | asserted | in the mirror |
| f16 | relation | e1 | using | e6 | asserted | using a cell phone |
| f17 | relation | e1 | near | e7 | asserted | He is positioned near the sink |
| f18 | attribute | e7 | location | center | asserted | the sink, which is located in the center of the bathroom |
| f19 | attribute | e2 | equipment_status | well_equipped | speculative | The bathroom appears to be well-equipped |
| f20 | relation | e8 | on_left_side_of | e2 | asserted | a toilet situated on the left side of the room |
| f21 | relation | e9 | on_right_side_of | e2 | asserted | a shower on the right side |
| f22 | count | ["e10"] | count | several | asserted | several bottles |
| f23 | relation | e10 | scattered_around | e2 | asserted | several bottles scattered around the bathroom |
| f24 | relation | e11 | near | e7 | asserted | some placed near the sink |
| f25 | relation | e12 | on_right_side_of | e2 | asserted | others on the right side of the room |
| f26 | relation | e13 | on_right_side_of | e2 | asserted | a vase located on the right side of the bathroom |
| f27 | attribute | e13 | decorative_role | decorative | asserted | adding a decorative touch to the space |

## 07 — 451972_vista_greedy

原始 caption：

> Santa Claus rides on a fire truck with his reindeer friends.

**0-shot 复核：** 保留 santa_claus/fire_truck/reindeer，没有按常识改成 float；输出 ride 与 with。

**8-shot 复核：** 同样保留原文类别；多出 belongs_to(reindeer,santa_claus)。

**仍存问题：** his reindeer friends 不能明确证明所有权，belongs_to 有过强解释风险；两个条件都没有把 rides on 的 on 单独表达，影响 Action/Relation 独立统计。

### 07_s0_r1 — success

原始记录：[JSON](checkpoints/07_s0_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | santa_claus | Santa Claus |
| e2 | fire_truck | a fire truck |
| e3 | reindeer | his reindeer friends |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | Santa Claus |
| f2 | object | e2 | exists |  | asserted | a fire truck |
| f3 | object | e3 | exists |  | asserted | his reindeer friends |
| f4 | action | e1 | rides | e2 | asserted | Santa Claus rides on a fire truck |
| f5 | relation | e1 | with | e3 | asserted | with his reindeer friends |

### 07_s8_r1 — success

原始记录：[JSON](checkpoints/07_s8_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | santa_claus | Santa Claus |
| e2 | fire_truck | a fire truck |
| e3 | reindeer | his reindeer friends |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | Santa Claus |
| f2 | object | e2 | exists |  | asserted | a fire truck |
| f3 | object | e3 | exists |  | asserted | his reindeer friends |
| f4 | action | e1 | ride | e2 | asserted | Santa Claus rides on a fire truck |
| f5 | relation | e1 | with | e3 | asserted | Santa Claus rides on a fire truck with his reindeer friends |
| f6 | relation | e3 | belongs_to | e1 | asserted | his reindeer friends |

## 08 — 275717_vanilla_beam5

原始 caption：

> The image is a vintage black and white photograph of a young woman wearing a white shirt and a tie. She is posing for the picture with a smile on her face. Her hair is styled in a bun, and she appears to be well-dressed for the occasion. The photograph captures a moment in time, showcasing the woman's youth and elegance.

**0-shot 复核：** 最终结构失败：source=her hair，原文为 Her hair，两次均未修复；不能纳入有效语义输出比较。

**8-shot 复核：** 结构通过，保留照片 vintage/black_and_white、woman 的 young、衬衫 white、穿戴及 bun 发型。

**仍存问题：** 把 smile 单独作为 object 并配 on_face；没有将其作为人物 smile 动作。bun 也被独立计作 object，存在把外观形式实体化的风险。

### 08_s0_r1 — failed

原始记录：[JSON](checkpoints/08_s0_r1.json)

第 1 次请求错误：Invalid API response: source must be a verbatim substring

- `facts[id=f21].source` = `her hair`

第 2 次请求错误：Invalid API response: source must be a verbatim substring

- `facts[id=f21].source` = `her hair`

### 08_s8_r1 — success

原始记录：[JSON](checkpoints/08_s8_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | photograph | a vintage black and white photograph |
| e2 | woman | a young woman |
| e3 | shirt | a white shirt |
| e4 | tie | a tie |
| e5 | photograph | the picture |
| e6 | smile | a smile |
| e7 | hair | Her hair |
| e8 | bun | a bun |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | a vintage black and white photograph |
| f2 | object | e2 | exists |  | asserted | a young woman |
| f3 | object | e3 | exists |  | asserted | a white shirt |
| f4 | object | e4 | exists |  | asserted | a tie |
| f5 | object | e6 | exists |  | asserted | a smile |
| f6 | object | e7 | exists |  | asserted | Her hair |
| f7 | object | e8 | exists |  | asserted | a bun |
| f8 | attribute | e1 | style | vintage | asserted | vintage |
| f9 | attribute | e1 | color_scheme | black_and_white | asserted | black and white |
| f10 | attribute | e2 | age | young | asserted | young woman |
| f11 | attribute | e3 | color | white | asserted | white shirt |
| f12 | relation | e2 | wears | e3 | asserted | a young woman wearing a white shirt and a tie |
| f13 | relation | e2 | wears | e4 | asserted | a young woman wearing a white shirt and a tie |
| f14 | action | e2 | pose | e5 | asserted | She is posing for the picture |
| f15 | relation | e6 | on_face | e2 | asserted | with a smile on her face |
| f16 | attribute | e7 | hairstyle | bun | asserted | Her hair is styled in a bun |
| f17 | relation | e7 | part_of | e2 | asserted | Her hair |
| f18 | attribute | e2 | dress_quality | well_dressed | speculative | she appears to be well-dressed for the occasion |

## 14 — 554582_vista_top_p

原始 caption：

> Three men are sitting on a bench outdoors, each wearing different colored clothes. They appear to be posing for a photograph. The men have their hands and feet crossed while they sit. One of them is wearing a watch on his wrist.

**0-shot 复核：** 遗漏明确 three 的 count；衣服颜色附于 men，没有独立 clothes 与 wears；但 hands/feet crossed 分开。

**8-shot 复核：** 补出 count(man,3)、clothes 对象、wears 和衣服颜色；手表只附于 One of them，没有泛化给三人。

**仍存问题：** 首轮将 hands_and_feet_crossed 合为一条姿态，第二轮才分开；一般男人组与 The men 的指代、身体部位 exists 取舍发生变化。

### 14_s0_r1 — success

原始记录：[JSON](checkpoints/14_s0_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | men | Three men |
| e2 | bench | a bench |
| e3 | hands | their hands |
| e4 | feet | feet |
| e5 | man | One of them |
| e6 | watch | a watch |
| e7 | wrist | his wrist |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | Three men |
| f2 | object | e2 | exists |  | asserted | a bench |
| f3 | action | e1 | sit |  | asserted | Three men are sitting |
| f4 | relation | e1 | on | e2 | asserted | sitting on a bench |
| f5 | attribute | e1 | location | outdoors | asserted | outdoors |
| f6 | attribute | e1 | clothes_color | different colored | asserted | each wearing different colored clothes |
| f7 | action | e1 | pose |  | speculative | They appear to be posing for a photograph |
| f8 | object | e3 | exists |  | asserted | their hands |
| f9 | object | e4 | exists |  | asserted | feet |
| f10 | attribute | e3 | crossed | crossed | asserted | hands and feet crossed |
| f11 | attribute | e4 | crossed | crossed | asserted | hands and feet crossed |
| f12 | object | e5 | exists |  | asserted | One of them |
| f13 | object | e6 | exists |  | asserted | a watch |
| f14 | object | e7 | exists |  | asserted | his wrist |
| f15 | relation | e5 | wears | e6 | asserted | One of them is wearing a watch on his wrist |
| f16 | relation | e6 | on | e7 | asserted | a watch on his wrist |

### 14_s8_r1 — success

原始记录：[JSON](checkpoints/14_s8_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | man | Three men |
| e2 | bench | a bench |
| e3 | clothes | different colored clothes |
| e4 | man | The men |
| e5 | hand | their hands |
| e6 | foot | feet |
| e7 | man | One of them |
| e8 | watch | a watch |
| e9 | wrist | his wrist |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | Three men |
| f2 | object | e2 | exists |  | asserted | a bench |
| f3 | object | e3 | exists |  | asserted | different colored clothes |
| f4 | object | e8 | exists |  | asserted | a watch |
| f5 | count | man | count | 3 | asserted | Three men |
| f6 | action | e1 | sit |  | asserted | Three men are sitting on a bench |
| f7 | relation | e1 | on | e2 | asserted | Three men are sitting on a bench |
| f8 | attribute | e1 | location | outdoors | asserted | outdoors |
| f9 | relation | e1 | wears | e3 | asserted | each wearing different colored clothes |
| f10 | attribute | e3 | color | different | asserted | different colored clothes |
| f11 | action | e4 | pose_for_photograph |  | speculative | They appear to be posing for a photograph |
| f12 | attribute | e4 | posture | hands_and_feet_crossed | asserted | The men have their hands and feet crossed |
| f13 | relation | e5 | part_of | e4 | asserted | their hands |
| f14 | relation | e6 | part_of | e4 | asserted | feet |
| f15 | relation | e7 | wears | e8 | asserted | One of them is wearing a watch on his wrist |
| f16 | relation | e8 | on | e9 | asserted | a watch on his wrist |
| f17 | relation | e9 | part_of | e7 | asserted | his wrist |

### 14_s8_r2 — success

原始记录：[JSON](checkpoints/14_s8_r2.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | man | Three men |
| e2 | bench | a bench |
| e3 | clothing | different colored clothes |
| e4 | hand | their hands |
| e5 | foot | feet |
| e6 | man | One of them |
| e7 | watch | a watch |
| e8 | wrist | his wrist |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | Three men |
| f2 | object | e2 | exists |  | asserted | a bench |
| f3 | object | e3 | exists |  | asserted | different colored clothes |
| f4 | object | e4 | exists |  | asserted | their hands |
| f5 | object | e5 | exists |  | asserted | feet |
| f6 | object | e7 | exists |  | asserted | a watch |
| f7 | object | e8 | exists |  | asserted | his wrist |
| f8 | count | ["e1"] | count | 3 | asserted | Three men |
| f9 | action | e1 | sit |  | asserted | Three men are sitting on a bench |
| f10 | relation | e1 | on | e2 | asserted | Three men are sitting on a bench |
| f11 | attribute | e1 | location | outdoors | asserted | outdoors |
| f12 | relation | e1 | wears | e3 | asserted | each wearing different colored clothes |
| f13 | attribute | e3 | color | different | asserted | different colored clothes |
| f14 | action | e1 | pose_for_photograph |  | speculative | They appear to be posing for a photograph |
| f15 | relation | e4 | part_of | e1 | asserted | The men have their hands |
| f16 | relation | e5 | part_of | e1 | asserted | The men have their hands and feet |
| f17 | attribute | e4 | posture | crossed | asserted | their hands and feet crossed |
| f18 | attribute | e5 | posture | crossed | asserted | their hands and feet crossed |
| f19 | relation | e6 | wears | e7 | asserted | One of them is wearing a watch on his wrist |
| f20 | relation | e7 | on | e8 | asserted | a watch on his wrist |
| f21 | relation | e8 | part_of | e6 | asserted | his wrist |

## 15 — 295574_vista_greedy

原始 caption：

> The image depicts a man taking a picture of himself in a bathroom. He is standing in front of a sink and a mirror. Various items can be seen in the bathroom, such as a toothbrush, a hair dryer, and a bottle. The man is wearing a black jacket and appears to be taking a selfie.

**0-shot 复核：** 保留黑夹克、镜子/水池、用品、asserted 自拍与 speculative selfie；himself 单独建立 man 锚点。

**8-shot 复核：** 复用人物，以 take_picture_of_self 保留 asserted 自拍，另保留 speculative take_selfie；未补原文没有的 phone。

**仍存问题：** 本条预设主要检查项表现较好；take_picture_of_self 与 take_selfie 词形差异仍需后续按语义对齐，不能只比较 predicate 字符串。

### 15_s0_r1 — success

原始记录：[JSON](checkpoints/15_s0_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | man | a man |
| e2 | man | himself |
| e3 | bathroom | a bathroom |
| e4 | sink | a sink |
| e5 | mirror | a mirror |
| e6 | toothbrush | a toothbrush |
| e7 | hair_dryer | a hair dryer |
| e8 | bottle | a bottle |
| e9 | jacket | a black jacket |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | a man |
| f2 | object | e3 | exists |  | asserted | a bathroom |
| f3 | object | e4 | exists |  | asserted | a sink |
| f4 | object | e5 | exists |  | asserted | a mirror |
| f5 | object | e6 | exists |  | asserted | a toothbrush |
| f6 | object | e7 | exists |  | asserted | a hair dryer |
| f7 | object | e8 | exists |  | asserted | a bottle |
| f8 | object | e9 | exists |  | asserted | a black jacket |
| f9 | action | e1 | take_picture | e2 | asserted | taking a picture of himself |
| f10 | action | e1 | stand |  | asserted | standing in front of a sink and a mirror |
| f11 | relation | e1 | in_front_of | e4 | asserted | standing in front of a sink and a mirror |
| f12 | relation | e1 | in_front_of | e5 | asserted | standing in front of a sink and a mirror |
| f13 | relation | e1 | in | e3 | asserted | in a bathroom |
| f14 | relation | e6 | in | e3 | asserted | in the bathroom |
| f15 | relation | e7 | in | e3 | asserted | in the bathroom |
| f16 | relation | e8 | in | e3 | asserted | in the bathroom |
| f17 | relation | e1 | wears | e9 | asserted | wearing a black jacket |
| f18 | attribute | e9 | color | black | asserted | black jacket |
| f19 | action | e1 | take_selfie |  | speculative | appears to be taking a selfie |

### 15_s8_r1 — success

原始记录：[JSON](checkpoints/15_s8_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | man | a man |
| e2 | bathroom | a bathroom |
| e3 | sink | a sink |
| e4 | mirror | a mirror |
| e5 | toothbrush | a toothbrush |
| e6 | hair_dryer | a hair dryer |
| e7 | bottle | a bottle |
| e8 | jacket | a black jacket |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | a man |
| f2 | object | e2 | exists |  | asserted | a bathroom |
| f3 | object | e3 | exists |  | asserted | a sink |
| f4 | object | e4 | exists |  | asserted | a mirror |
| f5 | object | e5 | exists |  | asserted | a toothbrush |
| f6 | object | e6 | exists |  | asserted | a hair dryer |
| f7 | object | e7 | exists |  | asserted | a bottle |
| f8 | object | e8 | exists |  | asserted | a black jacket |
| f9 | action | e1 | take_picture_of_self |  | asserted | a man taking a picture of himself |
| f10 | relation | e1 | in | e2 | asserted | a man taking a picture of himself in a bathroom |
| f11 | action | e1 | stand |  | asserted | He is standing in front of a sink and a mirror |
| f12 | relation | e1 | in_front_of | e3 | asserted | He is standing in front of a sink and a mirror |
| f13 | relation | e1 | in_front_of | e4 | asserted | He is standing in front of a sink and a mirror |
| f14 | relation | e5 | in | e2 | asserted | Various items can be seen in the bathroom |
| f15 | relation | e6 | in | e2 | asserted | Various items can be seen in the bathroom |
| f16 | relation | e7 | in | e2 | asserted | Various items can be seen in the bathroom |
| f17 | attribute | e8 | color | black | asserted | a black jacket |
| f18 | relation | e1 | wears | e8 | asserted | The man is wearing a black jacket |
| f19 | action | e1 | take_selfie |  | speculative | appears to be taking a selfie |

## 17 — 275717_vista_beam5

原始 caption：

> The girl in the picture is wearing a white shirt with a tie around her neck. She has long hair and is smiling at the camera.

**0-shot 复核：** 保留 girl、white shirt、tie around neck、long hair 与 smile(camera)，没有推断 happiness。

**8-shot 复核：** 主要外观与领带关系保留；smile 与 toward(camera) 分开。

**仍存问题：** 8-shot 中 neck/camera 有实体却没有存在事实；toward(person,camera) 脱离 smile 后可能被误读为一般身体朝向。应明确动作目标的表达边界。

### 17_s0_r1 — success

原始记录：[JSON](checkpoints/17_s0_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | girl | The girl |
| e2 | shirt | a white shirt |
| e3 | tie | a tie |
| e4 | neck | her neck |
| e5 | hair | long hair |
| e6 | camera | the camera |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | The girl |
| f2 | object | e2 | exists |  | asserted | a white shirt |
| f3 | object | e3 | exists |  | asserted | a tie |
| f4 | object | e4 | exists |  | asserted | her neck |
| f5 | object | e5 | exists |  | asserted | long hair |
| f6 | object | e6 | exists |  | asserted | the camera |
| f7 | relation | e1 | wears | e2 | asserted | is wearing a white shirt |
| f8 | attribute | e2 | color | white | asserted | white shirt |
| f9 | relation | e3 | around | e4 | asserted | a tie around her neck |
| f10 | relation | e4 | part_of | e1 | asserted | her neck |
| f11 | relation | e1 | has | e5 | asserted | She has long hair |
| f12 | attribute | e5 | length | long | asserted | long hair |
| f13 | action | e1 | smile | e6 | asserted | is smiling at the camera |

### 17_s8_r1 — success

原始记录：[JSON](checkpoints/17_s8_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | girl | The girl |
| e2 | shirt | a white shirt |
| e3 | tie | a tie |
| e4 | neck | her neck |
| e5 | hair | long hair |
| e6 | camera | the camera |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | The girl |
| f2 | object | e2 | exists |  | asserted | a white shirt |
| f3 | object | e3 | exists |  | asserted | a tie |
| f4 | object | e5 | exists |  | asserted | long hair |
| f5 | attribute | e2 | color | white | asserted | a white shirt |
| f6 | relation | e1 | wears | e2 | asserted | The girl in the picture is wearing a white shirt |
| f7 | relation | e3 | around | e4 | asserted | a tie around her neck |
| f8 | relation | e4 | part_of | e1 | asserted | her neck |
| f9 | attribute | e5 | length | long | asserted | long hair |
| f10 | relation | e1 | has | e5 | asserted | She has long hair |
| f11 | action | e1 | smile |  | asserted | is smiling at the camera |
| f12 | relation | e1 | toward | e6 | asserted | smiling at the camera |

## 18 — 159736_vista_beam5

原始 caption：

> A person is holding a plate with a piece of cake on it.

**0-shot 复核：** person holds plate、cake on plate，未添加 person holds cake，也未推断性别。

**8-shot 复核：** 同样保留两条明确关系；cake_piece 较好保留 piece 计量形态。

**仍存问题：** 本条预设主要检查项两者均通过；cake 与 cake_piece 的归一化边界要在后续对齐中明示，不能因词形差异直接判 removed/added。

### 18_s0_r1 — success

原始记录：[JSON](checkpoints/18_s0_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | person | A person |
| e2 | plate | a plate |
| e3 | cake | a piece of cake |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | A person |
| f2 | object | e2 | exists |  | asserted | a plate |
| f3 | object | e3 | exists |  | asserted | a piece of cake |
| f4 | relation | e1 | holds | e2 | asserted | A person is holding a plate |
| f5 | relation | e3 | on | e2 | asserted | a plate with a piece of cake on it |

### 18_s8_r1 — success

原始记录：[JSON](checkpoints/18_s8_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | person | A person |
| e2 | plate | a plate |
| e3 | cake_piece | a piece of cake |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | A person |
| f2 | object | e2 | exists |  | asserted | a plate |
| f3 | object | e3 | exists |  | asserted | a piece of cake |
| f4 | relation | e1 | holds | e2 | asserted | A person is holding a plate |
| f5 | relation | e3 | on | e2 | asserted | a plate with a piece of cake on it |

## 20 — 451972_vanilla_greedy

原始 caption：

> The image features a red fire truck with a large Santa Claus float on its back, driving down a street. The fire truck is adorned with Christmas decorations, making it a festive sight.
>
> There are several people around the fire truck, with some standing closer to the truck and others further away. Some of the people are closer to the front of the truck, while others are positioned towards the back. The scene captures the excitement and joy of the holiday season.

**0-shot 复核：** 保留 Santa Claus float、红车、装饰和前后远近子组；遗漏 several 数量、street 路径关系与 standing。

**8-shot 复核：** 补出 count(several)、truck on street、两个远近子组的 stand，保留一般人群与各子组，没有相加推算人数。

**仍存问题：** 两个条件的 float on truck 都没有保留 on its back 的 back 信息，具体空间范围仍有损失。

### 20_s0_r1 — success

原始记录：[JSON](checkpoints/20_s0_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | fire_truck | fire truck |
| e2 | santa_claus_float | Santa Claus float |
| e3 | street | street |
| e4 | christmas_decorations | Christmas decorations |
| e5 | people | several people |
| e6 | people | some |
| e7 | people | others |
| e8 | people | Some of the people |
| e9 | people | others |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | fire truck |
| f2 | object | e2 | exists |  | asserted | Santa Claus float |
| f3 | object | e3 | exists |  | asserted | street |
| f4 | object | e4 | exists |  | asserted | Christmas decorations |
| f5 | object | e5 | exists |  | asserted | several people |
| f6 | attribute | e1 | color | red | asserted | red fire truck |
| f7 | attribute | e2 | size | large | asserted | large Santa Claus float |
| f8 | relation | e2 | on | e1 | asserted | Santa Claus float on its back |
| f9 | action | e1 | drive |  | asserted | driving down a street |
| f10 | relation | e1 | adorned_with | e4 | asserted | fire truck is adorned with Christmas decorations |
| f11 | relation | e5 | around | e1 | asserted | several people around the fire truck |
| f12 | relation | e6 | closer_to | e1 | asserted | some standing closer to the truck |
| f13 | relation | e7 | further_from | e1 | asserted | others further away |
| f14 | relation | e8 | closer_to_front | e1 | asserted | Some of the people are closer to the front of the truck |
| f15 | relation | e9 | towards_back | e1 | asserted | others are positioned towards the back |

### 20_s8_r1 — success

原始记录：[JSON](checkpoints/20_s8_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | fire_truck | a red fire truck |
| e2 | santa_claus_float | a large Santa Claus float |
| e3 | street | a street |
| e4 | christmas_decoration | Christmas decorations |
| e5 | person | several people |
| e6 | person | some |
| e7 | person | others |
| e8 | person | Some of the people |
| e9 | person | others |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | a red fire truck |
| f2 | object | e2 | exists |  | asserted | a large Santa Claus float |
| f3 | object | e3 | exists |  | asserted | a street |
| f4 | object | e4 | exists |  | asserted | Christmas decorations |
| f5 | object | e5 | exists |  | asserted | several people |
| f6 | attribute | e1 | color | red | asserted | a red fire truck |
| f7 | attribute | e2 | size | large | asserted | a large Santa Claus float |
| f8 | relation | e2 | on | e1 | asserted | a large Santa Claus float on its back |
| f9 | action | e1 | drive |  | asserted | driving down a street |
| f10 | relation | e1 | on | e3 | asserted | driving down a street |
| f11 | relation | e1 | adorned_with | e4 | asserted | The fire truck is adorned with Christmas decorations |
| f12 | count | ["e5"] | count | several | asserted | several people |
| f13 | relation | e5 | around | e1 | asserted | several people around the fire truck |
| f14 | action | e6 | stand |  | asserted | some standing closer to the truck |
| f15 | relation | e6 | closer_to | e1 | asserted | some standing closer to the truck |
| f16 | action | e7 | stand |  | asserted | others further away |
| f17 | relation | e7 | further_from | e1 | asserted | others further away |
| f18 | relation | e8 | closer_to_front_of | e1 | asserted | Some of the people are closer to the front of the truck |
| f19 | relation | e9 | towards_back_of | e1 | asserted | others are positioned towards the back |

## 21 — 43098_vista_greedy

原始 caption：

> The image features a blue suitcase with a handle on a sidewalk. The suitcase is placed on the sidewalk, and a man is walking past it. The man is wearing a jacket and jeans, and he is walking past the suitcase.

**0-shot 复核：** handle 有实体却无存在事实；walking past 只写 walk(man,suitcase)，遗漏 past 含义。

**8-shot 复核：** 补 handle exists，改为 walk_past(man,suitcase)，保留蓝箱、夹克和牛仔裤；重复的 walking past 没有计两次。

**仍存问题：** 本条预设主要检查项较零示例改善。去重后 f10 缺号是可接受的局部 ID，不应当作语义错误。

### 21_s0_r1 — success

原始记录：[JSON](checkpoints/21_s0_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | suitcase | blue suitcase |
| e2 | handle | a handle |
| e3 | sidewalk | a sidewalk |
| e4 | man | a man |
| e5 | jacket | a jacket |
| e6 | jeans | jeans |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | blue suitcase |
| f2 | attribute | e1 | color | blue | asserted | blue suitcase |
| f3 | relation | e1 | has | e2 | asserted | with a handle |
| f4 | relation | e1 | on | e3 | asserted | on a sidewalk |
| f5 | object | e3 | exists |  | asserted | a sidewalk |
| f6 | object | e4 | exists |  | asserted | a man |
| f7 | action | e4 | walk | e1 | asserted | walking past it |
| f8 | relation | e4 | wears | e5 | asserted | wearing a jacket |
| f9 | relation | e4 | wears | e6 | asserted | wearing a jacket and jeans |
| f10 | object | e5 | exists |  | asserted | a jacket |
| f11 | object | e6 | exists |  | asserted | jeans |

### 21_s8_r1 — success

原始记录：[JSON](checkpoints/21_s8_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | suitcase | a blue suitcase |
| e2 | handle | a handle |
| e3 | sidewalk | a sidewalk |
| e4 | man | a man |
| e5 | jacket | a jacket |
| e6 | jeans | jeans |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | a blue suitcase |
| f2 | object | e2 | exists |  | asserted | a handle |
| f3 | object | e3 | exists |  | asserted | a sidewalk |
| f4 | object | e4 | exists |  | asserted | a man |
| f5 | object | e5 | exists |  | asserted | a jacket |
| f6 | object | e6 | exists |  | asserted | jeans |
| f7 | attribute | e1 | color | blue | asserted | a blue suitcase |
| f8 | relation | e1 | has | e2 | asserted | a blue suitcase with a handle |
| f9 | relation | e1 | on | e3 | asserted | a blue suitcase with a handle on a sidewalk |
| f11 | action | e4 | walk_past | e1 | asserted | a man is walking past it |
| f12 | relation | e4 | wears | e5 | asserted | The man is wearing a jacket and jeans |
| f13 | relation | e4 | wears | e6 | asserted | The man is wearing a jacket and jeans |

## 24 — 3501_vanilla_top_p

原始 caption：

> The image features a bowl filled with a mixture of rice and beans, topped with a variety of broccoli pieces. There are several pieces of broccoli scattered throughout the bowl, with some larger and closer to the center and others smaller and more towards the outer edge of the bowl. The broccoli and rice combination creates a colorful and appetizing meal.

**0-shot 复核：** 结构通过且保留 rice AND beans；遗漏 several，并把 larger/smaller、center/edge 都附到同一 broccoli_pieces 锚点，抹掉 some/others 子组范围。

**8-shot 复核：** 主测和重复均因 mention 首字母大小写错误失败，修复重试也未改正；失败原始响应不能作为正式可用结果。

**仍存问题：** 只能对失败原始响应作诊断：第二次运行分出了大小子组和 several，但不能据此计为成功或宣称准确率改善。

### 24_s0_r1 — success

原始记录：[JSON](checkpoints/24_s0_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | bowl | bowl |
| e2 | rice | rice |
| e3 | beans | beans |
| e4 | broccoli_pieces | broccoli pieces |
| e5 | broccoli | broccoli |
| e6 | rice | rice |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | bowl |
| f2 | object | e2 | exists |  | asserted | rice |
| f3 | object | e3 | exists |  | asserted | beans |
| f4 | object | e4 | exists |  | asserted | broccoli pieces |
| f5 | object | e5 | exists |  | asserted | broccoli |
| f6 | relation | e1 | filled_with | e2 | asserted | bowl filled with a mixture of rice and beans |
| f7 | relation | e1 | filled_with | e3 | asserted | bowl filled with a mixture of rice and beans |
| f8 | relation | e1 | topped_with | e4 | asserted | topped with a variety of broccoli pieces |
| f9 | relation | e4 | scattered_throughout | e1 | asserted | several pieces of broccoli scattered throughout the bowl |
| f10 | attribute | e4 | size | larger | asserted | some larger |
| f11 | attribute | e4 | position | closer to the center | asserted | closer to the center |
| f12 | attribute | e4 | size | smaller | asserted | others smaller |
| f13 | attribute | e4 | position | more towards the outer edge of the bowl | asserted | more towards the outer edge of the bowl |
| f14 | relation | e5 | combination | e6 | asserted | broccoli and rice combination |

### 24_s8_r1 — failed

原始记录：[JSON](checkpoints/24_s8_r1.json)

第 1 次请求错误：Invalid API response: mention must be a verbatim substring, including case

- `entities[id=e7].mention` = `the broccoli and rice combination`

第 2 次请求错误：Invalid API response: mention must be a verbatim substring, including case

- `entities[id=e7].mention` = `the broccoli and rice combination`

### 24_s8_r2 — failed

原始记录：[JSON](checkpoints/24_s8_r2.json)

第 1 次请求错误：Invalid API response: mention must be a verbatim substring, including case

- `entities[id=e9].mention` = `the broccoli and rice combination`

第 2 次请求错误：Invalid API response: mention must be a verbatim substring, including case

- `entities[id=e9].mention` = `the broccoli and rice combination`

## 25 — 554582_vanilla_top_p

原始 caption：

> In the image, there is a group of three older gentlemen sitting together on a white concrete bench, taking a break. They appear to be enjoying each other's company and relaxing outdoors. The bench is positioned on a sidewalk in front of a building.
>
> In the background, a truck is visible, parked at a short distance from the men. It can be inferred that they might be observing or waiting for the truck's activities or perhaps the truck is related to their work or daily activities.

**0-shot 复核：** 保留 three、older、white/concrete、休息、truck parked 及部分 speculative 分支。

**8-shot 复核：** 额外保留 speculative relax 和背景位置；人数仍为三人，没把一般组与 the men 相加。

**仍存问题：** 两者都把 truck's activities 简化成 truck，把 related to their work or daily activities 简化为 related_to(truck,men)，丢失活动/工作对象与替代分支；8-shot 也未保留 outdoors。

### 25_s0_r1 — success

原始记录：[JSON](checkpoints/25_s0_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | group_of_older_gentlemen | a group of three older gentlemen |
| e2 | bench | a white concrete bench |
| e3 | sidewalk | a sidewalk |
| e4 | building | a building |
| e5 | truck | a truck |
| e6 | group_of_older_gentlemen | the men |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | there is a group of three older gentlemen |
| f2 | count | older_gentlemen | count_eq | 3 | asserted | three older gentlemen |
| f3 | attribute | e1 | age | older | asserted | older gentlemen |
| f4 | action | e1 | sit |  | asserted | sitting together |
| f5 | relation | e1 | on | e2 | asserted | sitting together on a white concrete bench |
| f6 | action | e1 | take_a_break |  | asserted | taking a break |
| f7 | object | e2 | exists |  | asserted | a white concrete bench |
| f8 | attribute | e2 | color | white | asserted | white concrete bench |
| f9 | attribute | e2 | material | concrete | asserted | concrete bench |
| f10 | relation | e2 | on | e3 | asserted | bench is positioned on a sidewalk |
| f11 | object | e3 | exists |  | asserted | a sidewalk |
| f12 | relation | e3 | in_front_of | e4 | asserted | sidewalk in front of a building |
| f13 | object | e4 | exists |  | asserted | a building |
| f14 | object | e5 | exists |  | asserted | a truck is visible |
| f15 | action | e5 | park |  | asserted | parked at a short distance from the men |
| f16 | relation | e5 | at_short_distance_from | e6 | asserted | parked at a short distance from the men |
| f17 | action | e6 | observe |  | speculative | they might be observing |
| f18 | action | e6 | wait_for | e5 | speculative | waiting for the truck's activities |
| f19 | relation | e5 | related_to | e6 | speculative | the truck is related to their work or daily activities |

### 25_s8_r1 — success

原始记录：[JSON](checkpoints/25_s8_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | group_of_men | a group of three older gentlemen |
| e2 | bench | a white concrete bench |
| e3 | sidewalk | a sidewalk |
| e4 | building | a building |
| e5 | truck | a truck |
| e6 | man | the men |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | a group of three older gentlemen |
| f2 | object | e2 | exists |  | asserted | a white concrete bench |
| f3 | object | e3 | exists |  | asserted | a sidewalk |
| f4 | object | e4 | exists |  | asserted | a building |
| f5 | object | e5 | exists |  | asserted | a truck |
| f6 | count | man | count | 3 | asserted | a group of three older gentlemen |
| f7 | attribute | e1 | age | older | asserted | older gentlemen |
| f8 | attribute | e2 | color | white | asserted | a white concrete bench |
| f9 | attribute | e2 | material | concrete | asserted | a white concrete bench |
| f10 | action | e1 | sit |  | asserted | a group of three older gentlemen sitting together on a white concrete bench |
| f11 | relation | e1 | on | e2 | asserted | a group of three older gentlemen sitting together on a white concrete bench |
| f12 | action | e1 | take_a_break |  | asserted | taking a break |
| f13 | action | e1 | relax |  | speculative | They appear to be enjoying each other's company and relaxing outdoors |
| f14 | relation | e2 | on | e3 | asserted | The bench is positioned on a sidewalk |
| f15 | relation | e2 | in_front_of | e4 | asserted | on a sidewalk in front of a building |
| f16 | attribute | e5 | image_position | background | asserted | In the background, a truck is visible |
| f17 | action | e5 | park |  | asserted | a truck is visible, parked at a short distance from the men |
| f18 | relation | e5 | at_short_distance_from | e6 | asserted | parked at a short distance from the men |
| f19 | action | e6 | observe | e5 | speculative | It can be inferred that they might be observing or waiting for the truck's activities |
| f20 | action | e6 | wait_for | e5 | speculative | It can be inferred that they might be observing or waiting for the truck's activities |
| f21 | relation | e5 | related_to | e6 | speculative | perhaps the truck is related to their work or daily activities |

## 26 — 3501_vista_top_p

原始 caption：

> A white bowl full of food sits on a tabletop. Rice and broccoli are among the ingredients.

**0-shot 复核：** 保留 white/full、food、tabletop、rice/broccoli，未从另一 caption 带入 beans。

**8-shot 复核：** 同样保留这些显式成分，没有带入 beans；增加 ingredient 抽象锚点承载 among。

**仍存问题：** 两个条件均将静态 bowl sits 拆出 sit 动作并另给 on 关系，造成冗余。8-shot 的 full_of 还将满的属性与容纳关系合并，独立变化边界不够清晰。

### 26_s0_r1 — success

原始记录：[JSON](checkpoints/26_s0_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | bowl | A white bowl |
| e2 | food | food |
| e3 | tabletop | a tabletop |
| e4 | rice | Rice |
| e5 | broccoli | broccoli |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | A white bowl |
| f2 | attribute | e1 | color | white | asserted | white bowl |
| f3 | attribute | e1 | fullness | full | asserted | full of food |
| f4 | object | e2 | exists |  | asserted | food |
| f5 | relation | e1 | contains | e2 | asserted | bowl full of food |
| f6 | action | e1 | sits |  | asserted | sits on a tabletop |
| f7 | object | e3 | exists |  | asserted | a tabletop |
| f8 | relation | e1 | on | e3 | asserted | sits on a tabletop |
| f9 | object | e4 | exists |  | asserted | Rice |
| f10 | object | e5 | exists |  | asserted | broccoli |
| f11 | relation | e4 | part_of | e2 | asserted | Rice and broccoli are among the ingredients |
| f12 | relation | e5 | part_of | e2 | asserted | Rice and broccoli are among the ingredients |

### 26_s8_r1 — success

原始记录：[JSON](checkpoints/26_s8_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | bowl | A white bowl |
| e2 | food | food |
| e3 | tabletop | a tabletop |
| e4 | rice | Rice |
| e5 | broccoli | broccoli |
| e6 | ingredient | the ingredients |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | A white bowl |
| f2 | object | e2 | exists |  | asserted | food |
| f3 | object | e3 | exists |  | asserted | a tabletop |
| f4 | object | e4 | exists |  | asserted | Rice |
| f5 | object | e5 | exists |  | asserted | broccoli |
| f6 | attribute | e1 | color | white | asserted | A white bowl |
| f7 | relation | e1 | full_of | e2 | asserted | A white bowl full of food |
| f8 | action | e1 | sit |  | asserted | A white bowl full of food sits on a tabletop |
| f9 | relation | e1 | on | e3 | asserted | A white bowl full of food sits on a tabletop |
| f10 | relation | e4 | among | e6 | asserted | Rice and broccoli are among the ingredients |
| f11 | relation | e5 | among | e6 | asserted | Rice and broccoli are among the ingredients |

## 29 — 159736_vanilla_beam5

原始 caption：

> In the image, a person is cutting a piece of cake on a plate using a knife. The cake is placed on a dining table, and there are multiple forks scattered around the table. Some of the forks are close to the cake, while others are positioned further away.
>
> In addition to the cake and forks, there are two bowls on the table. One bowl is located on the left side of the table, while the other is on the right side. The person cutting the cake appears to be focused on their task, enjoying the delicious dessert.

**0-shot 复核：** 保留 cake on plate 和直接声称的 cake on table，没有推导 plate on table；碗的左右是相对 table 的关系。但 cake/person 的明确指代被重复建锚。

**8-shot 复核：** 首轮合并了 cake 的明确指代，保留两处 cake 位置、cut、uses knife 和 two bowls。

**仍存问题：** 两者均遗漏 multiple forks 的 count。8-shot 将碗的 on left/right side of table 改成无 table 参照的 horizontal_position 属性；focused 情绪/注意状态仍输出。重复时又将 the table 新建锚点。

### 29_s0_r1 — success

原始记录：[JSON](checkpoints/29_s0_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | person | a person |
| e2 | cake | a piece of cake |
| e3 | plate | a plate |
| e4 | knife | a knife |
| e5 | cake | The cake |
| e6 | dining_table | a dining table |
| e7 | fork | multiple forks |
| e8 | fork | Some of the forks |
| e9 | fork | others |
| e10 | bowl | two bowls |
| e11 | bowl | One bowl |
| e12 | bowl | the other |
| e13 | person | The person |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | a person |
| f2 | object | e2 | exists |  | asserted | a piece of cake |
| f3 | object | e3 | exists |  | asserted | a plate |
| f4 | object | e4 | exists |  | asserted | a knife |
| f5 | object | e5 | exists |  | asserted | The cake |
| f6 | object | e6 | exists |  | asserted | a dining table |
| f7 | object | e7 | exists |  | asserted | multiple forks |
| f8 | object | e8 | exists |  | asserted | Some of the forks |
| f9 | object | e9 | exists |  | asserted | others |
| f10 | object | e10 | exists |  | asserted | two bowls |
| f11 | object | e11 | exists |  | asserted | One bowl |
| f12 | object | e12 | exists |  | asserted | the other |
| f13 | object | e13 | exists |  | asserted | The person |
| f14 | action | e1 | cut | e2 | asserted | is cutting |
| f15 | relation | e2 | on | e3 | asserted | on a plate |
| f16 | relation | e1 | using | e4 | asserted | using a knife |
| f17 | relation | e5 | on | e6 | asserted | placed on a dining table |
| f18 | relation | e7 | scattered_around | e6 | asserted | scattered around the table |
| f19 | relation | e8 | close_to | e5 | asserted | close to the cake |
| f20 | relation | e9 | positioned_further_away | e5 | asserted | positioned further away |
| f21 | count | bowl | count_eq | 2 | asserted | two bowls |
| f22 | relation | e10 | on | e6 | asserted | on the table |
| f23 | relation | e11 | on_left_side_of | e6 | asserted | located on the left side of the table |
| f24 | relation | e12 | on_right_side_of | e6 | asserted | on the right side |
| f25 | attribute | e13 | focused | true | speculative | appears to be focused on their task |

### 29_s8_r1 — success

原始记录：[JSON](checkpoints/29_s8_r1.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | person | a person |
| e2 | cake | a piece of cake |
| e3 | plate | a plate |
| e4 | knife | a knife |
| e5 | table | a dining table |
| e6 | fork | multiple forks |
| e7 | fork | Some of the forks |
| e8 | fork | others |
| e9 | bowl | two bowls |
| e10 | bowl | One bowl |
| e11 | bowl | the other |
| e12 | person | The person cutting the cake |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | a person |
| f2 | object | e2 | exists |  | asserted | a piece of cake |
| f3 | object | e3 | exists |  | asserted | a plate |
| f4 | object | e4 | exists |  | asserted | a knife |
| f5 | object | e5 | exists |  | asserted | a dining table |
| f6 | object | e6 | exists |  | asserted | multiple forks |
| f7 | object | e9 | exists |  | asserted | two bowls |
| f8 | action | e1 | cut | e2 | asserted | a person is cutting a piece of cake |
| f9 | relation | e2 | on | e3 | asserted | a piece of cake on a plate |
| f10 | relation | e1 | uses | e4 | asserted | using a knife |
| f11 | relation | e2 | on | e5 | asserted | The cake is placed on a dining table |
| f12 | relation | e6 | scattered_around | e5 | asserted | multiple forks scattered around the table |
| f13 | relation | e7 | close_to | e2 | asserted | Some of the forks are close to the cake |
| f14 | relation | e8 | further_from | e2 | asserted | others are positioned further away |
| f15 | count | ["e9"] | count | 2 | asserted | two bowls |
| f16 | relation | e9 | on | e5 | asserted | two bowls on the table |
| f17 | attribute | e10 | horizontal_position | left | asserted | One bowl is located on the left side of the table |
| f18 | attribute | e11 | horizontal_position | right | asserted | the other is on the right side |
| f19 | action | e12 | be_focused_on |  | speculative | The person cutting the cake appears to be focused on their task |

### 29_s8_r2 — success

原始记录：[JSON](checkpoints/29_s8_r2.json)

| Entity | canonical | mention |
| --- | --- | --- |
| e1 | person | a person |
| e2 | cake | a piece of cake |
| e3 | plate | a plate |
| e4 | knife | a knife |
| e5 | table | a dining table |
| e6 | fork | multiple forks |
| e7 | fork | Some of the forks |
| e8 | fork | others |
| e9 | bowl | two bowls |
| e10 | bowl | One bowl |
| e11 | bowl | the other |
| e12 | table | the table |

| Fact | type | subject / target | predicate | object / value | assertion | source |
| --- | --- | --- | --- | --- | --- | --- |
| f1 | object | e1 | exists |  | asserted | a person |
| f2 | object | e2 | exists |  | asserted | a piece of cake |
| f3 | object | e3 | exists |  | asserted | a plate |
| f4 | object | e4 | exists |  | asserted | a knife |
| f5 | object | e5 | exists |  | asserted | a dining table |
| f6 | object | e6 | exists |  | asserted | multiple forks |
| f7 | object | e9 | exists |  | asserted | two bowls |
| f8 | action | e1 | cut | e2 | asserted | a person is cutting a piece of cake on a plate using a knife |
| f9 | relation | e2 | on | e3 | asserted | a piece of cake on a plate |
| f10 | relation | e1 | uses | e4 | asserted | using a knife |
| f11 | relation | e2 | on | e5 | asserted | The cake is placed on a dining table |
| f12 | relation | e6 | scattered_around | e5 | asserted | multiple forks scattered around the table |
| f13 | relation | e7 | close_to | e2 | asserted | Some of the forks are close to the cake |
| f14 | relation | e8 | further_from | e2 | asserted | others are positioned further away |
| f15 | count | ["e9"] | count | 2 | asserted | two bowls |
| f16 | relation | e9 | on | e12 | asserted | two bowls on the table |
| f17 | attribute | e10 | horizontal_position | left | asserted | One bowl is located on the left side of the table |
| f18 | attribute | e11 | horizontal_position | right | asserted | the other is on the right side |
| f19 | action | e1 | be_focused_on_task |  | speculative | The person cutting the cake appears to be focused on their task |
