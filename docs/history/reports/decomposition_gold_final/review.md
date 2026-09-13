# 真实 API 拆分试运行：逐条抽查

本文件记录原文、事实与语义核心词；不判断图片真实性。

## gold_red_bus_fixture_reference

A red car is beside a blue bus.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | bus exists | 7:bus | NOUN |  |
| f2 | attribute.color | bus is blue | 6:blue | ADJ |  |
| f3 | object.existence | car exists | 2:car | NOUN |  |
| f4 | attribute.color | car is red | 1:red | ADJ |  |
| f5 | relation.spatial | car is beside bus | 4:beside | ADP |  |

## gold_ownership_fixture_reference

A person's hand is holding a phone.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | hand exists | 3:hand | NOUN |  |
| f2 | relation.possession | hand belongs to person | 2:'s | PART |  |
| f3 | relation.possession | hand is holding phone | 5:holding | VERB |  |
| f4 | object.existence | person exists | 1:person | NOUN |  |
| f5 | object.existence | phone exists | 7:phone | NOUN |  |

## gold_count_fixture_reference

Two dogs are running.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | dogs exist | 1:dogs | NOUN |  |
| f2 | action.motion | dogs are running | 3:running | VERB |  |
| f3 | count.exact | number of dogs is 2 | 0:Two | NUM |  |

## gold_scene_fixture_reference

The scene is outdoors on a cloudy day.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | scene.location | scene is outdoors | 3:outdoors | ADV |  |
| f2 | scene.weather | weather is cloudy | 6:cloudy | ADJ |  |

## gold_properties_fixture_reference

A large brown dog is sitting under a wooden table.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | dog exists | 3:dog | NOUN |  |
| f2 | attribute.color | dog is brown | 2:brown | ADJ |  |
| f3 | attribute.size | dog is large | 1:large | ADJ |  |
| f4 | action.pose | dog is sitting | 5:sitting | VERB |  |
| f5 | relation.spatial | dog is under table | 6:under | ADP |  |
| f6 | object.existence | table exists | 9:table | NOUN |  |
| f7 | attribute.material | table is wooden | 8:wooden | ADJ |  |

## gold_subjective_fixture_reference

A dog looks happy.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | dog exists | 1:dog | NOUN |  |
| f2 | subjective.emotion | dog looks happy | 2:looks, 3:happy | VERB, ADJ |  |

## gold_negation_fixture_reference

No dog is beside the car.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | car exists | 5:car | NOUN |  |
| f2 | relation.spatial | dog is not beside car | 0:No, 3:beside | DET, ADP |  |

## gold_alternative_fixture_reference

A person might be browsing or making a call.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | person exists | 1:person | NOUN |  |
| f2 | subjective.inference | person might be browsing or making a call | 2:might, 4:browsing, 5:or, 6:making, 8:call | AUX, VERB, CCONJ, VERB, NOUN |  |

## gold_entities_fixture_reference

The left dog is black. The right dog is white.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | left dog exists | 1:left, 2:dog | ADJ, NOUN |  |
| f2 | attribute.color | left dog is black | 4:black | ADJ |  |
| f3 | object.existence | right dog exists | 7:right, 8:dog | ADJ, NOUN |  |
| f4 | attribute.color | right dog is white | 10:white | ADJ |  |

## gold_brand_fixture_reference

A hand is holding a Palm Treo smartphone.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | hand exists | 1:hand | NOUN |  |
| f2 | relation.possession | hand is holding smartphone | 3:holding | VERB |  |
| f3 | object.existence | smartphone exists | 7:smartphone | NOUN |  |
| f4 | attribute.other | smartphone is Palm Treo | 5:Palm, 6:Treo | PROPN, PROPN |  |

## gold_empty_fixture_reference



| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|

## gold_no_implicit_relation_fixture_reference

A phone is visible. On the screen there is a menu.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | menu exists | 11:menu | NOUN |  |
| f2 | relation.spatial | menu is on screen | 5:On, 7:screen | ADP, NOUN |  |
| f3 | object.existence | phone exists | 1:phone | NOUN |  |
| f4 | attribute.state | phone is visible | 3:visible | ADJ |  |
| f5 | object.existence | screen exists | 7:screen | NOUN |  |

## gold_grazing_fixture_reference

Horses are grazing on grass in a field.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | field exists | 7:field | NOUN |  |
| f2 | object.existence | grass exists | 4:grass | NOUN |  |
| f3 | object.existence | horses exist | 0:Horses | NOUN |  |
| f4 | action.interaction | horses are grazing on grass | 2:grazing, 3:on | VERB, ADP |  |
| f5 | relation.spatial | horses are in field | 5:in | ADP |  |
