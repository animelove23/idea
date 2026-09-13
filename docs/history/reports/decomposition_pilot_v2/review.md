# 真实 API 拆分试运行：逐条抽查

本文件记录原文、事实与语义核心词；不判断图片真实性。

## 332570_vanilla_greedy

The image features a close-up of a person's hand holding a smartphone. The phone is open and displaying a screen with various options, including a menu and a search bar. The hand is positioned in the upper left corner of the image, with the phone occupying the majority of the frame. The person's thumb is visible on the bottom right side of the phone, likely used for navigating the screen.

| ID | 类型 | 事实 | 核心 token | POS |
|---|---|---|---|---|
| f1 | object.existence | hand exists | 11:hand | NOUN |
| f2 | object.existence | smartphone exists | 14:smartphone | NOUN |
| f3 | relation.possession | hand belongs to person | 9:person, 10:'s | NOUN, PART |
| f4 | action.interaction | hand is holding smartphone | 12:holding | VERB |
| f5 | attribute.state | phone is open | 19:open | ADJ |
| f6 | action.other | phone is displaying screen | 21:displaying | VERB |
| f7 | object.existence | screen exists | 23:screen | NOUN |
| f8 | object.existence | menu exists | 30:menu | NOUN |
| f9 | object.existence | search bar exists | 33:search, 34:bar | NOUN, NOUN |
| f10 | relation.spatial | hand is positioned in upper left corner of image | 39:positioned, 40:in, 42:upper, 43:left, 44:corner | VERB, ADP, ADJ, ADJ, NOUN |
| f11 | relation.spatial | phone occupies majority of frame | 52:occupying, 54:majority | VERB, NOUN |
| f12 | object.existence | thumb exists | 62:thumb | NOUN |
| f13 | relation.possession | thumb belongs to person | 60:person, 61:'s | NOUN, PART |
| f14 | attribute.state | thumb is visible | 64:visible | ADJ |
| f15 | relation.spatial | thumb is on bottom right side of phone | 65:on, 67:bottom, 68:right, 69:side | ADP, ADJ, ADJ, NOUN |
| f16 | subjective.inference | thumb is likely used for navigating screen | 74:likely, 75:used, 77:navigating | ADV, VERB, VERB |

## 332570_vista_greedy

A hand holding a cell phone with a keyboard on it.

| ID | 类型 | 事实 | 核心 token | POS |
|---|---|---|---|---|
| f1 | object.existence | hand exists | 1:hand | NOUN |
| f2 | object.existence | cell phone exists | 4:cell, 5:phone | NOUN, NOUN |
| f3 | relation.possession | hand is holding cell phone | 2:holding | VERB |
| f4 | object.existence | keyboard exists | 8:keyboard | NOUN |
| f5 | relation.spatial | keyboard is on cell phone | 9:on | ADP |

## 332570_vanilla_beam5

The image features a close-up view of a person's hand holding a cell phone. The cell phone is prominently displayed in the foreground, occupying a significant portion of the image. On the screen of the cell phone, there is a menu visible, indicating that the person might be using the device for various purposes, such as browsing the internet, texting, or making calls. The hand holding the cell phone appears to be in focus, while the rest of the scene is slightly blurred, creating a sense of depth in the image.

| ID | 类型 | 事实 | 核心 token | POS |
|---|---|---|---|---|
| f1 | object.existence | hand exists | 12:hand | NOUN |
| f2 | object.existence | cell phone exists | 15:cell, 16:phone | NOUN, NOUN |
| f3 | relation.possession | hand is holding cell phone | 13:holding | VERB |
| f4 | attribute.appearance | cell phone is prominently displayed | 22:prominently, 23:displayed | ADV, VERB |
| f5 | relation.spatial | cell phone is in foreground | 26:foreground | NOUN |
| f6 | attribute.size | cell phone occupies significant portion of image | 30:significant, 31:portion | ADJ, NOUN |
| f7 | object.existence | screen exists | 38:screen | NOUN |
| f8 | relation.spatial | screen is on cell phone | 36:On | ADP |
| f9 | object.existence | menu exists | 47:menu | NOUN |
| f10 | attribute.state | menu is visible | 48:visible | ADJ |
| f11 | subjective.inference | person might be using device for various purposes | 54:might, 56:using | AUX, VERB |
| f12 | subjective.inference | person might be browsing internet | 65:browsing, 67:internet | VERB, NOUN |
| f13 | subjective.inference | person might be texting | 69:texting | NOUN |
| f14 | subjective.inference | person might be making calls | 72:making, 73:calls | VERB, NOUN |
| f15 | attribute.state | hand appears to be in focus | 81:appears, 85:focus | VERB, NOUN |
| f16 | attribute.state | rest of scene is slightly blurred | 94:slightly, 95:blurred | ADV, VERB |
| f17 | subjective.aesthetic | image creates sense of depth | 97:creating, 101:depth | VERB, NOUN |

## 332570_vanilla_top_p

The image features a person's hand holding a Palm Treo smartphone up close. The hand is in the foreground, occupying most of the frame, while the phone fills the middle of the scene. On the screen, there is a menu displayed with various options, including a search function. This gives the impression of the smartphone in use, possibly for browsing, searching for information, or making a call.

| ID | 类型 | 事实 | 核心 token | POS |
|---|---|---|---|---|
| f1 | object.existence | hand exists | 6:hand | NOUN |
| f2 | object.existence | Palm Treo smartphone exists | 9:Palm, 10:Treo, 11:smartphone | PROPN, PROPN, VERB |
| f3 | relation.possession | hand belongs to person | 4:person, 5:'s | NOUN, PART |
| f4 | action.interaction | hand is holding Palm Treo smartphone | 7:holding | VERB |
| f5 | attribute.other | hand is up close | 12:up, 13:close | ADP, ADV |
| f6 | relation.spatial | hand is in foreground | 20:foreground | NOUN |
| f7 | relation.spatial | hand occupies most of frame | 22:occupying, 23:most, 26:frame | VERB, ADJ, NOUN |
| f8 | relation.spatial | phone fills middle of scene | 31:fills, 33:middle, 36:scene | VERB, NOUN, NOUN |
| f9 | object.existence | screen exists | 40:screen | NOUN |
| f10 | object.existence | menu exists | 45:menu | NOUN |
| f11 | attribute.state | menu is displayed on screen | 46:displayed | VERB |
| f12 | object.existence | options exist | 49:options | NOUN |
| f13 | object.existence | search function exists | 53:search, 54:function | NOUN, NOUN |
| f14 | relation.other | menu includes search function | 51:including | VERB |
| f15 | subjective.inference | smartphone is in use | 64:use | NOUN |
| f16 | subjective.inference | smartphone is possibly used for browsing | 66:possibly, 68:browsing | ADV, VERB |
| f17 | subjective.inference | smartphone is possibly used for searching for information | 66:possibly, 70:searching, 72:information | ADV, VERB, NOUN |
| f18 | subjective.inference | smartphone is possibly used for making a call | 66:possibly, 75:making, 77:call | ADV, VERB, NOUN |

## 332570_vista_top_p

the palm palm is in the foreground with a hand in the background holding a phone.

| ID | 类型 | 事实 | 核心 token | POS |
|---|---|---|---|---|
| f1 | object.existence | palm exists | 1:palm | NOUN |
| f2 | relation.spatial | palm is in foreground | 4:in, 6:foreground | ADP, NOUN |
| f3 | object.existence | hand exists | 9:hand | NOUN |
| f4 | relation.spatial | hand is in background | 10:in, 12:background | ADP, NOUN |
| f5 | object.existence | phone exists | 15:phone | NOUN |
| f6 | relation.possession | hand is holding phone | 13:holding | VERB |
