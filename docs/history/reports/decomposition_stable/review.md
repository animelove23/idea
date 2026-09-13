# 真实 API 拆分试运行：逐条抽查

本文件记录原文、事实与语义核心词；不判断图片真实性。

## 332570_vanilla_greedy

The image features a close-up of a person's hand holding a smartphone. The phone is open and displaying a screen with various options, including a menu and a search bar. The hand is positioned in the upper left corner of the image, with the phone occupying the majority of the frame. The person's thumb is visible on the bottom right side of the phone, likely used for navigating the screen.

| ID | 类型 | 事实 | 核心 token | POS |
|---|---|---|---|---|
| f1 | object.existence | hand exists | 11:hand | NOUN |
| f2 | relation.possession | hand belongs to person | 10:'s | PART |
| f3 | relation.possession | hand is holding smartphone | 12:holding | VERB |
| f4 | relation.spatial | hand is in upper left corner of image |  |  |
| f5 | object.existence | menu exists | 30:menu | NOUN |
| f6 | object.existence | person exists | 9:person | NOUN |
| f7 | attribute.state | phone is open | 19:open | ADJ |
| f8 | relation.spatial | phone occupies majority of frame | 52:occupying, 54:majority, 55:of, 57:frame | VERB, NOUN, ADP, NOUN |
| f9 | object.existence | screen exists | 23:screen | NOUN |
| f10 | relation.spatial | screen is on phone | 21:displaying, 22:a, 23:screen | VERB, DET, NOUN |
| f11 | object.existence | search bar exists | 33:search, 34:bar | NOUN, NOUN |
| f12 | object.existence | smartphone exists | 14:smartphone | NOUN |
| f13 | object.existence | thumb exists | 62:thumb | NOUN |
| f14 | attribute.state | thumb is visible | 64:visible | ADJ |
| f15 | relation.possession | thumb belongs to person | 61:'s | PART |
| f16 | relation.spatial | thumb is on bottom right side of phone |  |  |
| f17 | subjective.inference | thumb is likely used for navigating screen |  |  |

## 352478_vanilla_greedy

The image features a large display of fresh vegetables, including a variety of broccoli and lettuce, arranged in a market setting. The broccoli is displayed in two separate piles, one on the left side and the other on the right side of the image. The lettuce is also displayed in two piles, one in the middle and the other on the right side.

In addition to the vegetables, there are several potted plants placed throughout the scene, adding a touch of greenery to the display. A bicycle can be seen in the background, possibly belonging to a customer or a vendor. There are also a few people present in the scene, likely browsing the vegetable selection or attending to the market.

| ID | 类型 | 事实 | 核心 token | POS |
|---|---|---|---|---|
| f1 | object.existence | bicycle exists | 97:bicycle | NOUN |
| f2 | relation.spatial | bicycle is in background | 101:in, 103:background | ADP, NOUN |
| f3 | subjective.inference | bicycle possibly belongs to customer or vendor |  |  |
| f4 | object.existence | broccoli exists | 14:broccoli | NOUN |
| f5 | relation.spatial | broccoli pile is on left side of image | 34:on, 36:left, 37:side, 45:of, 47:image | ADP, ADJ, NOUN, ADP, NOUN |
| f6 | relation.spatial | broccoli pile is on right side of image | 41:on, 43:right, 44:side, 45:of, 47:image | ADP, ADJ, NOUN, ADP, NOUN |
| f7 | count.exact | number of broccoli piles is 2 | 29:two | NUM |
| f8 | object.existence | lettuce exists | 16:lettuce | NOUN |
| f9 | relation.spatial | lettuce pile is in middle | 59:in, 61:middle | ADP, NOUN |
| f10 | relation.spatial | lettuce pile is on right side | 65:on, 67:right, 68:side | ADP, ADJ, NOUN |
| f11 | count.exact | number of lettuce piles is 2 | 55:two | NUM |
| f12 | object.existence | people exist | 119:people | NOUN |
| f13 | count.approximate | number of people is a few |  |  |
| f14 | subjective.intention | people are likely browsing vegetable selection or attending to market | 125:likely, 126:browsing, 128:vegetable, 129:selection, 130:or, 131:attending, 132:to, 134:market | ADV, VERB, NOUN, NOUN, CCONJ, VERB, ADP, NOUN |
| f15 | object.existence | potted plants exist | 80:potted, 81:plants | ADJ, NOUN |
| f16 | relation.spatial | potted plants are placed throughout scene | 82:placed, 83:throughout, 85:scene | VERB, ADP, NOUN |
| f17 | count.approximate | number of potted plants is several | 79:several | ADJ |
| f18 | scene.location | scene is market setting | 21:market, 22:setting | NOUN, NOUN |
| f19 | object.existence | vegetables exist | 8:vegetables | NOUN |
| f20 | attribute.state | vegetables are fresh | 7:fresh | ADJ |

## 332570_vista_greedy

A hand holding a cell phone with a keyboard on it.

| ID | 类型 | 事实 | 核心 token | POS |
|---|---|---|---|---|
| f1 | object.existence | cell phone exists | 4:cell, 5:phone | NOUN, NOUN |
| f2 | object.existence | hand exists | 1:hand | NOUN |
| f3 | relation.possession | hand is holding cell phone | 2:holding | VERB |
| f4 | object.existence | keyboard exists | 8:keyboard | NOUN |
| f5 | relation.spatial | keyboard is on cell phone | 9:on | ADP |

## 332570_vanilla_beam5

The image features a close-up view of a person's hand holding a cell phone. The cell phone is prominently displayed in the foreground, occupying a significant portion of the image. On the screen of the cell phone, there is a menu visible, indicating that the person might be using the device for various purposes, such as browsing the internet, texting, or making calls. The hand holding the cell phone appears to be in focus, while the rest of the scene is slightly blurred, creating a sense of depth in the image.

| ID | 类型 | 事实 | 核心 token | POS |
|---|---|---|---|---|
| f1 | object.existence | cell phone exists | 15:cell, 16:phone | NOUN, NOUN |
| f2 | attribute.appearance | cell phone is prominently displayed | 22:prominently, 23:displayed | ADV, VERB |
| f3 | relation.spatial | cell phone is in foreground | 24:in, 26:foreground | ADP, NOUN |
| f4 | relation.spatial | cell phone occupies significant portion of image |  |  |
| f5 | object.existence | hand exists | 12:hand | NOUN |
| f6 | attribute.state | hand appears to be in focus | 81:appears, 82:to, 83:be, 84:in, 85:focus | VERB, PART, AUX, ADP, NOUN |
| f7 | relation.possession | hand belongs to person | 11:'s | PART |
| f8 | relation.possession | hand is holding cell phone | 13:holding | VERB |
| f9 | subjective.aesthetic | image creates a sense of depth | 97:creating, 99:sense, 100:of, 101:depth | VERB, NOUN, ADP, NOUN |
| f10 | object.existence | menu exists | 47:menu | NOUN |
| f11 | attribute.state | menu is visible | 48:visible | ADJ |
| f12 | relation.spatial | menu is on screen | 36:On, 38:screen | ADP, NOUN |
| f13 | object.existence | person exists | 10:person | NOUN |
| f14 | subjective.inference | person might be using device for various purposes, such as browsing internet, texting, or making calls | 54:might, 56:using, 58:device, 59:for, 60:various, 61:purposes, 63:such, 64:as, 65:browsing, 67:internet, 69:texting, 71:or, 72:making, 73:calls | AUX, VERB, NOUN, ADP, ADJ, NOUN, ADJ, ADP, VERB, NOUN, NOUN, CCONJ, VERB, NOUN |
| f15 | attribute.state | rest of scene is slightly blurred | 94:slightly, 95:blurred | ADV, VERB |
| f16 | object.existence | screen exists | 38:screen | NOUN |
| f17 | relation.other | screen is part of cell phone | 39:of | ADP |

## 331883_vista_beam5

The man is sleeping on a mattress on a floor.

| ID | 类型 | 事实 | 核心 token | POS |
|---|---|---|---|---|
| f1 | object.existence | floor exists | 9:floor | NOUN |
| f2 | object.existence | man exists | 1:man | NOUN |
| f3 | action.pose | man is sleeping | 3:sleeping | VERB |
| f4 | relation.spatial | man is on mattress | 4:on | ADP |
| f5 | object.existence | mattress exists | 6:mattress | NOUN |
| f6 | relation.spatial | mattress is on floor | 7:on | ADP |

## 332570_vista_top_p

the palm palm is in the foreground with a hand in the background holding a phone.

| ID | 类型 | 事实 | 核心 token | POS |
|---|---|---|---|---|
| f1 | object.existence | hand exists | 9:hand | NOUN |
| f2 | relation.possession | hand is holding phone | 13:holding | VERB |
| f3 | relation.spatial | hand is in background | 10:in, 12:background | ADP, NOUN |
| f4 | object.existence | palm exists | 1:palm | NOUN |
| f5 | relation.spatial | palm is in foreground | 4:in, 6:foreground | ADP, NOUN |
| f6 | object.existence | phone exists | 15:phone | NOUN |

## 116887_vista_top_p

A tennis player in a white uniform with a yellow tennis racquet in hand prepares to serve the ball.

| ID | 类型 | 事实 | 核心 token | POS |
|---|---|---|---|---|
| f1 | object.existence | ball exists | 18:ball | NOUN |
| f2 | object.existence | hand exists | 13:hand | NOUN |
| f3 | relation.possession | hand is holding tennis racquet | 12:in | ADP |
| f4 | object.existence | tennis player exists | 1:tennis, 2:player | NOUN, NOUN |
| f5 | action.interaction | tennis player is preparing to serve ball | 14:prepares, 15:to, 16:serve | VERB, PART, VERB |
| f6 | object.existence | tennis racquet exists | 10:tennis, 11:racquet | NOUN, NOUN |
| f7 | attribute.color | tennis racquet is yellow | 9:yellow | ADJ |
| f8 | object.existence | uniform exists | 6:uniform | NOUN |
| f9 | attribute.color | uniform is white | 5:white | ADJ |
