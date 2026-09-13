# 30 对：原句、参考与实际对齐

参考为本轮运行前冻结的修订助手标注，部分边界经过用户反馈；并非完整人工审核 gold。所有预测来自本次DeepSeek实际返回及程序校验结果。

## 469134

**Vanilla**

The image depicts a lively scene on a city street, where a group of people is gathered around a row of parked motorcycles. There are at least nine motorcycles visible in the scene, with some parked closer to the foreground and others further back.

The people are standing and interacting with each other, with some of them wearing backpacks. There are at least 13 people in the scene, with some standing closer to the motorcycles and others further away. A pizza shop can be seen in the background, adding to the urban atmosphere.

The street is also equipped with traffic lights, with one on the left side of the scene and another on the right side. The presence of these traffic lights indicates that the area is well-regulated for both pedestrian and vehicular traffic.

**Steer**

The image depicts a busy street scene with a group of motorcycle riders gathered on the sidewalk. There are several motorcycles parked along the street, with some riders wearing jackets and others in leather jackets. People are milling about on the sidewalk, some of them are carrying handbags. The street is bustling with activity, and traffic lights can be seen in the background.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A street is present. | f8: There is a street. | retained | same_fact |
| f2: A group of people is present. | f1: A group of motorcycle riders is present. | ambiguous | partial_overlap |
| f6: Motorcycles are present. | f5: There are motorcycles. | retained | same_fact |
| f7: At least nine motorcycles are present. | ∅ | removed | not_expressed |
| ∅ | f4: Several motorcycles are present. | added | not_expressed |
| f5: The motorcycles are parked. | f6: The motorcycles are parked. | retained | same_fact |
| f4: The motorcycles form a row. | ∅ | removed | not_expressed |
| f8: Some motorcycles are closer to the foreground. | ∅ | removed | not_expressed |
| f9: Other motorcycles are further back. | ∅ | removed | not_expressed |
| f3: The people are gathered around the motorcycles. | f2: The motorcycle riders are gathered on the sidewalk. | ambiguous | partial_overlap |
| f10: The people are standing. | ∅ | removed | not_expressed |
| f11: The people are interacting with each other. | f12: People are milling about on the sidewalk. | ambiguous | partial_overlap |
| f13: Backpacks are present. | ∅ | removed | not_expressed |
| f12: Some people wear backpacks. | ∅ | removed | not_expressed |
| f14: At least 13 people are present. | ∅ | removed | not_expressed |
| f15: Some people stand closer to the motorcycles. | ∅ | removed | not_expressed |
| f16: Other people stand further from the motorcycles. | ∅ | removed | not_expressed |
| f17: A pizza shop is present. | ∅ | removed | not_expressed |
| f18: The pizza shop is in the background. | ∅ | removed | not_expressed |
| f19: Traffic lights are present. | f15: Traffic lights are present. | retained | same_fact |
| f20: One traffic light is on the left. | ∅ | removed | not_expressed |
| f21: Another traffic light is on the right. | ∅ | removed | not_expressed |
| ∅ | f16: The traffic lights are in the background. | added | not_expressed |
| ∅ | f3: There is a sidewalk. | added | not_expressed |
| ∅ | f7: Motorcycles are parked along the street. | added | not_expressed |
| ∅ | f10: Jackets are present. | added | not_expressed |
| ∅ | f9: Some riders wear jackets. | added | not_expressed |
| ∅ | f11: Some jackets are leather. | added | not_expressed |
| ∅ | f14: Handbags are present. | added | not_expressed |
| ∅ | f13: Some people carry handbags. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A street is present. | f8: There is a street. | retained | same_fact |
| f4: The motorcycles form a row. | ∅ | removed | not_expressed |
| f5: The motorcycles are parked. | f6: The motorcycles are parked. | retained | same_fact |
| f6: Motorcycles are present. | f5: There are motorcycles. | retained | same_fact |
| f7: At least nine motorcycles are present. | f4: Several motorcycles are present. | modified | value_changed |
| f8: Some motorcycles are closer to the foreground. | ∅ | removed | not_expressed |
| f9: Other motorcycles are further back. | ∅ | removed | not_expressed |
| f11: The people are interacting with each other. | ∅ | removed | not_expressed |
| f12: Some people wear backpacks. | ∅ | removed | not_expressed |
| f13: Backpacks are present. | ∅ | removed | not_expressed |
| f14: At least 13 people are present. | ∅ | removed | not_expressed |
| f15: Some people stand closer to the motorcycles. | ∅ | removed | not_expressed |
| f16: Other people stand further from the motorcycles. | ∅ | removed | not_expressed |
| f17: A pizza shop is present. | ∅ | removed | not_expressed |
| f18: The pizza shop is in the background. | ∅ | removed | not_expressed |
| f19: Traffic lights are present. | f15: Traffic lights are present. | retained | same_fact |
| f20: One traffic light is on the left. | ∅ | removed | not_expressed |
| f21: Another traffic light is on the right. | ∅ | removed | not_expressed |
| ∅ | f3: There is a sidewalk. | added | not_expressed |
| ∅ | f7: Motorcycles are parked along the street. | added | not_expressed |
| ∅ | f9: Some riders wear jackets. | added | not_expressed |
| ∅ | f10: Jackets are present. | added | not_expressed |
| ∅ | f11: Some jackets are leather. | added | not_expressed |
| ∅ | f13: Some people carry handbags. | added | not_expressed |
| ∅ | f14: Handbags are present. | added | not_expressed |
| ∅ | f16: The traffic lights are in the background. | added | not_expressed |
| f2: A group of people is present.<br>f10: The people are standing. | f1: A group of motorcycle riders is present.<br>f12: People are milling about on the sidewalk. | ambiguous | granularity |
| f3: The people are gathered around the motorcycles. | f2: The motorcycle riders are gathered on the sidewalk. | ambiguous | partial_overlap |

## 341389

**Vanilla**

The image captures a snowy mountain slope with a group of people skiing and snowboarding down the hill. There are at least 13 people visible in the scene, some of them closer to the foreground and others further away. They are all enjoying the winter sports and the beautiful snowy landscape.

In addition to the people, there are two snowboards and a pair of skis visible on the slope. The snowboards are located near the center of the scene, while the skis are positioned closer to the left side. The overall atmosphere of the image is lively and full of excitement as people engage in winter sports on the mountain.

**Steer**

The image depicts a snowy mountainous area with a group of people skiing down a snowy slope. There are at least 12 people skiing down the slope, some of them are wearing skis. The skiers are spread out across the slope, with some skiers positioned near the top of the slope, others are skiing down the slope.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A mountain slope is present. | f3: There is a mountain slope. | retained | same_fact |
| f2: The slope is snowy. | f4: The slope is snowy. | retained | same_fact |
| f3: A group of people is present. | f1: A group of people is present. | retained | same_fact |
| f4: People ski down the slope. | f2: People ski down the slope. | retained | same_fact |
| f5: People snowboard down the slope. | ∅ | removed | not_expressed |
| f6: At least 13 people are visible. | ∅ | removed | not_expressed |
| ∅ | f5: At least 12 people are skiing down the slope. | added | not_expressed |
| f7: Some people are closer to the foreground and others further away. | f8: The skiers are spread across the slope. | ambiguous | partial_overlap |
| f8: Snowboards are present. | ∅ | removed | not_expressed |
| f9: There are two snowboards. | ∅ | removed | not_expressed |
| f10: Skis are present. | f7: Skis are present. | retained | same_fact |
| f11: There is a pair of skis. | ∅ | removed | not_expressed |
| f12: The snowboards are near the scene center. | ∅ | removed | not_expressed |
| f13: The skis are closer to the left. | ∅ | removed | not_expressed |
| ∅ | f6: Some skiers wear skis. | added | not_expressed |
| ∅ | f9: Some skiers are near the top of the slope. | added | not_expressed |

### 实际预测：needs_review

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A mountain slope is present. | f3: There is a mountain slope. | retained | same_fact |
| f2: The slope is snowy. | f4: The slope is snowy. | retained | same_fact |
| f3: A group of people is present. | f1: A group of people is present. | retained | same_fact |
| f4: People ski down the slope. | f2: People ski down the slope. | retained | same_fact |
| f5: People snowboard down the slope. | ∅ | removed | not_expressed |
| f8: Snowboards are present. | ∅ | removed | not_expressed |
| f9: There are two snowboards. | ∅ | removed | not_expressed |
| f11: There is a pair of skis. | ∅ | removed | not_expressed |
| f12: The snowboards are near the scene center. | ∅ | removed | not_expressed |
| f13: The skis are closer to the left. | ∅ | removed | not_expressed |
| ∅ | f6: Some skiers wear skis. | added | not_expressed |
| ∅ | f9: Some skiers are near the top of the slope. | added | not_expressed |
| f6: At least 13 people are visible. | f5: At least 12 people are skiing down the slope. | ambiguous | partial_overlap |
| f7: Some people are closer to the foreground and others further away. | f8: The skiers are spread across the slope. | ambiguous | partial_overlap |
| f10: Skis are present. | f7: Skis are present. | ambiguous | entity_uncertain |

## 214124

**Vanilla**

The image features a close-up view of a delicious pizza with various toppings, including cheese, red peppers, and possibly chicken. The pizza is placed on a dining table, and a glass is visible in the background, likely containing a beverage to accompany the meal. The pizza appears to be a personal-sized pizza, making it a perfect choice for an individual to enjoy.

**Steer**

A pizza with cheese and sausage on top of it.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: There is a pizza. | f1: A pizza is present. | retained | same_fact |
| f4: Cheese is present. | f4: Cheese is present. | retained | same_fact |
| f5: Red peppers are present. | ∅ | removed | not_expressed |
| f6: The peppers are red. | ∅ | removed | not_expressed |
| f7: Chicken may be present. | ∅ | removed | not_expressed |
| f2: Cheese is a pizza topping. | f2: Cheese is on the pizza. | retained | same_fact |
| f3: Red peppers top the pizza. | ∅ | removed | not_expressed |
| f8: Chicken may top the pizza. | ∅ | removed | not_expressed |
| f10: A dining table is present. | ∅ | removed | not_expressed |
| f9: The pizza is on the dining table. | ∅ | removed | not_expressed |
| f11: A glass is present. | ∅ | removed | not_expressed |
| f12: The glass is in the background. | ∅ | removed | not_expressed |
| f13: A beverage is likely present. | ∅ | removed | not_expressed |
| f14: The glass likely contains a beverage. | ∅ | removed | not_expressed |
| f15: The pizza appears personal-sized. | ∅ | removed | not_expressed |
| ∅ | f5: Sausage is present. | added | not_expressed |
| ∅ | f3: Sausage is on the pizza. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: There is a pizza. | f1: A pizza is present. | retained | same_fact |
| f2: Cheese is a pizza topping. | f2: Cheese is on the pizza. | retained | same_fact |
| f3: Red peppers top the pizza. | ∅ | removed | not_expressed |
| f4: Cheese is present. | f4: Cheese is present. | retained | same_fact |
| f5: Red peppers are present. | ∅ | removed | not_expressed |
| f6: The peppers are red. | ∅ | removed | not_expressed |
| f7: Chicken may be present. | ∅ | removed | not_expressed |
| f8: Chicken may top the pizza. | ∅ | removed | not_expressed |
| f9: The pizza is on the dining table. | ∅ | removed | not_expressed |
| f10: A dining table is present. | ∅ | removed | not_expressed |
| f11: A glass is present. | ∅ | removed | not_expressed |
| f12: The glass is in the background. | ∅ | removed | not_expressed |
| f13: A beverage is likely present. | ∅ | removed | not_expressed |
| f14: The glass likely contains a beverage. | ∅ | removed | not_expressed |
| f15: The pizza appears personal-sized. | ∅ | removed | not_expressed |
| ∅ | f3: Sausage is on the pizza. | added | not_expressed |
| ∅ | f5: Sausage is present. | added | not_expressed |

## 4157

**Vanilla**

The image features a clock hanging on the wall, with a unique design that includes three chocolate-covered raisins attached to it. The clock is positioned above a shelf, and the raisins are placed at different heights, adding a playful touch to the scene.

In addition to the clock, there are several bottles scattered around the area, with some placed on the shelf and others on the floor. The bottles come in various sizes and shapes, creating a diverse collection of items in the scene.

**Steer**

The clock is black and white, and it hangs on a wall. It has a yellow bow and two black balls hanging from it. The clock is positioned above a collection of glasses and bottles.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A clock is present. | f1: A clock is present. | retained | same_fact |
| f3: A wall is present. | f4: A wall is present. | retained | same_fact |
| f2: The clock hangs on the wall. | f3: The clock hangs on a wall. | retained | same_fact |
| f7: Raisins are present. | f11: Balls are present. | ambiguous | entity_uncertain |
| f4: There are three raisins. | f8: There are two balls. | ambiguous | entity_uncertain |
| f6: The raisins are chocolate-covered. | ∅ | removed | not_expressed |
| f5: The raisins are attached to the clock. | f9: The balls hang from the clock. | ambiguous | entity_uncertain |
| f9: A shelf is present. | ∅ | removed | not_expressed |
| f8: The clock is above the shelf. | ∅ | removed | not_expressed |
| f10: The raisins are at different heights. | ∅ | removed | not_expressed |
| f12: Bottles are present. | f14: Bottles are present. | retained | same_fact |
| f11: There are several bottles. | ∅ | removed | not_expressed |
| f13: Some bottles are on the shelf. | ∅ | removed | not_expressed |
| f15: A floor is present. | ∅ | removed | not_expressed |
| f14: Other bottles are on the floor. | ∅ | removed | not_expressed |
| f16: The bottles have various sizes. | ∅ | removed | not_expressed |
| f17: The bottles have various shapes. | ∅ | removed | not_expressed |
| ∅ | f2: The clock is black and white. | added | not_expressed |
| ∅ | f6: A bow is present. | added | not_expressed |
| ∅ | f7: The bow is yellow. | added | not_expressed |
| ∅ | f5: The clock has a bow. | added | not_expressed |
| ∅ | f10: The balls are black. | added | not_expressed |
| ∅ | f13: Glasses are present. | added | not_expressed |
| ∅ | f12: The clock is above the glasses and bottles. | added | not_expressed |

### 实际预测：needs_review

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A clock is present. | f1: A clock is present. | retained | same_fact |
| f2: The clock hangs on the wall. | f3: The clock hangs on a wall. | retained | same_fact |
| f3: A wall is present. | f4: A wall is present. | retained | same_fact |
| f6: The raisins are chocolate-covered. | ∅ | removed | not_expressed |
| f10: The raisins are at different heights. | ∅ | removed | not_expressed |
| f11: There are several bottles. | ∅ | removed | not_expressed |
| f13: Some bottles are on the shelf. | ∅ | removed | not_expressed |
| f14: Other bottles are on the floor. | ∅ | removed | not_expressed |
| f15: A floor is present. | ∅ | removed | not_expressed |
| f16: The bottles have various sizes. | ∅ | removed | not_expressed |
| f17: The bottles have various shapes. | ∅ | removed | not_expressed |
| ∅ | f2: The clock is black and white. | added | not_expressed |
| ∅ | f5: The clock has a bow. | added | not_expressed |
| ∅ | f6: A bow is present. | added | not_expressed |
| ∅ | f7: The bow is yellow. | added | not_expressed |
| ∅ | f10: The balls are black. | added | not_expressed |
| f4: There are three raisins. | f8: There are two balls. | ambiguous | entity_uncertain |
| f5: The raisins are attached to the clock. | f9: The balls hang from the clock. | ambiguous | entity_uncertain |
| f7: Raisins are present. | f11: Balls are present. | ambiguous | entity_uncertain |
| f8: The clock is above the shelf. | f12: The clock is above the glasses and bottles. | ambiguous | partial_overlap |
| f9: A shelf is present. | ∅ | ambiguous | entity_uncertain |
| f12: Bottles are present. | f14: Bottles are present. | ambiguous | entity_uncertain |
| ∅ | f13: Glasses are present. | ambiguous | entity_uncertain |

## 264423

**Vanilla**

The image features two people, a woman and a child, standing outside and flying a kite together. The kite is soaring high in the sky, with its string visible between the two individuals. The woman is wearing a black jacket, and the child is standing close to her, both enjoying the outdoor activity. The scene captures a moment of bonding and shared enjoyment between the two people.

**Steer**

Two people are standing outside on a sunny day. One person is wearing glasses, and both individuals are watching a kite flying high in the sky. The kite is flying above them, and they are enjoying the outdoor activity.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: People are present. | f1: People are present. | retained | same_fact |
| f2: There are two people. | f2: There are two people. | retained | same_fact |
| f3: There is a woman. | ∅ | removed | not_expressed |
| ∅ | f6: One person wears glasses. | added | not_expressed |
| f4: There is a child. | ∅ | removed | not_expressed |
| f5: Both people are standing. | f3: Both people are standing. | retained | same_fact |
| f6: The people are outside. | f4: The people are outside. | retained | same_fact |
| f7: The people fly a kite together. | ∅ | removed | not_expressed |
| f8: A kite is present. | f9: There is a kite. | retained | same_fact |
| f9: The kite is high in the sky. | f10: The kite flies high in the sky. | retained | same_fact |
| f10: The kite has a string. | ∅ | removed | not_expressed |
| f11: The string is between the two people. | ∅ | removed | not_expressed |
| f13: A jacket is present. | ∅ | removed | not_expressed |
| f14: The jacket is black. | ∅ | removed | not_expressed |
| f12: The woman wears a jacket. | ∅ | removed | not_expressed |
| f15: The child stands close to the woman. | ∅ | removed | not_expressed |
| ∅ | f5: The day is sunny. | added | not_expressed |
| ∅ | f7: Glasses are present. | added | not_expressed |
| ∅ | f8: Both people watch the kite. | added | not_expressed |
| ∅ | f11: The kite is above the people. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: People are present. | f1: People are present. | retained | same_fact |
| f2: There are two people. | f2: There are two people. | retained | same_fact |
| f5: Both people are standing. | f3: Both people are standing. | retained | same_fact |
| f6: The people are outside. | f4: The people are outside. | retained | same_fact |
| f8: A kite is present. | f9: There is a kite. | retained | same_fact |
| f9: The kite is high in the sky. | f10: The kite flies high in the sky. | retained | same_fact |
| f10: The kite has a string. | ∅ | removed | not_expressed |
| f11: The string is between the two people. | ∅ | removed | not_expressed |
| f12: The woman wears a jacket. | ∅ | removed | not_expressed |
| f13: A jacket is present. | ∅ | removed | not_expressed |
| f14: The jacket is black. | ∅ | removed | not_expressed |
| f15: The child stands close to the woman. | ∅ | removed | not_expressed |
| ∅ | f5: The day is sunny. | added | not_expressed |
| ∅ | f6: One person wears glasses. | added | not_expressed |
| ∅ | f7: Glasses are present. | added | not_expressed |
| ∅ | f11: The kite is above the people. | added | not_expressed |
| f3: There is a woman.<br>f4: There is a child. | ∅ | ambiguous | entity_uncertain |
| f7: The people fly a kite together. | f8: Both people watch the kite. | ambiguous | partial_overlap |

## 537857

**Vanilla**

The image features a young girl wearing a yellow hat and a red and white dress, standing in a grassy field. She is holding a kite in her hand, possibly preparing to fly it. The girl appears to be enjoying her time outdoors, possibly at a park or a similar location.

In the background, there are a few other people, possibly enjoying the outdoor activities as well. Additionally, there are two kites visible in the scene, one near the girl and another further away.

**Steer**

The girl is wearing a yellow hat and a pink vest. She is holding a kite in her hand.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A girl is present. | f1: There is a girl. | retained | same_fact |
| f2: The girl is young. | ∅ | removed | not_expressed |
| f5: A hat is present. | f4: A hat is present. | retained | same_fact |
| f6: The hat is yellow. | f5: The hat is yellow. | retained | same_fact |
| f3: The girl wears a hat. | f2: The girl wears a hat. | retained | same_fact |
| f7: A dress is present. | ∅ | removed | not_expressed |
| f8: The dress is red and white. | ∅ | removed | not_expressed |
| f4: The girl wears a dress. | ∅ | removed | not_expressed |
| f10: A field is present. | ∅ | removed | not_expressed |
| f11: The field is grassy. | ∅ | removed | not_expressed |
| f9: The girl stands in the field. | ∅ | removed | not_expressed |
| f13: A kite is present. | f9: There is a kite. | retained | same_fact |
| f14: The girl's hand is present. | f10: The girl's hand is present. | retained | same_fact |
| f12: The girl holds a kite in her hand. | f8: The girl holds a kite in her hand. | retained | same_fact |
| f15: The girl may be preparing to fly the kite. | ∅ | removed | not_expressed |
| f18: Other people are present. | ∅ | removed | not_expressed |
| f17: There are a few other people. | ∅ | removed | not_expressed |
| f16: Other people are in the background. | ∅ | removed | not_expressed |
| f19: There are two kites. | ∅ | removed | not_expressed |
| ∅ | f3: The girl wears a vest. | added | not_expressed |
| f20: Another kite is further away. | ∅ | removed | not_expressed |
| ∅ | f6: A vest is present. | added | not_expressed |
| ∅ | f7: The vest is pink. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A girl is present. | f1: There is a girl. | retained | same_fact |
| f2: The girl is young. | ∅ | removed | not_expressed |
| f3: The girl wears a hat. | f2: The girl wears a hat. | retained | same_fact |
| f4: The girl wears a dress. | ∅ | removed | not_expressed |
| f5: A hat is present. | f4: A hat is present. | retained | same_fact |
| f6: The hat is yellow. | f5: The hat is yellow. | retained | same_fact |
| f7: A dress is present. | ∅ | removed | not_expressed |
| f8: The dress is red and white. | ∅ | removed | not_expressed |
| f9: The girl stands in the field. | ∅ | removed | not_expressed |
| f10: A field is present. | ∅ | removed | not_expressed |
| f11: The field is grassy. | ∅ | removed | not_expressed |
| f12: The girl holds a kite in her hand. | f8: The girl holds a kite in her hand. | retained | same_fact |
| f13: A kite is present. | f9: There is a kite. | retained | same_fact |
| f14: The girl's hand is present. | f10: The girl's hand is present. | retained | same_fact |
| f15: The girl may be preparing to fly the kite. | ∅ | removed | not_expressed |
| f16: Other people are in the background. | ∅ | removed | not_expressed |
| f17: There are a few other people. | ∅ | removed | not_expressed |
| f18: Other people are present. | ∅ | removed | not_expressed |
| f19: There are two kites. | ∅ | removed | not_expressed |
| f20: Another kite is further away. | ∅ | removed | not_expressed |
| ∅ | f3: The girl wears a vest. | added | not_expressed |
| ∅ | f6: A vest is present. | added | not_expressed |
| ∅ | f7: The vest is pink. | added | not_expressed |

## 46912

**Vanilla**

The image features a train station with a train on the tracks. The train is positioned on the left side of the scene, occupying a significant portion of the image. There are several people in the scene, with some standing near the train and others scattered around the station.

In addition to the train, there are two cars visible in the background, one on the left side and another on the right side of the image. The presence of people and cars suggests that this is a busy train station, with passengers and vehicles coming and going.

**Steer**

The image depicts a train traveling through a tunnel. The train is black and occupies most of the scene. There are several people in the train, some of them are near the front of the train, while others are scattered throughout the train. The train is on tracks, and it appears to be in motion.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A train station is present. | ∅ | removed | not_expressed |
| f2: A train is present. | f1: There is a train. | retained | same_fact |
| f4: Tracks are present. | f12: Tracks are present. | retained | same_fact |
| f3: The train is on the tracks. | f11: The train is on tracks. | retained | same_fact |
| f5: The train is on the left. | ∅ | removed | not_expressed |
| f6: The train occupies a significant portion of the image. | f5: The train occupies most of the scene. | ambiguous | partial_overlap |
| f8: People are present. | f7: There are people. | retained | same_fact |
| f7: There are several people. | f6: There are several people. | retained | same_fact |
| f9: Some people stand near the train. | ∅ | removed | not_expressed |
| f10: Other people are scattered around the station. | ∅ | removed | not_expressed |
| f13: Cars are present. | ∅ | removed | not_expressed |
| f11: There are two cars. | ∅ | removed | not_expressed |
| f12: The cars are in the background. | ∅ | removed | not_expressed |
| f14: One car is on the left and another on the right. | ∅ | removed | not_expressed |
| ∅ | f3: A tunnel is present. | added | not_expressed |
| ∅ | f2: The train travels through a tunnel. | added | not_expressed |
| ∅ | f4: The train is black. | added | not_expressed |
| ∅ | f8: People are in the train. | added | not_expressed |
| ∅ | f9: Some people are near the train's front. | added | not_expressed |
| ∅ | f10: Other people are scattered throughout the train. | added | not_expressed |
| ∅ | f13: The train appears in motion. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A train station is present. | ∅ | removed | not_expressed |
| f2: A train is present. | f1: There is a train. | retained | same_fact |
| f3: The train is on the tracks. | f11: The train is on tracks. | retained | same_fact |
| f4: Tracks are present. | f12: Tracks are present. | retained | same_fact |
| f5: The train is on the left. | ∅ | removed | not_expressed |
| f6: The train occupies a significant portion of the image. | f5: The train occupies most of the scene. | modified | value_changed |
| f7: There are several people. | f6: There are several people. | retained | same_fact |
| f8: People are present. | f7: There are people. | retained | same_fact |
| f11: There are two cars. | ∅ | removed | not_expressed |
| f12: The cars are in the background. | ∅ | removed | not_expressed |
| f13: Cars are present. | ∅ | removed | not_expressed |
| f14: One car is on the left and another on the right. | ∅ | removed | not_expressed |
| ∅ | f2: The train travels through a tunnel. | added | not_expressed |
| ∅ | f3: A tunnel is present. | added | not_expressed |
| ∅ | f4: The train is black. | added | not_expressed |
| ∅ | f8: People are in the train. | added | not_expressed |
| ∅ | f13: The train appears in motion. | added | not_expressed |
| f9: Some people stand near the train. | f9: Some people are near the train's front. | ambiguous | partial_overlap |
| f10: Other people are scattered around the station. | f10: Other people are scattered throughout the train. | ambiguous | partial_overlap |

## 378276

**Vanilla**

The image depicts a busy commercial kitchen with several chefs working together to prepare food. There are five people in the kitchen, with one chef standing near the left side, another in the middle, and three more on the right side. They are all focused on their tasks, with some of them wearing aprons.

The kitchen is well-equipped with various utensils and appliances. There are multiple knives, spoons, and bowls scattered throughout the scene. A refrigerator is visible on the right side of the kitchen, and an oven can be seen in the middle. A sink is also present on the left side of the kitchen.

The chefs are working in a professional environment, likely in a restaurant or a catering facility, as they prepare meals for their customers.

**Steer**

The image depicts a group of chefs working together in a kitchen. They are all wearing white uniforms and are busy preparing food. There are several bowls and utensils like knives and spoons scattered around the kitchen. The chefs are in various positions, some are closer to the camera while others are further away.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A kitchen is present. | f4: There is a kitchen. | retained | same_fact |
| f2: The kitchen is commercial. | ∅ | removed | not_expressed |
| f3: Chefs are present. | f1: Chefs are present. | retained | same_fact |
| f4: The chefs work together. | f2: The chefs work together. | retained | same_fact |
| f6: Food is present. | f9: Food is present. | retained | same_fact |
| f5: The chefs prepare food. | f8: The chefs prepare food. | retained | same_fact |
| f7: The chefs are in the kitchen. | f3: The chefs are in a kitchen. | retained | same_fact |
| f8: There are five people in the kitchen. | ∅ | removed | not_expressed |
| f9: One chef stands on the left. | ∅ | removed | not_expressed |
| f10: Another chef is in the middle. | ∅ | removed | not_expressed |
| f11: Three chefs are on the right. | ∅ | removed | not_expressed |
| f13: Aprons are present. | ∅ | removed | not_expressed |
| f12: Some chefs wear aprons. | ∅ | removed | not_expressed |
| f16: Knives are present. | f13: Knives are present. | retained | same_fact |
| f17: Spoons are present. | f14: Spoons are present. | retained | same_fact |
| f18: Bowls are present. | f11: Bowls are present. | retained | same_fact |
| f14: Multiple bowls are present. | f10: Several bowls are present. | ambiguous | partial_overlap |
| f15: The utensils and bowls are scattered through the kitchen. | f12: The utensils and bowls are scattered around the kitchen. | retained | same_fact |
| f19: A refrigerator is present. | ∅ | removed | not_expressed |
| f20: The refrigerator is on the right. | ∅ | removed | not_expressed |
| f21: An oven is present. | ∅ | removed | not_expressed |
| f22: The oven is in the middle. | ∅ | removed | not_expressed |
| f23: A sink is present. | ∅ | removed | not_expressed |
| f24: The sink is on the left. | ∅ | removed | not_expressed |
| ∅ | f6: Uniforms are present. | added | not_expressed |
| ∅ | f7: The uniforms are white. | added | not_expressed |
| ∅ | f5: All chefs wear uniforms. | added | not_expressed |
| ∅ | f15: Some chefs are closer to the camera and others further away. | added | not_expressed |

### 实际预测：needs_review

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A kitchen is present. | f4: There is a kitchen. | retained | same_fact |
| f2: The kitchen is commercial. | ∅ | removed | not_expressed |
| f6: Food is present. | f9: Food is present. | retained | same_fact |
| f8: There are five people in the kitchen. | ∅ | removed | not_expressed |
| f14: Multiple bowls are present. | f10: Several bowls are present. | modified | value_changed |
| f15: The utensils and bowls are scattered through the kitchen. | f12: The utensils and bowls are scattered around the kitchen. | retained | same_fact |
| f16: Knives are present. | f13: Knives are present. | retained | same_fact |
| f17: Spoons are present. | f14: Spoons are present. | retained | same_fact |
| f18: Bowls are present. | f11: Bowls are present. | retained | same_fact |
| f19: A refrigerator is present. | ∅ | removed | not_expressed |
| f20: The refrigerator is on the right. | ∅ | removed | not_expressed |
| f21: An oven is present. | ∅ | removed | not_expressed |
| f22: The oven is in the middle. | ∅ | removed | not_expressed |
| f23: A sink is present. | ∅ | removed | not_expressed |
| f24: The sink is on the left. | ∅ | removed | not_expressed |
| ∅ | f7: The uniforms are white. | added | not_expressed |
| f3: Chefs are present. | f1: Chefs are present. | ambiguous | entity_uncertain |
| f4: The chefs work together. | f2: The chefs work together. | ambiguous | entity_uncertain |
| f5: The chefs prepare food. | f8: The chefs prepare food. | ambiguous | entity_uncertain |
| f7: The chefs are in the kitchen. | f3: The chefs are in a kitchen. | ambiguous | entity_uncertain |
| f9: One chef stands on the left.<br>f10: Another chef is in the middle.<br>f11: Three chefs are on the right. | f15: Some chefs are closer to the camera and others further away. | ambiguous | granularity |
| f12: Some chefs wear aprons. | f5: All chefs wear uniforms. | ambiguous | partial_overlap |
| f13: Aprons are present. | f6: Uniforms are present. | ambiguous | partial_overlap |

## 559550

**Vanilla**

The image features a dining table with two children sitting at it. One child is sitting in a high chair, while the other is sitting at a regular table. Both children are eating, with one child holding a spoon and the other holding a fork.

There are several bowls on the table, with one near the high chair and another near the regular table. A cup is also present on the table, placed closer to the regular table. The scene appears to be a casual dining setting, with the children enjoying their meal.

**Steer**

The image features two children at a restaurant. One child is seated at a table with a plate of food, while the other child is in a play area. Both children are eating food at their respective tables.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f4: Children are present. | f3: Children are present. | retained | same_fact |
| f2: There are two children. | f1: There are two children. | retained | same_fact |
| f1: A dining table is present. | f12: Tables are present. | ambiguous | partial_overlap |
| f7: Both children are eating. | f11: Both children eat food. | retained | same_fact |
| f3: Two children are sitting at the dining table. | f5: One child is seated at a table. | ambiguous | partial_overlap |
| f6: A high chair is present. | ∅ | removed | not_expressed |
| f5: One child sits in a high chair. | ∅ | removed | not_expressed |
| f9: A spoon is present. | ∅ | removed | not_expressed |
| f8: One child holds a spoon. | ∅ | removed | not_expressed |
| f11: A fork is present. | ∅ | removed | not_expressed |
| f10: The other child holds a fork. | ∅ | removed | not_expressed |
| f14: Bowls are present. | ∅ | removed | not_expressed |
| f12: Several bowls are present. | ∅ | removed | not_expressed |
| f13: The bowls are on the table. | ∅ | removed | not_expressed |
| f15: One bowl is near the high chair. | ∅ | removed | not_expressed |
| f16: Another bowl is near the regular table. | ∅ | removed | not_expressed |
| f17: A cup is present. | ∅ | removed | not_expressed |
| f18: The cup is on the table. | ∅ | removed | not_expressed |
| f19: The cup is closer to the regular table. | ∅ | removed | not_expressed |
| ∅ | f4: A restaurant is present. | added | not_expressed |
| ∅ | f2: The children are at a restaurant. | added | not_expressed |
| ∅ | f6: A plate is present. | added | not_expressed |
| ∅ | f8: Food is present. | added | not_expressed |
| ∅ | f7: Food is on a plate. | added | not_expressed |
| ∅ | f10: A play area is present. | added | not_expressed |
| ∅ | f9: One child is in the play area. | added | not_expressed |

### 实际预测：needs_review

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f2: There are two children. | f1: There are two children. | retained | same_fact |
| f3: Two children are sitting at the dining table. | ∅ | removed | not_expressed |
| f4: Children are present. | f3: Children are present. | retained | same_fact |
| f5: One child sits in a high chair. | ∅ | removed | not_expressed |
| f6: A high chair is present. | ∅ | removed | not_expressed |
| f8: One child holds a spoon. | ∅ | removed | not_expressed |
| f9: A spoon is present. | ∅ | removed | not_expressed |
| f10: The other child holds a fork. | ∅ | removed | not_expressed |
| f11: A fork is present. | ∅ | removed | not_expressed |
| f12: Several bowls are present. | ∅ | removed | not_expressed |
| f13: The bowls are on the table. | ∅ | removed | not_expressed |
| f14: Bowls are present. | ∅ | removed | not_expressed |
| f15: One bowl is near the high chair. | ∅ | removed | not_expressed |
| f16: Another bowl is near the regular table. | ∅ | removed | not_expressed |
| f17: A cup is present. | ∅ | removed | not_expressed |
| f18: The cup is on the table. | ∅ | removed | not_expressed |
| f19: The cup is closer to the regular table. | ∅ | removed | not_expressed |
| ∅ | f2: The children are at a restaurant. | added | not_expressed |
| ∅ | f4: A restaurant is present. | added | not_expressed |
| ∅ | f5: One child is seated at a table. | added | not_expressed |
| ∅ | f6: A plate is present. | added | not_expressed |
| ∅ | f7: Food is on a plate. | added | not_expressed |
| ∅ | f8: Food is present. | added | not_expressed |
| ∅ | f9: One child is in the play area. | added | not_expressed |
| ∅ | f10: A play area is present. | added | not_expressed |
| ∅ | f12: Tables are present. | added | not_expressed |
| f1: A dining table is present. | ∅ | ambiguous | entity_uncertain |
| f7: Both children are eating. | f11: Both children eat food. | ambiguous | partial_overlap |

## 87144

**Vanilla**

The image features a family sitting on a park bench, consisting of a woman, a child, and an older man. The woman is sitting on the left side of the bench, while the child is sitting in the middle, and the older man is on the right side. They appear to be enjoying their time together in the park.

In the background, there are two cars parked, one on the left side and the other on the right side of the scene. Additionally, there is a handbag placed on the ground near the woman, possibly belonging to her.

**Steer**

The image depicts a family spending time together outdoors. They are seated on a bench with a little girl and a woman. The little girl is wearing a pink dress and is seated next to a woman who is wearing a blue dress. They all seem to be enjoying their time together.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A family is present. | f1: A family is present. | retained | same_fact |
| f3: A bench is present. | f3: A bench is present. | retained | same_fact |
| f2: The family sits on the bench. | f2: The family is seated on a bench. | retained | same_fact |
| f4: A woman is present. | f5: A woman is present. | retained | same_fact |
| f5: A child is present. | f4: A little girl is present. | ambiguous | partial_overlap |
| f6: An older man is present. | ∅ | removed | not_expressed |
| f7: The man is older. | ∅ | removed | not_expressed |
| f8: The woman sits on the left side of the bench. | ∅ | removed | not_expressed |
| f9: The child sits in the middle. | ∅ | removed | not_expressed |
| f10: The older man is on the right. | ∅ | removed | not_expressed |
| f14: Cars are present. | ∅ | removed | not_expressed |
| f12: There are two cars. | ∅ | removed | not_expressed |
| f13: The cars are parked. | ∅ | removed | not_expressed |
| f11: The cars are in the background. | ∅ | removed | not_expressed |
| f15: One car is on the left and another on the right. | ∅ | removed | not_expressed |
| f16: A handbag is present. | ∅ | removed | not_expressed |
| f18: The ground is present. | ∅ | removed | not_expressed |
| f17: The handbag is on the ground. | ∅ | removed | not_expressed |
| f19: The handbag is near the woman. | ∅ | removed | not_expressed |
| f20: The handbag may belong to the woman. | ∅ | removed | not_expressed |
| ∅ | f7: A dress worn by the girl is present. | added | not_expressed |
| ∅ | f8: The girl's dress is pink. | added | not_expressed |
| ∅ | f6: The girl wears a dress. | added | not_expressed |
| ∅ | f11: A dress worn by the woman is present. | added | not_expressed |
| ∅ | f12: The woman's dress is blue. | added | not_expressed |
| ∅ | f10: The woman wears a dress. | added | not_expressed |
| ∅ | f9: The little girl sits next to the woman. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A family is present. | f1: A family is present. | retained | same_fact |
| f2: The family sits on the bench. | f2: The family is seated on a bench. | retained | same_fact |
| f3: A bench is present. | f3: A bench is present. | retained | same_fact |
| f4: A woman is present. | f5: A woman is present. | retained | same_fact |
| f5: A child is present. | f4: A little girl is present. | retained | same_fact |
| f6: An older man is present. | ∅ | removed | not_expressed |
| f7: The man is older. | ∅ | removed | not_expressed |
| f8: The woman sits on the left side of the bench. | ∅ | removed | not_expressed |
| f9: The child sits in the middle. | ∅ | removed | not_expressed |
| f10: The older man is on the right. | ∅ | removed | not_expressed |
| f11: The cars are in the background. | ∅ | removed | not_expressed |
| f12: There are two cars. | ∅ | removed | not_expressed |
| f13: The cars are parked. | ∅ | removed | not_expressed |
| f14: Cars are present. | ∅ | removed | not_expressed |
| f15: One car is on the left and another on the right. | ∅ | removed | not_expressed |
| f16: A handbag is present. | ∅ | removed | not_expressed |
| f17: The handbag is on the ground. | ∅ | removed | not_expressed |
| f18: The ground is present. | ∅ | removed | not_expressed |
| f19: The handbag is near the woman. | ∅ | removed | not_expressed |
| f20: The handbag may belong to the woman. | ∅ | removed | not_expressed |
| ∅ | f6: The girl wears a dress. | added | not_expressed |
| ∅ | f7: A dress worn by the girl is present. | added | not_expressed |
| ∅ | f8: The girl's dress is pink. | added | not_expressed |
| ∅ | f9: The little girl sits next to the woman. | added | not_expressed |
| ∅ | f10: The woman wears a dress. | added | not_expressed |
| ∅ | f11: A dress worn by the woman is present. | added | not_expressed |
| ∅ | f12: The woman's dress is blue. | added | not_expressed |

## 288955

**Vanilla**

The image features a small black and brown dog standing on a wooden floor, looking at a plate of food placed on the floor. The dog appears to be curious about the food, possibly waiting for someone to serve it. The plate contains broccoli, which is a common food for dogs.

In the background, there is a chair and a dining table, suggesting that the scene takes place in a dining area. A bowl can also be seen on the floor, possibly containing more food for the dog.

**Steer**

A dog is eating food off a plate on a floor.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A dog is present. | f1: A dog is present. | retained | same_fact |
| f2: The dog is small. | ∅ | removed | not_expressed |
| f3: The dog is black and brown. | ∅ | removed | not_expressed |
| f5: A floor is present. | f7: A floor is present. | retained | same_fact |
| f6: The floor is wooden. | ∅ | removed | not_expressed |
| f4: The dog is standing. | ∅ | removed | not_expressed |
| f8: A plate is present. | f5: A plate is present. | retained | same_fact |
| f11: Food is present. | f3: Food is present. | retained | same_fact |
| f9: The plate is on the floor. | f6: The plate is on a floor. | retained | same_fact |
| f10: Food is on the plate. | f4: Food is on a plate. | retained | same_fact |
| f7: The dog looks at the plate of food. | ∅ | removed | not_expressed |
| ∅ | f2: The dog eats food from the plate. | added | not_expressed |
| f12: The dog may be waiting for someone to serve it. | ∅ | removed | not_expressed |
| f14: Broccoli is present. | ∅ | removed | not_expressed |
| f13: The plate contains broccoli. | ∅ | removed | not_expressed |
| f16: A chair is present. | ∅ | removed | not_expressed |
| f17: A dining table is present. | ∅ | removed | not_expressed |
| f15: The chair and table are in the background. | ∅ | removed | not_expressed |
| f18: A bowl is present. | ∅ | removed | not_expressed |
| f19: The bowl is on the floor. | ∅ | removed | not_expressed |
| f20: The bowl may contain more food for the dog. | ∅ | removed | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A dog is present. | f1: A dog is present. | retained | same_fact |
| f2: The dog is small. | ∅ | removed | not_expressed |
| f3: The dog is black and brown. | ∅ | removed | not_expressed |
| f4: The dog is standing. | ∅ | removed | not_expressed |
| f5: A floor is present. | f7: A floor is present. | retained | same_fact |
| f6: The floor is wooden. | ∅ | removed | not_expressed |
| f8: A plate is present. | f5: A plate is present. | retained | same_fact |
| f9: The plate is on the floor. | f6: The plate is on a floor. | retained | same_fact |
| f10: Food is on the plate. | f4: Food is on a plate. | retained | same_fact |
| f11: Food is present. | f3: Food is present. | retained | same_fact |
| f12: The dog may be waiting for someone to serve it. | ∅ | removed | not_expressed |
| f13: The plate contains broccoli. | ∅ | removed | not_expressed |
| f14: Broccoli is present. | ∅ | removed | not_expressed |
| f15: The chair and table are in the background. | ∅ | removed | not_expressed |
| f16: A chair is present. | ∅ | removed | not_expressed |
| f17: A dining table is present. | ∅ | removed | not_expressed |
| f18: A bowl is present. | ∅ | removed | not_expressed |
| f19: The bowl is on the floor. | ∅ | removed | not_expressed |
| f20: The bowl may contain more food for the dog. | ∅ | removed | not_expressed |
| f7: The dog looks at the plate of food. | f2: The dog eats food from the plate. | ambiguous | partial_overlap |

## 475150

**Vanilla**

The image features a giraffe standing in a wooded area with trees surrounding it. The giraffe is looking to the side, possibly observing its surroundings or searching for food. The giraffe's long neck and legs are clearly visible, making it the main focus of the scene. The trees in the background provide a natural habitat for the giraffe, creating a serene and peaceful atmosphere.

**Steer**

The giraffe is standing in a wooded area with trees and branches. It is a sunny day, and the giraffe is looking at something in the distance. The giraffe's long neck and head are prominent in the scene.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A giraffe is present. | f1: A giraffe is present. | retained | same_fact |
| f2: The giraffe is standing. | f2: The giraffe is standing. | retained | same_fact |
| f4: A wooded area is present. | f4: A wooded area is present. | retained | same_fact |
| f3: The giraffe is in the wooded area. | f3: The giraffe is in a wooded area. | retained | same_fact |
| f5: Trees are present. | f5: Trees are present. | retained | same_fact |
| f6: Trees surround the giraffe. | ∅ | removed | not_expressed |
| f7: The giraffe looks to the side. | f8: The giraffe looks at something in the distance. | ambiguous | partial_overlap |
| f8: The giraffe may be observing its surroundings or searching for food. | ∅ | removed | not_expressed |
| f9: The giraffe's neck is visible. | f9: The giraffe's neck is visible. | retained | same_fact |
| f10: The giraffe's neck is long. | f10: The giraffe's neck is long. | retained | same_fact |
| f11: The giraffe's legs are visible. | ∅ | removed | not_expressed |
| f12: Trees are in the background. | ∅ | removed | not_expressed |
| ∅ | f6: Branches are present. | added | not_expressed |
| ∅ | f7: It is sunny. | added | not_expressed |
| ∅ | f11: The giraffe's head is prominent. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A giraffe is present. | f1: A giraffe is present. | retained | same_fact |
| f2: The giraffe is standing. | f2: The giraffe is standing. | retained | same_fact |
| f3: The giraffe is in the wooded area. | f3: The giraffe is in a wooded area. | retained | same_fact |
| f4: A wooded area is present. | f4: A wooded area is present. | retained | same_fact |
| f5: Trees are present. | f5: Trees are present. | retained | same_fact |
| f6: Trees surround the giraffe. | ∅ | removed | not_expressed |
| f8: The giraffe may be observing its surroundings or searching for food. | ∅ | removed | not_expressed |
| f9: The giraffe's neck is visible. | f9: The giraffe's neck is visible. | retained | same_fact |
| f10: The giraffe's neck is long. | f10: The giraffe's neck is long. | retained | same_fact |
| f11: The giraffe's legs are visible. | ∅ | removed | not_expressed |
| f12: Trees are in the background. | ∅ | removed | not_expressed |
| ∅ | f6: Branches are present. | added | not_expressed |
| ∅ | f7: It is sunny. | added | not_expressed |
| ∅ | f11: The giraffe's head is prominent. | added | not_expressed |
| f7: The giraffe looks to the side. | f8: The giraffe looks at something in the distance. | ambiguous | partial_overlap |

## 239005

**Vanilla**

The image features a white plate with a bowl filled with a delicious meal of broccoli and carrots. The bowl is placed on the plate, and the broccoli and carrots are arranged in a visually appealing manner. The dish appears to be a healthy and nutritious meal, with the vegetables being the main focus.

**Steer**

The image depicts a white plate with a bowl full of broccoli and other vegetables. The broccoli is in various sizes and is spread across the plate. There are also several carrots and a few other vegetables on the plate. The dining table is red, and there is a book on the table.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A plate is present. | f1: A plate is present. | retained | same_fact |
| f2: The plate is white. | f2: The plate is white. | retained | same_fact |
| f3: A bowl is present. | f4: A bowl is present. | retained | same_fact |
| f6: Broccoli is present. | f7: Broccoli is present. | retained | same_fact |
| f7: Carrots are present. | f13: Carrots are present. | retained | same_fact |
| f4: The bowl contains broccoli. | f5: The bowl contains broccoli. | retained | same_fact |
| f5: The bowl contains carrots. | f6: The bowl contains other vegetables. | ambiguous | partial_overlap |
| f8: The bowl is on the plate. | f3: The plate has a bowl with it. | ambiguous | partial_overlap |
| ∅ | f9: The broccoli has various sizes. | added | not_expressed |
| ∅ | f10: The broccoli is spread across the plate. | added | not_expressed |
| ∅ | f11: There are several carrots. | added | not_expressed |
| ∅ | f12: Carrots are on the plate. | added | not_expressed |
| ∅ | f8: Other vegetables are present. | added | not_expressed |
| ∅ | f14: There are a few other vegetables on the plate. | added | not_expressed |
| ∅ | f15: A dining table is present. | added | not_expressed |
| ∅ | f16: The dining table is red. | added | not_expressed |
| ∅ | f17: A book is present. | added | not_expressed |
| ∅ | f18: The book is on the table. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A plate is present. | f1: A plate is present. | retained | same_fact |
| f2: The plate is white. | f2: The plate is white. | retained | same_fact |
| f3: A bowl is present. | f4: A bowl is present. | retained | same_fact |
| f4: The bowl contains broccoli. | f5: The bowl contains broccoli. | retained | same_fact |
| f6: Broccoli is present. | f7: Broccoli is present. | retained | same_fact |
| f7: Carrots are present. | f13: Carrots are present. | retained | same_fact |
| ∅ | f8: Other vegetables are present. | added | not_expressed |
| ∅ | f9: The broccoli has various sizes. | added | not_expressed |
| ∅ | f10: The broccoli is spread across the plate. | added | not_expressed |
| ∅ | f11: There are several carrots. | added | not_expressed |
| ∅ | f12: Carrots are on the plate. | added | not_expressed |
| ∅ | f14: There are a few other vegetables on the plate. | added | not_expressed |
| ∅ | f15: A dining table is present. | added | not_expressed |
| ∅ | f16: The dining table is red. | added | not_expressed |
| ∅ | f17: A book is present. | added | not_expressed |
| ∅ | f18: The book is on the table. | added | not_expressed |
| f5: The bowl contains carrots. | f6: The bowl contains other vegetables. | ambiguous | granularity |
| f8: The bowl is on the plate. | f3: The plate has a bowl with it. | ambiguous | partial_overlap |

## 188077

**Vanilla**

The image features a large airplane parked on the tarmac, with another smaller airplane positioned nearby. The larger airplane is situated on the left side of the scene, while the smaller one is on the right side. The smaller airplane appears to be a propeller plane, while the larger one is a jet.

There are several people scattered around the scene, likely attending to the planes or performing various tasks. Some of them are closer to the larger airplane, while others are near the smaller one. The presence of these individuals suggests that the airplanes are being prepared for takeoff or have recently landed.

**Steer**

The image shows a person standing on a runway next to a white airplane.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f2: The first airplane is large. | ∅ | removed | not_expressed |
| f1: A large airplane is present.<br>f6: Another airplane is present. | f6: An airplane is present. | ambiguous | entity_uncertain |
| f7: The second airplane is smaller. | ∅ | removed | not_expressed |
| f3: The large airplane is parked. | ∅ | removed | not_expressed |
| f5: Tarmac is present. | f5: A runway is present. | ambiguous | partial_overlap |
| f4: The large airplane is on the tarmac. | ∅ | ambiguous | entity_uncertain |
| ∅ | f1: A person is standing. | added | not_expressed |
| ∅ | f2: The person is on the runway. | added | not_expressed |
| ∅ | f3: The person is next to the airplane. | ambiguous | entity_uncertain |
| f8: The second airplane is near the first. | ∅ | removed | not_expressed |
| f9: The large airplane is on the left. | ∅ | removed | not_expressed |
| f10: The smaller airplane is on the right. | ∅ | removed | not_expressed |
| f11: The smaller airplane appears to be a propeller plane. | ∅ | removed | not_expressed |
| f12: The larger airplane is a jet. | ∅ | removed | not_expressed |
| f13: People are present. | f4: A person is present. | ambiguous | entity_uncertain |
| f14: There are several people. | ∅ | removed | not_expressed |
| f15: People are scattered around the scene. | ∅ | removed | not_expressed |
| f16: People likely attend to the planes or perform tasks. | ∅ | removed | not_expressed |
| f17: Some people are near the large airplane. | ∅ | removed | not_expressed |
| f18: Other people are near the smaller airplane. | ∅ | removed | not_expressed |
| ∅ | f7: The airplane is white. | added | not_expressed |

### 实际预测：needs_review

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f3: The large airplane is parked. | ∅ | removed | not_expressed |
| f9: The large airplane is on the left. | ∅ | removed | not_expressed |
| f10: The smaller airplane is on the right. | ∅ | removed | not_expressed |
| f11: The smaller airplane appears to be a propeller plane. | ∅ | removed | not_expressed |
| f12: The larger airplane is a jet. | ∅ | removed | not_expressed |
| f14: There are several people. | ∅ | removed | not_expressed |
| f15: People are scattered around the scene. | ∅ | removed | not_expressed |
| f16: People likely attend to the planes or perform tasks. | ∅ | removed | not_expressed |
| ∅ | f1: A person is standing. | added | not_expressed |
| ∅ | f7: The airplane is white. | added | not_expressed |
| f1: A large airplane is present.<br>f6: Another airplane is present. | f6: An airplane is present. | ambiguous | entity_uncertain |
| f4: The large airplane is on the tarmac. | f2: The person is on the runway. | ambiguous | entity_uncertain |
| f5: Tarmac is present. | f5: A runway is present. | ambiguous | entity_uncertain |
| f8: The second airplane is near the first.<br>f17: Some people are near the large airplane.<br>f18: Other people are near the smaller airplane. | f3: The person is next to the airplane. | ambiguous | entity_uncertain |
| f13: People are present. | f4: A person is present. | ambiguous | entity_uncertain |
| f2: The first airplane is large. | ∅ | ambiguous | alignment_validation_error |
| f7: The second airplane is smaller. | ∅ | ambiguous | alignment_validation_error |

rejected_alignments

```json
[
  {
    "index": 1,
    "raw": {
      "original_fact_ids": [
        "f2",
        "f7"
      ],
      "steer_fact_ids": [],
      "status": "removed",
      "reason": "not_expressed",
      "evidence": []
    },
    "error": "removed shape/reason"
  }
]
```

## 280888

**Vanilla**

The image captures a group of young women playing soccer on a grassy field. There are at least nine players visible in the scene, with some of them actively participating in the game, while others are watching or waiting for their turn. The players are spread out across the field, with some closer to the foreground and others further in the background.

A sports ball, likely a soccer ball, is located near the center of the field, indicating that the game is in progress. The players are wearing uniforms, which suggests that they are part of a team. The overall atmosphere of the scene is energetic and competitive, as the girls enjoy their time on the field.

**Steer**

The image depicts a group of girls playing soccer on a field. They are wearing uniforms and are spread out across the field. Some girls are running while others are stationary. The girls are in various positions on the field, some are in the middle of the field, others are near the edges. The girls are actively engaged in the game, with some girls in the background and others in the foreground.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: Young women are present. | f1: Girls are present. | ambiguous | partial_overlap |
| f2: The women play soccer. | f2: The girls play soccer. | retained | same_fact |
| f4: A field is present. | f4: A field is present. | retained | same_fact |
| f3: The players are on the field. | f3: The players are on the field. | retained | same_fact |
| f5: The field is grassy. | ∅ | removed | not_expressed |
| f6: At least nine players are visible. | ∅ | removed | not_expressed |
| f7: Some players actively participate while others watch or wait. | f8: Some girls run and others are stationary. | ambiguous | partial_overlap |
| f8: The players are spread across the field. | f7: The players are spread across the field. | retained | same_fact |
| f9: Some players are in the foreground and others in the background. | f11: Some girls are in the background and others in the foreground. | retained | same_fact |
| f10: A sports ball is present. | ∅ | removed | not_expressed |
| f11: The sports ball is likely a soccer ball. | ∅ | removed | not_expressed |
| f12: The ball is near the field center. | ∅ | removed | not_expressed |
| f14: Uniforms are present. | f6: Uniforms are present. | retained | same_fact |
| f13: The players wear uniforms. | f5: The girls wear uniforms. | retained | same_fact |
| ∅ | f9: Some girls are in the middle of the field. | added | not_expressed |
| ∅ | f10: Other girls are near the field edges. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: Young women are present. | f1: Girls are present. | retained | same_fact |
| f2: The women play soccer. | f2: The girls play soccer. | retained | same_fact |
| f3: The players are on the field. | f3: The players are on the field. | retained | same_fact |
| f4: A field is present. | f4: A field is present. | retained | same_fact |
| f5: The field is grassy. | ∅ | removed | not_expressed |
| f6: At least nine players are visible. | ∅ | removed | not_expressed |
| f8: The players are spread across the field. | f7: The players are spread across the field. | retained | same_fact |
| f9: Some players are in the foreground and others in the background. | f11: Some girls are in the background and others in the foreground. | retained | same_fact |
| f10: A sports ball is present. | ∅ | removed | not_expressed |
| f11: The sports ball is likely a soccer ball. | ∅ | removed | not_expressed |
| f12: The ball is near the field center. | ∅ | removed | not_expressed |
| f13: The players wear uniforms. | f5: The girls wear uniforms. | retained | same_fact |
| f14: Uniforms are present. | f6: Uniforms are present. | retained | same_fact |
| ∅ | f9: Some girls are in the middle of the field. | added | not_expressed |
| ∅ | f10: Other girls are near the field edges. | added | not_expressed |
| f7: Some players actively participate while others watch or wait. | f8: Some girls run and others are stationary. | ambiguous | partial_overlap |

## 136140

**Vanilla**

The image features a person holding a small, old-fashioned cell phone in their hand. The phone is positioned towards the center of the scene, with the person's hand holding it securely. The person appears to be focused on the device, possibly checking messages or using an app. The scene is set in a dark environment, which adds a sense of mystery to the image.

**Steer**

The image depicts a person holding a cell phone in their hand. The person is wearing glasses and a black sweater. The cell phone is open and ready to be used.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A person is present. | f1: A person is present. | retained | same_fact |
| f3: A cell phone is present. | f3: A cell phone is present. | retained | same_fact |
| f6: The person's hand is present. | f4: The person's hand is present. | retained | same_fact |
| f2: The person holds the cell phone in their hand. | f2: The person holds the phone in their hand. | retained | same_fact |
| f4: The phone is small. | ∅ | removed | not_expressed |
| f5: The phone is old-fashioned. | ∅ | removed | not_expressed |
| f7: The phone is towards the scene center. | ∅ | removed | not_expressed |
| f8: The person may be checking messages or using an app. | ∅ | removed | not_expressed |
| f9: The environment is dark. | ∅ | removed | not_expressed |
| ∅ | f7: Glasses are present. | added | not_expressed |
| ∅ | f5: The person wears glasses. | added | not_expressed |
| ∅ | f8: A sweater is present. | added | not_expressed |
| ∅ | f9: The sweater is black. | added | not_expressed |
| ∅ | f6: The person wears a sweater. | added | not_expressed |
| ∅ | f10: The phone is open. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A person is present. | f1: A person is present. | retained | same_fact |
| f2: The person holds the cell phone in their hand. | f2: The person holds the phone in their hand. | retained | same_fact |
| f3: A cell phone is present. | f3: A cell phone is present. | retained | same_fact |
| f4: The phone is small. | ∅ | removed | not_expressed |
| f5: The phone is old-fashioned. | ∅ | removed | not_expressed |
| f6: The person's hand is present. | f4: The person's hand is present. | retained | same_fact |
| f7: The phone is towards the scene center. | ∅ | removed | not_expressed |
| f8: The person may be checking messages or using an app. | ∅ | removed | not_expressed |
| f9: The environment is dark. | ∅ | removed | not_expressed |
| ∅ | f5: The person wears glasses. | added | not_expressed |
| ∅ | f6: The person wears a sweater. | added | not_expressed |
| ∅ | f7: Glasses are present. | added | not_expressed |
| ∅ | f8: A sweater is present. | added | not_expressed |
| ∅ | f9: The sweater is black. | added | not_expressed |
| ∅ | f10: The phone is open. | added | not_expressed |

## 69584

**Vanilla**

The image features a large airplane flying through a cloudy sky. The airplane is positioned in the middle of the scene, with its wings visible as it soars through the air. The sky is filled with clouds, creating a dramatic backdrop for the airplane's flight. The scene captures the beauty of the airplane in motion against the vast expanse of the sky.

**Steer**

The image depicts a large airplane flying through a cloudy sky. The plane is in the middle of the scene, and it appears to be a sunny day.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: An airplane is present. | f1: An airplane is present. | retained | same_fact |
| f2: The airplane is large. | f2: The airplane is large. | retained | same_fact |
| f4: The sky is present. | f4: The sky is present. | retained | same_fact |
| f5: The sky is cloudy. | f5: The sky is cloudy. | retained | same_fact |
| f3: The airplane flies through the sky. | f3: The airplane flies through the sky. | retained | same_fact |
| f6: The airplane is in the middle of the scene. | f6: The airplane is in the middle of the scene. | retained | same_fact |
| f7: The airplane's wings are visible. | ∅ | removed | not_expressed |
| f9: Clouds are present. | ∅ | ambiguous | extraction_gap |
| f8: The sky is filled with clouds. | ∅ | ambiguous | partial_overlap |
| ∅ | f7: It appears to be a sunny day. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: An airplane is present. | f1: An airplane is present. | retained | same_fact |
| f2: The airplane is large. | f2: The airplane is large. | retained | same_fact |
| f3: The airplane flies through the sky. | f3: The airplane flies through the sky. | retained | same_fact |
| f4: The sky is present. | f4: The sky is present. | retained | same_fact |
| f5: The sky is cloudy. | f5: The sky is cloudy. | retained | same_fact |
| f6: The airplane is in the middle of the scene. | f6: The airplane is in the middle of the scene. | retained | same_fact |
| f7: The airplane's wings are visible. | ∅ | removed | not_expressed |
| f8: The sky is filled with clouds. | ∅ | removed | not_expressed |
| f9: Clouds are present. | ∅ | removed | not_expressed |
| ∅ | f7: It appears to be a sunny day. | added | not_expressed |

## 319726

**Vanilla**

The image captures a tennis match in progress, with a man in a white shirt and red shorts serving the ball. He is holding a tennis racket and appears to be in the middle of a serve. The tennis ball is in the air, and the man is focused on hitting it.

There are several other people in the scene, some of whom are also holding tennis rackets, indicating that they are also participating in the match. A few of them are standing close to the main player, while others are scattered around the court.

In addition to the players, there are a few chairs placed around the court, likely for resting or observing the match. A backpack can also be seen on the ground, possibly belonging to one of the players.

**Steer**

The image depicts a man in red shorts and a white shirt playing tennis. He is in the middle of a tennis court, preparing to serve a tennis ball. He is wearing a bandage on his left knee, and he is holding a tennis racquet.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A man is present. | f1: A man is present. | retained | same_fact |
| f4: A shirt is present. | f6: A shirt is present. | retained | same_fact |
| f5: The shirt is white. | f7: The shirt is white. | retained | same_fact |
| f2: The man wears a shirt. | f2: The man wears a shirt. | retained | same_fact |
| f6: Shorts are present. | f4: Shorts are present. | retained | same_fact |
| f7: The shorts are red. | f5: The shorts are red. | retained | same_fact |
| f3: The man wears shorts. | f3: The man wears shorts. | retained | same_fact |
| f8: The man serves the ball. | f10: The man prepares to serve a ball. | ambiguous | partial_overlap |
| f12: A tennis ball is present. | f11: A tennis ball is present. | retained | same_fact |
| f10: A tennis racket is present. | f16: A tennis racquet is present. | retained | same_fact |
| f9: The man holds a tennis racket. | f15: The man holds a tennis racquet. | retained | same_fact |
| f11: The man appears in the middle of a serve. | ∅ | ambiguous | partial_overlap |
| f13: The ball is in the air. | ∅ | removed | not_expressed |
| f14: Other people are present. | ∅ | removed | not_expressed |
| f15: There are several other people. | ∅ | removed | not_expressed |
| f16: Some other people hold tennis rackets. | ∅ | removed | not_expressed |
| f17: A few people stand close to the main player. | ∅ | removed | not_expressed |
| f18: Other people are scattered around the court. | ∅ | removed | not_expressed |
| f19: A court is present. | f9: A tennis court is present. | retained | same_fact |
| f22: Chairs are present. | ∅ | removed | not_expressed |
| f20: There are a few chairs. | ∅ | removed | not_expressed |
| f21: Chairs are around the court. | ∅ | removed | not_expressed |
| f23: A backpack is present. | ∅ | removed | not_expressed |
| f25: The ground is present. | ∅ | removed | not_expressed |
| f24: The backpack is on the ground. | ∅ | removed | not_expressed |
| f26: The backpack may belong to a player. | ∅ | removed | not_expressed |
| ∅ | f8: The man is in the middle of the court. | added | not_expressed |
| ∅ | f13: A bandage is present. | added | not_expressed |
| ∅ | f14: The man's left knee is present. | added | not_expressed |
| ∅ | f12: The man wears a bandage on his left knee. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A man is present. | f1: A man is present. | retained | same_fact |
| f2: The man wears a shirt. | f2: The man wears a shirt. | retained | same_fact |
| f3: The man wears shorts. | f3: The man wears shorts. | retained | same_fact |
| f4: A shirt is present. | f6: A shirt is present. | retained | same_fact |
| f5: The shirt is white. | f7: The shirt is white. | retained | same_fact |
| f6: Shorts are present. | f4: Shorts are present. | retained | same_fact |
| f7: The shorts are red. | f5: The shorts are red. | retained | same_fact |
| f9: The man holds a tennis racket. | f15: The man holds a tennis racquet. | retained | same_fact |
| f10: A tennis racket is present. | f16: A tennis racquet is present. | retained | same_fact |
| f12: A tennis ball is present. | f11: A tennis ball is present. | retained | same_fact |
| f13: The ball is in the air. | ∅ | removed | not_expressed |
| f14: Other people are present. | ∅ | removed | not_expressed |
| f15: There are several other people. | ∅ | removed | not_expressed |
| f16: Some other people hold tennis rackets. | ∅ | removed | not_expressed |
| f17: A few people stand close to the main player. | ∅ | removed | not_expressed |
| f18: Other people are scattered around the court. | ∅ | removed | not_expressed |
| f19: A court is present. | f9: A tennis court is present. | retained | same_fact |
| f20: There are a few chairs. | ∅ | removed | not_expressed |
| f21: Chairs are around the court. | ∅ | removed | not_expressed |
| f22: Chairs are present. | ∅ | removed | not_expressed |
| f23: A backpack is present. | ∅ | removed | not_expressed |
| f24: The backpack is on the ground. | ∅ | removed | not_expressed |
| f25: The ground is present. | ∅ | removed | not_expressed |
| f26: The backpack may belong to a player. | ∅ | removed | not_expressed |
| ∅ | f8: The man is in the middle of the court. | added | not_expressed |
| ∅ | f12: The man wears a bandage on his left knee. | added | not_expressed |
| ∅ | f13: A bandage is present. | added | not_expressed |
| ∅ | f14: The man's left knee is present. | added | not_expressed |
| f8: The man serves the ball.<br>f11: The man appears in the middle of a serve. | f10: The man prepares to serve a ball. | ambiguous | partial_overlap |

## 443218

**Vanilla**

The image features a baby lying on a bed, sleeping peacefully. The baby is wearing a diaper and is positioned in the center of the bed. The bed is covered with a blanket, and there are two pillows on the bed, one on the left side and another on the right side.

In addition to the baby, there are two cell phones on the bed. One is located near the right side of the bed, while the other is closer to the left side. The scene gives a sense of a cozy and comfortable environment for the baby to rest.

**Steer**

The image depicts a young child sleeping on a bed with a pillow and blankets. The child is wearing a diaper and a pacifier. The bedding is messy with various items such as a cell phone, a remote, and a toy. The child is laying on their stomach with their hands and feet visible.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A baby is present. | f1: A young child is present. | ambiguous | partial_overlap |
| f3: A bed is present. | f3: A bed is present. | retained | same_fact |
| f2: The baby lies on the bed. | f17: The child lies on the bed. | retained | same_fact |
| f4: The baby sleeps. | f2: The child sleeps. | retained | same_fact |
| f6: A diaper is present. | f10: A diaper is present. | retained | same_fact |
| f5: The baby wears a diaper. | f8: The child wears a diaper. | retained | same_fact |
| f7: The baby is in the center of the bed. | ∅ | removed | not_expressed |
| f9: A blanket is present. | f7: Blankets are present. | retained | same_fact |
| f8: A blanket covers the bed. | f4: Blankets are on the bed. | retained | same_fact |
| f12: Pillows are present. | f6: A pillow is present. | retained | same_fact |
| f10: There are two pillows. | ∅ | removed | not_expressed |
| f11: Pillows are on the bed. | f5: A pillow is on the bed. | retained | same_fact |
| f13: One pillow is on the left and another on the right. | ∅ | removed | not_expressed |
| f16: Cell phones are present. | f14: A cell phone is present. | retained | same_fact |
| f14: There are two cell phones. | ∅ | removed | not_expressed |
| f15: Cell phones are on the bed. | f12: A cell phone is among the bedding. | retained | same_fact |
| f17: One phone is near the right of the bed and the other nearer the left. | ∅ | removed | not_expressed |
| ∅ | f11: A pacifier is present. | added | not_expressed |
| ∅ | f9: The child wears a pacifier. | added | not_expressed |
| ∅ | f13: The bedding is messy. | added | not_expressed |
| ∅ | f15: A remote is present. | added | not_expressed |
| ∅ | f16: A toy is present. | added | not_expressed |
| ∅ | f18: The child lies on their stomach. | added | not_expressed |
| ∅ | f19: The child's hands are visible. | added | not_expressed |
| ∅ | f20: The child's feet are visible. | added | not_expressed |

### 实际预测：failed

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A baby is present. | ∅ | ambiguous | stage_failed |
| f2: The baby lies on the bed. | ∅ | ambiguous | stage_failed |
| f3: A bed is present. | ∅ | ambiguous | stage_failed |
| f4: The baby sleeps. | ∅ | ambiguous | stage_failed |
| f5: The baby wears a diaper. | ∅ | ambiguous | stage_failed |
| f6: A diaper is present. | ∅ | ambiguous | stage_failed |
| f7: The baby is in the center of the bed. | ∅ | ambiguous | stage_failed |
| f8: A blanket covers the bed. | ∅ | ambiguous | stage_failed |
| f9: A blanket is present. | ∅ | ambiguous | stage_failed |
| f10: There are two pillows. | ∅ | ambiguous | stage_failed |
| f11: Pillows are on the bed. | ∅ | ambiguous | stage_failed |
| f12: Pillows are present. | ∅ | ambiguous | stage_failed |
| f13: One pillow is on the left and another on the right. | ∅ | ambiguous | stage_failed |
| f14: There are two cell phones. | ∅ | ambiguous | stage_failed |
| f15: Cell phones are on the bed. | ∅ | ambiguous | stage_failed |
| f16: Cell phones are present. | ∅ | ambiguous | stage_failed |
| f17: One phone is near the right of the bed and the other nearer the left. | ∅ | ambiguous | stage_failed |
| ∅ | f1: A young child is present. | ambiguous | stage_failed |
| ∅ | f2: The child sleeps. | ambiguous | stage_failed |
| ∅ | f3: A bed is present. | ambiguous | stage_failed |
| ∅ | f4: Blankets are on the bed. | ambiguous | stage_failed |
| ∅ | f5: A pillow is on the bed. | ambiguous | stage_failed |
| ∅ | f6: A pillow is present. | ambiguous | stage_failed |
| ∅ | f7: Blankets are present. | ambiguous | stage_failed |
| ∅ | f8: The child wears a diaper. | ambiguous | stage_failed |
| ∅ | f9: The child wears a pacifier. | ambiguous | stage_failed |
| ∅ | f10: A diaper is present. | ambiguous | stage_failed |
| ∅ | f11: A pacifier is present. | ambiguous | stage_failed |
| ∅ | f12: A cell phone is among the bedding. | ambiguous | stage_failed |
| ∅ | f13: The bedding is messy. | ambiguous | stage_failed |
| ∅ | f14: A cell phone is present. | ambiguous | stage_failed |
| ∅ | f15: A remote is present. | ambiguous | stage_failed |
| ∅ | f16: A toy is present. | ambiguous | stage_failed |
| ∅ | f17: The child lies on the bed. | ambiguous | stage_failed |
| ∅ | f18: The child lies on their stomach. | ambiguous | stage_failed |
| ∅ | f19: The child's hands are visible. | ambiguous | stage_failed |
| ∅ | f20: The child's feet are visible. | ambiguous | stage_failed |

## 142826

**Vanilla**

The image features a brick patio with several outdoor dining tables and chairs. There are multiple umbrellas providing shade for the tables, with some of them being black and others being white. The tables are arranged in various positions, creating a cozy and inviting atmosphere.

There are several people in the scene, some of them sitting at the tables and others standing nearby. The patio appears to be a popular spot for socializing and enjoying the outdoors.

**Steer**

The image depicts a patio area with several tables and chairs. There are umbrella-covered tables and chairs, and a few people are enjoying their time outdoors. The patio is adorned with several umbrella-covered tables and chairs, and a few people are enjoying their time outdoors.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A patio is present. | f1: A patio is present. | retained | same_fact |
| f2: The patio is brick. | ∅ | removed | not_expressed |
| f5: Tables are present. | f4: Tables are present. | retained | same_fact |
| f6: Chairs are present. | f5: Chairs are present. | retained | same_fact |
| f4: There are several tables. | f3: There are several tables. | retained | same_fact |
| f3: Tables and chairs are on the patio. | f2: Tables and chairs are on the patio. | retained | same_fact |
| f8: Umbrellas are present. | f6: Umbrellas are present. | retained | same_fact |
| f9: Umbrellas provide shade for tables. | f7: Umbrellas cover the tables. | retained | same_fact |
| f7: There are multiple umbrellas. | ∅ | removed | not_expressed |
| f10: Some umbrellas are black. | ∅ | removed | not_expressed |
| f11: Other umbrellas are white. | ∅ | removed | not_expressed |
| f12: Tables are arranged in various positions. | ∅ | removed | not_expressed |
| f14: People are present. | f10: People are present. | retained | same_fact |
| f13: There are several people. | f9: There are a few people. | modified | value_changed |
| f15: Some people sit at tables. | ∅ | removed | not_expressed |
| f16: Other people stand nearby. | ∅ | removed | not_expressed |
| ∅ | f8: Umbrellas cover chairs. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A patio is present. | f1: A patio is present. | retained | same_fact |
| f2: The patio is brick. | ∅ | removed | not_expressed |
| f3: Tables and chairs are on the patio. | f2: Tables and chairs are on the patio. | retained | same_fact |
| f4: There are several tables. | f3: There are several tables. | retained | same_fact |
| f5: Tables are present. | f4: Tables are present. | retained | same_fact |
| f6: Chairs are present. | f5: Chairs are present. | retained | same_fact |
| f7: There are multiple umbrellas. | ∅ | removed | not_expressed |
| f8: Umbrellas are present. | f6: Umbrellas are present. | retained | same_fact |
| f9: Umbrellas provide shade for tables. | f7: Umbrellas cover the tables. | modified | value_changed |
| f10: Some umbrellas are black. | ∅ | removed | not_expressed |
| f11: Other umbrellas are white. | ∅ | removed | not_expressed |
| f12: Tables are arranged in various positions. | ∅ | removed | not_expressed |
| f13: There are several people. | f9: There are a few people. | modified | value_changed |
| f14: People are present. | f10: People are present. | retained | same_fact |
| f15: Some people sit at tables. | ∅ | removed | not_expressed |
| f16: Other people stand nearby. | ∅ | removed | not_expressed |
| ∅ | f8: Umbrellas cover chairs. | added | not_expressed |

## 439426

**Vanilla**

The image features a person holding a glazed doughnut in their hand, showcasing the doughnut's hole. The doughnut is placed in the center of the scene, with the person's hand holding it. The person is standing on a tiled floor, which adds to the overall setting of the image.

**Steer**

The image features a person holding a delicious glazed donut with a hole in it. The person is standing on a tile floor, and their hand is holding the donut. The donut is placed on a tile floor, and it appears to be a popular snack choice.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A person is present. | f1: A person is present. | retained | same_fact |
| f5: The person's hand is present. | f9: The person's hand is present. | retained | same_fact |
| f3: A doughnut is present. | f3: A donut is present. | retained | same_fact |
| f4: The doughnut is glazed. | f4: The donut is glazed. | retained | same_fact |
| f6: The doughnut has a hole. | f5: The donut has a hole. | retained | same_fact |
| f2: The person holds the doughnut. | f2: The person holds the donut. | retained | same_fact |
| f8: The person's hand holds the doughnut. | f10: The person's hand holds the donut. | retained | same_fact |
| f7: The doughnut is in the scene center. | ∅ | removed | not_expressed |
| f10: A floor is present. | f7: A floor is present. | retained | same_fact |
| f11: The floor is tiled. | f8: The floor is tiled. | retained | same_fact |
| f9: The person stands on the floor. | f6: The person stands on the floor. | retained | same_fact |
| ∅ | f11: The donut is on the tile floor. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A person is present. | f1: A person is present. | retained | same_fact |
| f2: The person holds the doughnut. | f2: The person holds the donut. | retained | same_fact |
| f3: A doughnut is present. | f3: A donut is present. | retained | same_fact |
| f4: The doughnut is glazed. | f4: The donut is glazed. | retained | same_fact |
| f5: The person's hand is present. | f9: The person's hand is present. | retained | same_fact |
| f6: The doughnut has a hole. | f5: The donut has a hole. | retained | same_fact |
| f7: The doughnut is in the scene center. | ∅ | removed | not_expressed |
| f8: The person's hand holds the doughnut. | f10: The person's hand holds the donut. | retained | same_fact |
| f9: The person stands on the floor. | f6: The person stands on the floor. | retained | same_fact |
| f10: A floor is present. | f7: A floor is present. | retained | same_fact |
| f11: The floor is tiled. | f8: The floor is tiled. | retained | same_fact |
| ∅ | f11: The donut is on the tile floor. | added | not_expressed |

## 45644

**Vanilla**

The image features a vibrant display of fresh vegetables at a market, with a variety of broccoli and cauliflower prominently featured. The broccoli is arranged in several clusters, with some placed closer to the front and others further back. The cauliflower is also abundant in the display, with multiple clusters spread throughout the scene.

In addition to the vegetables, there are a few oranges visible in the background, adding a pop of color to the scene. A person can be seen in the background, likely browsing the produce or attending to the market stand. The overall atmosphere of the image is lively and inviting, showcasing the freshness and variety of the vegetables available for purchase.

**Steer**

The image showcases a variety of vegetables and fruits at a market. Broccoli, cabbage, and cauliflower are among the vegetables, while bananas and lemons are among the fruits. The market is well stocked with fresh produce, and it is a great place to shop for healthy and delicious meals.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f4: A market is present. | f5: A market is present. | retained | same_fact |
| f3: Vegetables are present. | f1: Vegetables are present. | retained | same_fact |
| f1: The vegetables are fresh. | f12: The produce is fresh. | ambiguous | partial_overlap |
| f5: Broccoli is present. | f6: Broccoli is present. | retained | same_fact |
| f6: Cauliflower is present. | f8: Cauliflower is present. | retained | same_fact |
| f2: The vegetables are at a market. | f2: Vegetables are at a market. | retained | same_fact |
| f7: Broccoli is arranged in several clusters. | ∅ | removed | not_expressed |
| f8: Some broccoli is near the front and other broccoli further back. | ∅ | removed | not_expressed |
| f9: The cauliflower is abundant. | ∅ | removed | not_expressed |
| f10: Cauliflower clusters are spread throughout the scene. | ∅ | removed | not_expressed |
| f13: Oranges are present. | ∅ | removed | not_expressed |
| f11: There are a few oranges. | ∅ | removed | not_expressed |
| f12: Oranges are in the background. | ∅ | removed | not_expressed |
| f14: A person is present. | ∅ | removed | not_expressed |
| f15: The person is in the background. | ∅ | removed | not_expressed |
| f16: The person likely browses produce or attends to the stand. | ∅ | removed | not_expressed |
| ∅ | f3: Fruit is present. | added | not_expressed |
| ∅ | f7: Cabbage is present. | added | not_expressed |
| ∅ | f9: Bananas are present. | added | not_expressed |
| ∅ | f10: Lemons are present. | added | not_expressed |
| ∅ | f4: Fruit is at the market. | added | not_expressed |
| ∅ | f11: The market is well stocked with produce. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f2: The vegetables are at a market. | f2: Vegetables are at a market. | retained | same_fact |
| f3: Vegetables are present. | f1: Vegetables are present. | retained | same_fact |
| f4: A market is present. | f5: A market is present. | retained | same_fact |
| f5: Broccoli is present. | f6: Broccoli is present. | retained | same_fact |
| f6: Cauliflower is present. | f8: Cauliflower is present. | retained | same_fact |
| f7: Broccoli is arranged in several clusters. | ∅ | removed | not_expressed |
| f8: Some broccoli is near the front and other broccoli further back. | ∅ | removed | not_expressed |
| f9: The cauliflower is abundant. | ∅ | removed | not_expressed |
| f10: Cauliflower clusters are spread throughout the scene. | ∅ | removed | not_expressed |
| f11: There are a few oranges. | ∅ | removed | not_expressed |
| f12: Oranges are in the background. | ∅ | removed | not_expressed |
| f13: Oranges are present. | ∅ | removed | not_expressed |
| f14: A person is present. | ∅ | removed | not_expressed |
| f15: The person is in the background. | ∅ | removed | not_expressed |
| f16: The person likely browses produce or attends to the stand. | ∅ | removed | not_expressed |
| ∅ | f3: Fruit is present. | added | not_expressed |
| ∅ | f4: Fruit is at the market. | added | not_expressed |
| ∅ | f7: Cabbage is present. | added | not_expressed |
| ∅ | f9: Bananas are present. | added | not_expressed |
| ∅ | f10: Lemons are present. | added | not_expressed |
| ∅ | f11: The market is well stocked with produce. | added | not_expressed |
| f1: The vegetables are fresh. | f12: The produce is fresh. | ambiguous | granularity |

## 260257

**Vanilla**

The image features a red stop sign with the word "all" written underneath it. The stop sign is positioned on a pole, and it is located in front of a tall building. The building is made of glass and has many windows, giving it a modern and sleek appearance. The stop sign is placed on a street corner, ensuring that drivers and pedestrians are aware of the traffic regulations in the area.

**Steer**

The image depicts a busy city street with a stop sign prominently displayed. The sign is positioned at an intersection, and it is a one way sign. The building in the background is tall and made of glass, with windows and balconies. The street is bustling with traffic, and a few people can be seen in the scene.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A stop sign is present. | f1: A stop sign is present. | retained | same_fact |
| f2: The stop sign is red. | ∅ | removed | not_expressed |
| f3: The word all is written underneath the stop sign. | ∅ | removed | not_expressed |
| f5: A pole is present. | ∅ | removed | not_expressed |
| f4: The stop sign is on the pole. | ∅ | removed | not_expressed |
| f7: A building is present. | f4: A building is present. | retained | same_fact |
| f8: The building is tall. | f5: The building is tall. | retained | same_fact |
| f9: The building is glass. | f7: The building is glass. | retained | same_fact |
| f12: Windows are present. | f10: Windows are present. | retained | same_fact |
| f10: The building has windows. | f8: The building has windows. | retained | same_fact |
| f11: The building has many windows. | ∅ | removed | not_expressed |
| f6: The stop sign is in front of the building. | f6: The building is in the background. | ambiguous | partial_overlap |
| f13: The stop sign is at a street corner. | f2: The sign is at an intersection. | ambiguous | partial_overlap |
| ∅ | f3: The sign is a one way sign. | added | not_expressed |
| ∅ | f11: Balconies are present. | added | not_expressed |
| ∅ | f9: The building has balconies. | added | not_expressed |
| ∅ | f14: People are present. | added | not_expressed |
| ∅ | f13: A few people are present. | added | not_expressed |
| ∅ | f12: There is traffic on the street. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A stop sign is present. | f1: A stop sign is present. | retained | same_fact |
| f2: The stop sign is red. | ∅ | removed | not_expressed |
| f3: The word all is written underneath the stop sign. | ∅ | removed | not_expressed |
| f4: The stop sign is on the pole. | ∅ | removed | not_expressed |
| f5: A pole is present. | ∅ | removed | not_expressed |
| f6: The stop sign is in front of the building. | ∅ | removed | not_expressed |
| f7: A building is present. | f4: A building is present. | retained | same_fact |
| f8: The building is tall. | f5: The building is tall. | retained | same_fact |
| f9: The building is glass. | f7: The building is glass. | retained | same_fact |
| f10: The building has windows. | f8: The building has windows. | retained | same_fact |
| f11: The building has many windows. | ∅ | removed | not_expressed |
| f12: Windows are present. | f10: Windows are present. | retained | same_fact |
| ∅ | f3: The sign is a one way sign. | added | not_expressed |
| ∅ | f6: The building is in the background. | added | not_expressed |
| ∅ | f9: The building has balconies. | added | not_expressed |
| ∅ | f11: Balconies are present. | added | not_expressed |
| ∅ | f12: There is traffic on the street. | added | not_expressed |
| ∅ | f13: A few people are present. | added | not_expressed |
| ∅ | f14: People are present. | added | not_expressed |
| f13: The stop sign is at a street corner. | f2: The sign is at an intersection. | ambiguous | partial_overlap |

## 224222

**Vanilla**

The image captures a lively scene at the beach, where two men are enjoying themselves in the ocean. One man is skillfully riding a wave on a surfboard, while the other man is swimming nearby. The surfer is in the middle of the wave, showcasing his talent and balance.

The ocean is filled with waves, providing an exciting environment for the surfer and swimmer. The waves are of varying sizes, with some larger ones closer to the surfer and smaller ones further away. The overall atmosphere is energetic and fun, as both men are having a great time in the water.

**Steer**

The image depicts a man riding a surfboard on a wave in the ocean. He is wearing a green shirt and yellow shorts. Another person is in the water, wearing a green shirt and yellow shorts. They both seem to be enjoying themselves in the water.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f4: A man surfing is present. | f1: A man surfing is present. | retained | same_fact |
| f7: Another man is present. | f13: Another person is present. | ambiguous | partial_overlap |
| f1: There are two men. | ∅ | removed | not_expressed |
| f3: The ocean is present. | f6: The ocean is present. | retained | same_fact |
| f12: Waves are present. | f5: A wave is present. | retained | same_fact |
| f6: A surfboard is present. | f4: A surfboard is present. | retained | same_fact |
| f5: The man rides a wave on a surfboard. | f2: The man rides a surfboard on a wave. | retained | same_fact |
| f2: The surfer is in the ocean. | f3: The surfer is in the ocean. | retained | same_fact |
| f8: The other man is in the water. | f14: Another person is in the water. | retained | same_fact |
| f9: The other man swims. | ∅ | removed | not_expressed |
| f10: The swimmer is near the surfer. | ∅ | removed | not_expressed |
| f11: The surfer is in the middle of the wave. | ∅ | removed | not_expressed |
| f13: The waves vary in size. | ∅ | removed | not_expressed |
| f14: Larger waves are closer to the surfer and smaller waves further away. | ∅ | removed | not_expressed |
| ∅ | f7: The surfer's shirt is present. | added | not_expressed |
| ∅ | f10: The surfer's shirt is green. | added | not_expressed |
| ∅ | f8: The surfer wears a shirt. | added | not_expressed |
| ∅ | f11: The surfer's shorts are present. | added | not_expressed |
| ∅ | f12: The surfer's shorts are yellow. | added | not_expressed |
| ∅ | f9: The surfer wears shorts. | added | not_expressed |
| ∅ | f15: The other person's shirt is present. | added | not_expressed |
| ∅ | f16: The other person's shirt is green. | added | not_expressed |
| ∅ | f17: The other person wears a shirt. | added | not_expressed |
| ∅ | f18: The other person's shorts are present. | added | not_expressed |
| ∅ | f19: The other person's shorts are yellow. | added | not_expressed |
| ∅ | f20: The other person wears shorts. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: There are two men. | ∅ | removed | not_expressed |
| f2: The surfer is in the ocean. | f3: The surfer is in the ocean. | retained | same_fact |
| f3: The ocean is present. | f6: The ocean is present. | retained | same_fact |
| f4: A man surfing is present. | f1: A man surfing is present. | retained | same_fact |
| f5: The man rides a wave on a surfboard. | f2: The man rides a surfboard on a wave. | retained | same_fact |
| f6: A surfboard is present. | f4: A surfboard is present. | retained | same_fact |
| f7: Another man is present. | f13: Another person is present. | retained | same_fact |
| f8: The other man is in the water. | f14: Another person is in the water. | retained | same_fact |
| f9: The other man swims. | ∅ | removed | not_expressed |
| f10: The swimmer is near the surfer. | ∅ | removed | not_expressed |
| f11: The surfer is in the middle of the wave. | ∅ | removed | not_expressed |
| f13: The waves vary in size. | ∅ | removed | not_expressed |
| f14: Larger waves are closer to the surfer and smaller waves further away. | ∅ | removed | not_expressed |
| ∅ | f7: The surfer's shirt is present. | added | not_expressed |
| ∅ | f8: The surfer wears a shirt. | added | not_expressed |
| ∅ | f9: The surfer wears shorts. | added | not_expressed |
| ∅ | f10: The surfer's shirt is green. | added | not_expressed |
| ∅ | f11: The surfer's shorts are present. | added | not_expressed |
| ∅ | f12: The surfer's shorts are yellow. | added | not_expressed |
| ∅ | f15: The other person's shirt is present. | added | not_expressed |
| ∅ | f16: The other person's shirt is green. | added | not_expressed |
| ∅ | f17: The other person wears a shirt. | added | not_expressed |
| ∅ | f18: The other person's shorts are present. | added | not_expressed |
| ∅ | f19: The other person's shorts are yellow. | added | not_expressed |
| ∅ | f20: The other person wears shorts. | added | not_expressed |
| f12: Waves are present. | f5: A wave is present. | ambiguous | granularity |

## 61715

**Vanilla**

The image features a train traveling down the tracks in a city, surrounded by tall buildings. The train is positioned in the middle of the scene, with a few cars visible in the background. The train appears to be a commuter train, providing transportation for the city's residents. The cityscape, with its tall buildings, creates a bustling urban atmosphere.

**Steer**

The image depicts a train traveling down a track in a city. The train is positioned in the middle of the scene, and it is surrounded by a variety of buildings. The train is passing through a city with a mix of cars and pedestrians. The scene also includes a few people scattered around the area, and a few cars parked or moving in the vicinity.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A train is present. | f1: A train is present. | retained | same_fact |
| f4: Tracks are present. | f4: A track is present. | retained | same_fact |
| f5: A city is present. | f5: A city is present. | retained | same_fact |
| f2: The train travels down the tracks. | f2: The train travels down a track. | retained | same_fact |
| f3: The train travels in a city. | f3: The train travels in a city. | retained | same_fact |
| f8: Buildings are present. | f8: Buildings are present. | retained | same_fact |
| f7: The buildings are tall. | ∅ | removed | not_expressed |
| f6: Buildings surround the train. | f7: Buildings surround the train. | retained | same_fact |
| f9: The train is in the middle of the scene. | f6: The train is in the middle of the scene. | retained | same_fact |
| f12: Cars are present. | f9: Cars are present. | retained | same_fact |
| f10: There are a few cars. | f12: There are a few cars. | retained | same_fact |
| f11: Cars are in the background. | ∅ | removed | not_expressed |
| f13: The train appears to be a commuter train. | ∅ | removed | not_expressed |
| ∅ | f10: Pedestrians are present. | added | not_expressed |
| ∅ | f11: A few people are scattered around the area. | added | not_expressed |
| ∅ | f13: Cars are parked or moving nearby. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A train is present. | f1: A train is present. | retained | same_fact |
| f2: The train travels down the tracks. | f2: The train travels down a track. | retained | same_fact |
| f3: The train travels in a city. | f3: The train travels in a city. | retained | same_fact |
| f4: Tracks are present. | f4: A track is present. | retained | same_fact |
| f5: A city is present. | f5: A city is present. | retained | same_fact |
| f6: Buildings surround the train. | f7: Buildings surround the train. | retained | same_fact |
| f7: The buildings are tall. | ∅ | removed | not_expressed |
| f8: Buildings are present. | f8: Buildings are present. | retained | same_fact |
| f9: The train is in the middle of the scene. | f6: The train is in the middle of the scene. | retained | same_fact |
| f10: There are a few cars. | f12: There are a few cars. | retained | same_fact |
| f11: Cars are in the background. | ∅ | removed | not_expressed |
| f12: Cars are present. | f9: Cars are present. | retained | same_fact |
| f13: The train appears to be a commuter train. | ∅ | removed | not_expressed |
| ∅ | f10: Pedestrians are present. | added | not_expressed |
| ∅ | f11: A few people are scattered around the area. | added | not_expressed |
| ∅ | f13: Cars are parked or moving nearby. | added | not_expressed |

## 332777

**Vanilla**

The image features a giraffe standing in a grassy area, possibly in a zoo enclosure. The giraffe is positioned near a wooden fence, and it appears to be looking over the fence. The scene is set against a backdrop of trees, creating a natural and serene environment for the giraffe.

**Steer**

The giraffe is standing in a grassy area with a tree in the background. It is positioned in front of a wooden structure. The giraffe is looking upwards, possibly at a branch or a tree.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A giraffe is present. | f1: A giraffe is present. | retained | same_fact |
| f2: The giraffe is standing. | f2: The giraffe is standing. | retained | same_fact |
| f4: A grassy area is present. | f4: A grassy area is present. | retained | same_fact |
| f3: The giraffe is in the grassy area. | f3: The giraffe is in a grassy area. | retained | same_fact |
| f5: The giraffe may be in a zoo enclosure. | ∅ | removed | not_expressed |
| f7: A fence is present. | f8: A structure is present. | ambiguous | partial_overlap |
| f8: The fence is wooden. | f9: The structure is wooden. | retained | same_fact |
| f6: The giraffe is near the fence. | f7: The giraffe is in front of the structure. | ambiguous | partial_overlap |
| f9: The giraffe appears to look over the fence. | f10: The giraffe looks upwards. | ambiguous | partial_overlap |
| f11: Trees are present. | f5: A tree is present. | retained | same_fact |
| f10: Trees form the backdrop. | f6: A tree is in the background. | retained | same_fact |
| ∅ | f11: The giraffe may be looking at a branch or a tree. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A giraffe is present. | f1: A giraffe is present. | retained | same_fact |
| f2: The giraffe is standing. | f2: The giraffe is standing. | retained | same_fact |
| f3: The giraffe is in the grassy area. | f3: The giraffe is in a grassy area. | retained | same_fact |
| f4: A grassy area is present. | f4: A grassy area is present. | retained | same_fact |
| f5: The giraffe may be in a zoo enclosure. | ∅ | removed | not_expressed |
| f7: A fence is present. | f8: A structure is present. | retained | same_fact |
| f8: The fence is wooden. | f9: The structure is wooden. | retained | same_fact |
| ∅ | f11: The giraffe may be looking at a branch or a tree. | added | not_expressed |
| f6: The giraffe is near the fence. | f7: The giraffe is in front of the structure. | ambiguous | partial_overlap |
| f9: The giraffe appears to look over the fence. | f10: The giraffe looks upwards. | ambiguous | partial_overlap |
| f10: Trees form the backdrop. | f6: A tree is in the background. | ambiguous | granularity |
| f11: Trees are present. | f5: A tree is present. | ambiguous | granularity |

## 303713

**Vanilla**

The image captures a tennis match in progress, with a man in the center of the scene holding a tennis racket and preparing to serve the ball. He is surrounded by a crowd of people, some of whom are sitting on chairs and others standing, all watching the game intently.

There are several chairs scattered around the scene, with some placed near the players and others further away. A few people can be seen holding cell phones, likely capturing the moment or communicating with others.

In addition to the main tennis player, there are other people in the scene, including a person holding a tennis racket and a few others who appear to be spectators. The atmosphere is lively and filled with anticipation as the players engage in the match.

**Steer**

The image depicts a crowded indoor arena with a tennis player in action. The player is wearing a white shirt and shorts, holding a tennis racket. The arena is filled with spectators, some of whom are seated on chairs, while others are standing or milling about. The scene captures the excitement of a tennis match with a large number of people present.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A man is present. | f4: A tennis player is present. | ambiguous | partial_overlap |
| f4: A tennis racket is present. | f12: A tennis racket is present. | retained | same_fact |
| f2: The man holds a tennis racket. | f11: The player holds a tennis racket. | retained | same_fact |
| f3: The main player is in the scene center. | ∅ | removed | not_expressed |
| f5: The man prepares to serve a ball. | f5: The tennis player is in action. | ambiguous | partial_overlap |
| f6: A ball is present. | ∅ | removed | not_expressed |
| f8: A crowd of people is present. | f13: Spectators are present. | ambiguous | partial_overlap |
| f10: Chairs are present. | f15: Chairs are present. | retained | same_fact |
| f9: Some people sit on chairs. | f14: Some spectators are seated on chairs. | retained | same_fact |
| f11: Other people are standing. | f16: Other spectators are standing. | retained | same_fact |
| f12: The crowd watches the game. | ∅ | ambiguous | extraction_gap |
| f7: The crowd surrounds the main player. | ∅ | removed | not_expressed |
| f13: There are several chairs. | ∅ | removed | not_expressed |
| f14: Chairs are scattered around the scene. | ∅ | removed | not_expressed |
| f15: Some chairs are near players and others further away. | ∅ | removed | not_expressed |
| f17: Cell phones are present. | ∅ | removed | not_expressed |
| f16: A few people hold cell phones. | ∅ | removed | not_expressed |
| f18: People likely capture the moment or communicate. | ∅ | removed | not_expressed |
| f19: Another racket-holding person is present. | ∅ | removed | not_expressed |
| f20: Another person holds a tennis racket. | ∅ | removed | not_expressed |
| ∅ | f1: An arena is present. | added | not_expressed |
| ∅ | f3: The arena is indoors. | added | not_expressed |
| ∅ | f2: The player is in the arena. | added | not_expressed |
| ∅ | f8: A shirt is present. | added | not_expressed |
| ∅ | f9: The shirt is white. | added | not_expressed |
| ∅ | f6: The player wears a shirt. | added | not_expressed |
| ∅ | f10: Shorts are present. | added | not_expressed |
| ∅ | f7: The player wears shorts. | added | not_expressed |
| ∅ | f17: Some spectators mill about. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A man is present. | f4: A tennis player is present. | retained | same_fact |
| f2: The man holds a tennis racket. | f11: The player holds a tennis racket. | retained | same_fact |
| f3: The main player is in the scene center. | ∅ | removed | not_expressed |
| f4: A tennis racket is present. | f12: A tennis racket is present. | retained | same_fact |
| f6: A ball is present. | ∅ | removed | not_expressed |
| f7: The crowd surrounds the main player. | ∅ | removed | not_expressed |
| f8: A crowd of people is present. | f13: Spectators are present. | retained | same_fact |
| f9: Some people sit on chairs. | f14: Some spectators are seated on chairs. | retained | same_fact |
| f10: Chairs are present. | f15: Chairs are present. | retained | same_fact |
| f11: Other people are standing. | f16: Other spectators are standing. | retained | same_fact |
| f12: The crowd watches the game. | ∅ | removed | not_expressed |
| f13: There are several chairs. | ∅ | removed | not_expressed |
| f14: Chairs are scattered around the scene. | ∅ | removed | not_expressed |
| f15: Some chairs are near players and others further away. | ∅ | removed | not_expressed |
| f16: A few people hold cell phones. | ∅ | removed | not_expressed |
| f17: Cell phones are present. | ∅ | removed | not_expressed |
| f18: People likely capture the moment or communicate. | ∅ | removed | not_expressed |
| f19: Another racket-holding person is present. | ∅ | removed | not_expressed |
| f20: Another person holds a tennis racket. | ∅ | removed | not_expressed |
| ∅ | f1: An arena is present. | added | not_expressed |
| ∅ | f2: The player is in the arena. | added | not_expressed |
| ∅ | f3: The arena is indoors. | added | not_expressed |
| ∅ | f6: The player wears a shirt. | added | not_expressed |
| ∅ | f7: The player wears shorts. | added | not_expressed |
| ∅ | f8: A shirt is present. | added | not_expressed |
| ∅ | f9: The shirt is white. | added | not_expressed |
| ∅ | f10: Shorts are present. | added | not_expressed |
| ∅ | f17: Some spectators mill about. | added | not_expressed |
| f5: The man prepares to serve a ball. | f5: The tennis player is in action. | ambiguous | partial_overlap |

## 373089

**Vanilla**

The image features a train station with a train on the tracks, pulling into the station. The train is positioned towards the center of the scene, and it appears to be a passenger train. The station is surrounded by a parking lot, with several cars parked in various positions around the area.

There are multiple people in the scene, some of them standing near the train, while others are scattered throughout the station. A few individuals can be seen closer to the foreground, while others are further back in the scene. The presence of people and cars suggests that the train station is a busy transportation hub.

**Steer**

The image depicts a train station with a yellow and black train on the tracks. The train is traveling on a track with several cars parked in a parking lot. There are also several people in the scene, some of them are near the train, others are scattered around the station.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A train station is present. | f1: A train station is present. | retained | same_fact |
| f2: A train is present. | f2: A train is present. | retained | same_fact |
| f4: Tracks are present. | f5: Tracks are present. | retained | same_fact |
| f3: The train is on the tracks. | f3: The train is on the tracks. | retained | same_fact |
| f5: The train pulls into the station. | f6: The train travels on a track. | ambiguous | partial_overlap |
| f6: The train is towards the scene center. | ∅ | removed | not_expressed |
| f7: The train appears to be a passenger train. | ∅ | removed | not_expressed |
| f9: A parking lot is present. | f11: A parking lot is present. | retained | same_fact |
| f8: The station is surrounded by a parking lot. | ∅ | removed | not_expressed |
| f13: Cars are present. | f10: Cars are present. | retained | same_fact |
| f11: There are several cars. | f7: There are several cars. | retained | same_fact |
| f12: Cars are parked. | f8: Cars are parked. | retained | same_fact |
| f10: Cars are in the parking lot. | f9: Cars are in a parking lot. | retained | same_fact |
| f15: People are present. | f13: People are present. | retained | same_fact |
| f14: There are multiple people. | f12: There are several people. | ambiguous | partial_overlap |
| f16: Some people are near the train. | f14: Some people are near the train. | retained | same_fact |
| f17: Some people are standing. | ∅ | removed | not_expressed |
| f18: Other people are scattered through the station. | f15: Other people are scattered around the station. | retained | same_fact |
| f19: Some people are in the foreground and others further back. | ∅ | removed | not_expressed |
| ∅ | f4: The train is yellow and black. | added | not_expressed |

### 实际预测：ready

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A train station is present. | f1: A train station is present. | retained | same_fact |
| f2: A train is present. | f2: A train is present. | retained | same_fact |
| f3: The train is on the tracks. | f3: The train is on the tracks. | retained | same_fact |
| f4: Tracks are present. | f5: Tracks are present. | retained | same_fact |
| f6: The train is towards the scene center. | ∅ | removed | not_expressed |
| f7: The train appears to be a passenger train. | ∅ | removed | not_expressed |
| f8: The station is surrounded by a parking lot. | ∅ | removed | not_expressed |
| f9: A parking lot is present. | f11: A parking lot is present. | retained | same_fact |
| f10: Cars are in the parking lot. | f9: Cars are in a parking lot. | retained | same_fact |
| f11: There are several cars. | f7: There are several cars. | retained | same_fact |
| f12: Cars are parked. | f8: Cars are parked. | retained | same_fact |
| f13: Cars are present. | f10: Cars are present. | retained | same_fact |
| f14: There are multiple people. | f12: There are several people. | retained | same_fact |
| f15: People are present. | f13: People are present. | retained | same_fact |
| f16: Some people are near the train. | f14: Some people are near the train. | retained | same_fact |
| f17: Some people are standing. | ∅ | removed | not_expressed |
| f18: Other people are scattered through the station. | f15: Other people are scattered around the station. | retained | same_fact |
| f19: Some people are in the foreground and others further back. | ∅ | removed | not_expressed |
| ∅ | f4: The train is yellow and black. | added | not_expressed |
| f5: The train pulls into the station. | f6: The train travels on a track. | ambiguous | partial_overlap |

## 458778

**Vanilla**

The image features a kitchen area inside a recreational vehicle, or RV. The kitchen is equipped with a stainless steel refrigerator, a microwave, and a sink. The refrigerator is positioned on the left side of the kitchen, while the microwave is located above the sink. The sink is situated in the middle of the kitchen area.

The kitchen is also equipped with a dining table, which is located on the right side of the kitchen. The table is accompanied by a chair, positioned close to the table. The overall setup of the kitchen and dining area creates a functional and comfortable space for cooking and dining within the RV.

**Steer**

The image showcases a kitchenette with a refrigerator and a microwave. The refrigerator is silver and occupies most of the space in the kitchenette. The microwave is positioned above the refrigerator. The kitchenette is well-equipped with a sink and a dining table.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A kitchen is present. | f1: A kitchenette is present. | retained | same_fact |
| f3: An RV is present. | ∅ | removed | not_expressed |
| f2: The kitchen is inside the RV. | ∅ | removed | not_expressed |
| f7: A refrigerator is present. | f4: A refrigerator is present. | retained | same_fact |
| f8: The refrigerator is stainless steel. | ∅ | removed | not_expressed |
| f9: A microwave is present. | f5: A microwave is present. | retained | same_fact |
| f10: A sink is present. | f11: A sink is present. | retained | same_fact |
| f4: The refrigerator is in the kitchen. | f2: The refrigerator is in the kitchenette. | retained | same_fact |
| f5: The microwave is in the kitchen. | f3: The microwave is in the kitchenette. | retained | same_fact |
| f6: The sink is in the kitchen. | f9: The sink is in the kitchenette. | retained | same_fact |
| f11: The refrigerator is on the left side of the kitchen. | ∅ | removed | not_expressed |
| f12: The microwave is above the sink. | f8: The microwave is above the refrigerator. | ambiguous | partial_overlap |
| f13: The sink is in the kitchen middle. | ∅ | removed | not_expressed |
| f15: A dining table is present. | f12: A dining table is present. | retained | same_fact |
| f14: The dining table is in the kitchen. | f10: The dining table is in the kitchenette. | retained | same_fact |
| f16: The table is on the right side of the kitchen. | ∅ | removed | not_expressed |
| f17: A chair is present. | ∅ | removed | not_expressed |
| f18: The chair is close to the table. | ∅ | removed | not_expressed |
| ∅ | f6: The refrigerator is silver. | added | not_expressed |
| ∅ | f7: The refrigerator occupies most of the kitchenette. | added | not_expressed |

### 实际预测：needs_review

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A kitchen is present. | f1: A kitchenette is present. | retained | same_fact |
| f2: The kitchen is inside the RV. | ∅ | removed | not_expressed |
| f3: An RV is present. | ∅ | removed | not_expressed |
| f4: The refrigerator is in the kitchen. | f2: The refrigerator is in the kitchenette. | retained | same_fact |
| f5: The microwave is in the kitchen. | f3: The microwave is in the kitchenette. | retained | same_fact |
| f6: The sink is in the kitchen. | f9: The sink is in the kitchenette. | retained | same_fact |
| f7: A refrigerator is present. | f4: A refrigerator is present. | retained | same_fact |
| f9: A microwave is present. | f5: A microwave is present. | retained | same_fact |
| f10: A sink is present. | f11: A sink is present. | retained | same_fact |
| f11: The refrigerator is on the left side of the kitchen. | ∅ | removed | not_expressed |
| f13: The sink is in the kitchen middle. | ∅ | removed | not_expressed |
| f14: The dining table is in the kitchen. | f10: The dining table is in the kitchenette. | retained | same_fact |
| f15: A dining table is present. | f12: A dining table is present. | retained | same_fact |
| f16: The table is on the right side of the kitchen. | ∅ | removed | not_expressed |
| f17: A chair is present. | ∅ | removed | not_expressed |
| f18: The chair is close to the table. | ∅ | removed | not_expressed |
| ∅ | f7: The refrigerator occupies most of the kitchenette. | added | not_expressed |
| f8: The refrigerator is stainless steel. | f6: The refrigerator is silver. | ambiguous | partial_overlap |
| f12: The microwave is above the sink. | f8: The microwave is above the refrigerator. | ambiguous | partial_overlap |

## 570659

**Vanilla**

The image features a cozy kitchen with a white stove top oven and a sink. The kitchen is well-equipped with various utensils and dishes, including multiple knives, spoons, and bowls. There are also several cups and bottles placed around the kitchen, adding to the overall clutter.

A potted plant is situated near the stove, adding a touch of greenery to the space. The kitchen is adorned with blue and white dishes, creating a visually appealing and harmonious atmosphere. A window can be seen in the background, allowing natural light to enter the room.

**Steer**

The image depicts a kitchen with a white oven and a black stove. Various utensils and dishes are displayed on shelves and countertops. There are several cups and bowls on display, along with a clock and a vase. The room also features a window and a potted plant.

### 冻结参考

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A kitchen is present. | f1: A kitchen is present. | retained | same_fact |
| f2: A stove top oven is present. | f2: An oven is present. | ambiguous | partial_overlap |
| f3: The stove top oven is white. | f3: The oven is white. | ambiguous | partial_overlap |
| f4: A sink is present. | ∅ | removed | not_expressed |
| ∅ | f4: A stove is present. | added | not_expressed |
| f7: Knives are present. | ∅ | removed | not_expressed |
| f8: Spoons are present. | ∅ | removed | not_expressed |
| f9: Bowls are present. | f13: Bowls are present. | retained | same_fact |
| f5: Utensils are present. | f7: Utensils are present. | retained | same_fact |
| f6: Dishes are present. | f8: Dishes are present. | retained | same_fact |
| f12: Cups are present. | f12: Cups are present. | retained | same_fact |
| f13: Bottles are present. | ∅ | removed | not_expressed |
| f10: There are several bottles. | ∅ | removed | not_expressed |
| f11: There are several cups. | f11: There are several cups. | retained | same_fact |
| f14: A potted plant is present. | f17: A potted plant is present. | retained | same_fact |
| f15: The potted plant is near the stove. | ∅ | removed | not_expressed |
| f16: Dishes are blue and white. | ∅ | removed | not_expressed |
| f17: A window is present. | f16: A window is present. | retained | same_fact |
| f18: The window is in the background. | ∅ | removed | not_expressed |
| f19: Light enters through the window. | ∅ | removed | not_expressed |
| ∅ | f5: The stove is black. | added | not_expressed |
| ∅ | f9: Shelves are present. | added | not_expressed |
| ∅ | f10: Countertops are present. | added | not_expressed |
| ∅ | f6: Utensils and dishes are displayed on shelves and countertops. | added | not_expressed |
| ∅ | f14: A clock is present. | added | not_expressed |
| ∅ | f15: A vase is present. | added | not_expressed |

### 实际预测：needs_review

| 原侧事实 | Steer事实 | 状态 | 原因 |
| --- | --- | --- | --- |
| f1: A kitchen is present. | f1: A kitchen is present. | retained | same_fact |
| f4: A sink is present. | ∅ | removed | not_expressed |
| f5: Utensils are present. | f7: Utensils are present. | retained | same_fact |
| f6: Dishes are present. | f8: Dishes are present. | retained | same_fact |
| f7: Knives are present. | ∅ | removed | not_expressed |
| f8: Spoons are present. | ∅ | removed | not_expressed |
| f9: Bowls are present. | f13: Bowls are present. | retained | same_fact |
| f10: There are several bottles. | ∅ | removed | not_expressed |
| f11: There are several cups. | f11: There are several cups. | retained | same_fact |
| f12: Cups are present. | f12: Cups are present. | retained | same_fact |
| f13: Bottles are present. | ∅ | removed | not_expressed |
| f14: A potted plant is present. | f17: A potted plant is present. | retained | same_fact |
| f15: The potted plant is near the stove. | ∅ | removed | not_expressed |
| f16: Dishes are blue and white. | ∅ | removed | not_expressed |
| f17: A window is present. | f16: A window is present. | retained | same_fact |
| f18: The window is in the background. | ∅ | removed | not_expressed |
| f19: Light enters through the window. | ∅ | removed | not_expressed |
| ∅ | f5: The stove is black. | added | not_expressed |
| ∅ | f6: Utensils and dishes are displayed on shelves and countertops. | added | not_expressed |
| ∅ | f9: Shelves are present. | added | not_expressed |
| ∅ | f10: Countertops are present. | added | not_expressed |
| ∅ | f14: A clock is present. | added | not_expressed |
| ∅ | f15: A vase is present. | added | not_expressed |
| f2: A stove top oven is present. | f2: An oven is present.<br>f4: A stove is present. | ambiguous | entity_uncertain |
| f3: The stove top oven is white. | f3: The oven is white. | ambiguous | entity_uncertain |
