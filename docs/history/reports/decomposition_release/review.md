# 真实 API 拆分试运行：逐条抽查

本文件记录原文、事实与语义核心词；不判断图片真实性。

## 332570_vanilla_greedy

The image features a close-up of a person's hand holding a smartphone. The phone is open and displaying a screen with various options, including a menu and a search bar. The hand is positioned in the upper left corner of the image, with the phone occupying the majority of the frame. The person's thumb is visible on the bottom right side of the phone, likely used for navigating the screen.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | hand exists | 11:hand | NOUN |  |
| f2 | relation.possession | hand belongs to person | 10:'s | PART |  |
| f3 | relation.possession | hand is holding smartphone | 12:holding | VERB |  |
| f4 | relation.spatial | hand is in upper left corner of image | 40:in, 42:upper, 43:left, 44:corner, 45:of | ADP, ADJ, ADJ, NOUN, ADP |  |
| f5 | object.existence | menu exists | 30:menu | NOUN |  |
| f6 | object.existence | person exists | 9:person | NOUN |  |
| f7 | object.existence | screen exists | 23:screen | NOUN |  |
| f8 | object.existence | search bar exists | 33:search, 34:bar | NOUN, NOUN |  |
| f9 | object.existence | smartphone exists | 14:smartphone | NOUN |  |
| f10 | attribute.state | smartphone is open | 19:open | ADJ |  |
| f11 | action.interaction | smartphone is displaying screen | 21:displaying | VERB |  |
| f12 | relation.spatial | smartphone occupies majority of frame | 52:occupying, 54:majority, 55:of, 57:frame | VERB, NOUN, ADP, NOUN |  |
| f13 | object.existence | thumb exists | 62:thumb | NOUN |  |
| f14 | attribute.state | thumb is visible | 64:visible | ADJ |  |
| f15 | relation.possession | thumb belongs to person | 61:'s | PART |  |
| f16 | relation.spatial | thumb is on bottom right side of smartphone | 65:on, 67:bottom, 68:right, 69:side, 70:of | ADP, ADJ, ADJ, NOUN, ADP |  |
| f17 | subjective.inference | thumb is likely used for navigating screen | 74:likely, 75:used, 76:for, 77:navigating | ADV, VERB, ADP, VERB |  |

## 352478_vanilla_greedy

The image features a large display of fresh vegetables, including a variety of broccoli and lettuce, arranged in a market setting. The broccoli is displayed in two separate piles, one on the left side and the other on the right side of the image. The lettuce is also displayed in two piles, one in the middle and the other on the right side.

In addition to the vegetables, there are several potted plants placed throughout the scene, adding a touch of greenery to the display. A bicycle can be seen in the background, possibly belonging to a customer or a vendor. There are also a few people present in the scene, likely browsing the vegetable selection or attending to the market.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | bicycle exists | 97:bicycle | NOUN |  |
| f2 | relation.spatial | bicycle is in background | 101:in, 103:background | ADP, NOUN |  |
| f3 | subjective.inference | bicycle possibly belongs to customer or vendor | 105:possibly, 106:belonging, 107:to, 110:or, 112:vendor | ADV, VERB, ADP, CCONJ, NOUN |  |
| f4 | object.existence | broccoli exists | 14:broccoli | NOUN |  |
| f5 | relation.spatial | broccoli pile is on left side of image | 34:on, 36:left, 37:side, 45:of, 47:image | ADP, ADJ, NOUN, ADP, NOUN |  |
| f6 | relation.spatial | broccoli pile is on right side of image | 41:on, 43:right, 44:side, 45:of, 47:image | ADP, ADJ, NOUN, ADP, NOUN |  |
| f7 | count.exact | number of broccoli piles is 2 | 29:two | NUM |  |
| f8 | object.existence | lettuce exists | 16:lettuce | NOUN |  |
| f9 | relation.spatial | lettuce pile is in middle | 59:in, 61:middle | ADP, NOUN |  |
| f10 | relation.spatial | lettuce pile is on right side | 65:on, 67:right, 68:side | ADP, ADJ, NOUN |  |
| f11 | count.exact | number of lettuce piles is 2 | 55:two | NUM |  |
| f12 | object.existence | market setting exists | 21:market, 22:setting | NOUN, NOUN |  |
| f13 | object.existence | people exist | 119:people | NOUN |  |
| f14 | count.approximate | number of people is a few | 118:few | ADJ |  |
| f15 | subjective.inference | people are likely browsing vegetable selection or attending to market | 125:likely, 126:browsing, 128:vegetable, 129:selection, 130:or, 131:attending, 132:to, 134:market | ADV, VERB, NOUN, NOUN, CCONJ, VERB, ADP, NOUN | pos_models_disagree |
| f16 | object.existence | potted plants exist | 80:potted, 81:plants | ADJ, NOUN |  |
| f17 | relation.spatial | potted plants are throughout scene | 83:throughout, 85:scene | ADP, NOUN |  |
| f18 | count.approximate | number of potted plants is several | 79:several | ADJ |  |
| f19 | object.existence | vegetables exist | 8:vegetables | NOUN |  |
| f20 | attribute.state | vegetables are fresh | 7:fresh | ADJ |  |
| f21 | relation.spatial | vegetables are in market setting | 19:in, 21:market, 22:setting | ADP, NOUN, NOUN |  |

## 332570_vista_greedy

A hand holding a cell phone with a keyboard on it.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | cell phone exists | 4:cell, 5:phone | NOUN, NOUN |  |
| f2 | object.existence | hand exists | 1:hand | NOUN |  |
| f3 | relation.possession | hand is holding cell phone | 2:holding | VERB |  |
| f4 | object.existence | keyboard exists | 8:keyboard | NOUN |  |
| f5 | relation.spatial | keyboard is on cell phone | 9:on | ADP |  |

## 54627_vista_greedy

The image depicts a group of horses grazing in a field. There are at least four horses visible in the scene. They are spread out across the field, some are closer to the camera while others are further away. The horses are grazing on grass, and some are positioned near trees.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | field exists | 10:field | NOUN |  |
| f2 | object.existence | grass exists | 48:grass | NOUN |  |
| f3 | object.existence | horses exist | 6:horses | NOUN |  |
| f4 | attribute.state | horses are visible | 18:visible | ADJ |  |
| f5 | action.interaction | horses are grazing on grass | 46:grazing, 47:on | VERB, ADP |  |
| f6 | relation.spatial | horses are in field | 8:in | ADP |  |
| f7 | relation.spatial | horses are spread out across field | 25:spread, 26:out, 27:across | VERB, ADP, ADP |  |
| f8 | count.approximate | number of horses is at least four | 14:at, 15:least, 16:four | ADV, ADJ, NUM | pos_models_disagree |
| f9 | relation.spatial | other horses are further away | 候选: 38:others, 40:further, 41:away / 候选: 40:further, 41:away |  | semantic_anchors_disagree |
| f10 | relation.spatial | some horses are closer to camera | 候选: 31:some, 33:closer, 34:to / 候选: 33:closer, 34:to |  | semantic_anchors_disagree |
| f11 | relation.spatial | some horses are positioned near trees | 候选: 51:some, 53:positioned, 54:near / 候选: 53:positioned, 54:near |  | semantic_anchors_disagree |
| f12 | object.existence | trees exist | 55:trees | NOUN |  |

## 332570_vanilla_beam5

The image features a close-up view of a person's hand holding a cell phone. The cell phone is prominently displayed in the foreground, occupying a significant portion of the image. On the screen of the cell phone, there is a menu visible, indicating that the person might be using the device for various purposes, such as browsing the internet, texting, or making calls. The hand holding the cell phone appears to be in focus, while the rest of the scene is slightly blurred, creating a sense of depth in the image.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | cell phone exists | 15:cell, 16:phone | NOUN, NOUN |  |
| f2 | attribute.appearance | cell phone is prominently displayed | 22:prominently, 23:displayed | ADV, VERB |  |
| f3 | relation.spatial | cell phone is in foreground | 24:in, 26:foreground | ADP, NOUN |  |
| f4 | relation.spatial | cell phone occupies significant portion of image | 28:occupying, 30:significant, 31:portion, 32:of, 34:image | VERB, ADJ, NOUN, ADP, NOUN |  |
| f5 | object.existence | hand exists | 12:hand | NOUN |  |
| f6 | attribute.state | hand appears to be in focus | 81:appears, 82:to, 83:be, 84:in, 85:focus | VERB, PART, AUX, ADP, NOUN |  |
| f7 | relation.possession | hand belongs to person | 11:'s | PART |  |
| f8 | relation.possession | hand is holding cell phone | 13:holding | VERB |  |
| f9 | subjective.aesthetic | image creates a sense of depth | 97:creating, 98:a, 99:sense, 100:of, 101:depth, 102:in, 103:the, 104:image | VERB, DET, NOUN, ADP, NOUN, ADP, DET, NOUN |  |
| f10 | object.existence | menu exists | 47:menu | NOUN |  |
| f11 | attribute.state | menu is visible | 48:visible | ADJ |  |
| f12 | relation.spatial | menu is on screen | 36:On, 38:screen | ADP, NOUN |  |
| f13 | object.existence | person exists | 10:person | NOUN |  |
| f14 | subjective.inference | person might be using device for various purposes, such as browsing the internet, texting, or making calls | 54:might, 56:using, 58:device, 59:for, 60:various, 61:purposes, 63:such, 64:as, 65:browsing, 66:the, 67:internet, 69:texting, 71:or, 72:making, 73:calls | AUX, VERB, NOUN, ADP, ADJ, NOUN, ADJ, ADP, VERB, DET, NOUN, NOUN, CCONJ, VERB, NOUN |  |
| f15 | attribute.state | rest of scene is slightly blurred | 89:rest, 90:of, 91:the, 92:scene, 93:is, 94:slightly, 95:blurred | NOUN, ADP, DET, NOUN, AUX, ADV, VERB |  |
| f16 | object.existence | screen exists | 38:screen | NOUN |  |
| f17 | relation.other | screen is part of cell phone | 39:of | ADP |  |

## 331883_vista_beam5

The man is sleeping on a mattress on a floor.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | floor exists | 9:floor | NOUN |  |
| f2 | object.existence | man exists | 1:man | NOUN |  |
| f3 | action.pose | man is sleeping | 3:sleeping | VERB |  |
| f4 | relation.spatial | man is on mattress | 4:on | ADP |  |
| f5 | object.existence | mattress exists | 6:mattress | NOUN |  |
| f6 | relation.spatial | mattress is on floor | 7:on | ADP |  |

## 332570_vanilla_top_p

The image features a person's hand holding a Palm Treo smartphone up close. The hand is in the foreground, occupying most of the frame, while the phone fills the middle of the scene. On the screen, there is a menu displayed with various options, including a search function. This gives the impression of the smartphone in use, possibly for browsing, searching for information, or making a call.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | hand exists | 6:hand | NOUN |  |
| f2 | relation.possession | hand belongs to person | 5:'s | PART |  |
| f3 | relation.possession | hand is holding smartphone | 7:holding | VERB |  |
| f4 | relation.spatial | hand is in foreground | 18:in, 20:foreground | ADP, NOUN |  |
| f5 | relation.spatial | hand occupies most of frame | 22:occupying, 23:most, 24:of, 26:frame | VERB, ADJ, ADP, NOUN |  |
| f6 | object.existence | menu exists | 45:menu | NOUN |  |
| f7 | relation.other | menu has various options | 候选: 47:with, 48:various / 候选: 47:with, 48:various, 49:options |  | semantic_anchors_disagree |
| f8 | relation.spatial | menu is displayed on screen | 38:On, 40:screen, 46:displayed | ADP, NOUN, VERB |  |
| f9 | object.existence | options exist | 49:options | NOUN |  |
| f10 | relation.other | options include search function | 候选: 51:including / 候选: 51:including, 53:search, 54:function |  | semantic_anchors_disagree |
| f11 | object.existence | person exists | 4:person | NOUN |  |
| f12 | object.existence | screen exists | 40:screen | NOUN |  |
| f13 | object.existence | search function exists | 53:search, 54:function | NOUN, NOUN |  |
| f14 | object.existence | smartphone exists | 11:smartphone | NOUN | pos_models_disagree |
| f15 | attribute.appearance | smartphone is up close | 12:up, 13:close | ADP, ADV |  |
| f16 | attribute.other | smartphone is Palm Treo | 9:Palm, 10:Treo | PROPN, PROPN |  |
| f17 | relation.spatial | smartphone fills middle of scene | 31:fills, 33:middle, 34:of, 36:scene | VERB, NOUN, ADP, NOUN |  |
| f18 | subjective.inference | smartphone might be in use, possibly for browsing, searching for information, or making a call | 候选: 56:This, 57:gives, 59:impression, 60:of, 62:smartphone, 63:in, 64:use, 66:possibly, 67:for, 68:browsing, 70:searching, 71:for, 72:information, 74:or, 75:making, 77:call / 候选: 63:in, 64:use, 66:possibly, 67:for, 68:browsing, 70:searching, 71:for, 72:information, 74:or, 75:making, 77:call |  | semantic_anchors_disagree |

## 332570_vista_top_p

the palm palm is in the foreground with a hand in the background holding a phone.

| ID | 类型 | 事实 | 核心 token | POS | 质量标记 |
|---|---|---|---|---|---|
| f1 | object.existence | hand exists | 9:hand | NOUN |  |
| f2 | relation.possession | hand is holding phone | 13:holding | VERB |  |
| f3 | relation.spatial | hand is in background | 10:in, 12:background | ADP, NOUN |  |
| f4 | object.existence | palm exists | 1:palm | NOUN |  |
| f5 | relation.spatial | palm is in foreground | 4:in, 6:foreground | ADP, NOUN |  |
| f6 | object.existence | phone exists | 15:phone | NOUN |  |
