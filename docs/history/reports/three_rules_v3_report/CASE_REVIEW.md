# 三轮逐样本复核

三次独立 API 提取的记录均保留。checked 目录是相同请求响应在最终本地规则上的离线复放，不是三次新增 API 调用。共同出现不保证正确；差异不自动代表语义损失。

## 116887_vista_top_p

A tennis player in a white uniform with a yellow tennis racquet in hand prepares to serve the ball.

状态：success / success / success

三轮共同事实：

- action: tennis player prepares to serve ball
- attribute: tennis racquet is yellow
- attribute: uniform is white
- object: ball exists
- object: hand exists
- object: tennis player exists
- object: tennis racquet exists
- object: uniform exists
- relation: tennis player holds tennis racquet
- relation: tennis player wears uniform

第 1 轮相对共同部分的额外表述：

无。

第 2 轮相对共同部分的额外表述：

- relation: tennis racquet is in hand

第 3 轮相对共同部分的额外表述：

无。

## 331883_vista_beam5

The man is sleeping on a mattress on a floor.

状态：success / success / success

三轮共同事实：

- action: man is sleeping
- object: floor exists
- object: man exists
- object: mattress exists
- relation: man is on mattress
- relation: mattress is on floor

第 1 轮相对共同部分的额外表述：

无。

第 2 轮相对共同部分的额外表述：

无。

第 3 轮相对共同部分的额外表述：

无。

## 332570_vanilla_beam5

The image features a close-up view of a person's hand holding a cell phone. The cell phone is prominently displayed in the foreground, occupying a significant portion of the image. On the screen of the cell phone, there is a menu visible, indicating that the person might be using the device for various purposes, such as browsing the internet, texting, or making calls. The hand holding the cell phone appears to be in focus, while the rest of the scene is slightly blurred, creating a sense of depth in the image.

状态：success / success / success

三轮共同事实：

- attribute: cell phone is prominent
- object: cell phone exists
- object: hand exists
- object: menu exists
- object: screen exists
- relation: cell phone is in foreground
- relation: cell phone occupies significant portion of image
- relation: hand holds cell phone
- relation: hand is close to camera
- relation: menu is on screen
- relation: screen is on cell phone

第 1 轮相对共同部分的额外表述：

无。

第 2 轮相对共同部分的额外表述：

无。

第 3 轮相对共同部分的额外表述：

无。

## 332570_vanilla_greedy

The image features a close-up of a person's hand holding a smartphone. The phone is open and displaying a screen with various options, including a menu and a search bar. The hand is positioned in the upper left corner of the image, with the phone occupying the majority of the frame. The person's thumb is visible on the bottom right side of the phone, likely used for navigating the screen.

状态：success / success / success

三轮共同事实：

- attribute: phone is open
- object: hand exists
- object: menu exists
- object: screen exists
- object: search bar exists
- object: smartphone exists
- object: thumb exists
- relation: hand holds smartphone
- relation: hand is close to camera
- relation: hand is in upper left corner of image
- relation: menu is on screen
- relation: phone displays screen
- relation: phone occupies majority of frame
- relation: search bar is on screen
- relation: thumb is on bottom right side of phone

第 1 轮相对共同部分的额外表述：

无。

第 2 轮相对共同部分的额外表述：

无。

第 3 轮相对共同部分的额外表述：

无。

## 332570_vanilla_top_p

The image features a person's hand holding a Palm Treo smartphone up close. The hand is in the foreground, occupying most of the frame, while the phone fills the middle of the scene. On the screen, there is a menu displayed with various options, including a search function. This gives the impression of the smartphone in use, possibly for browsing, searching for information, or making a call.

状态：success / success / success

三轮共同事实：

- object: hand exists
- object: menu exists
- object: screen exists
- object: search function exists
- object: smartphone exists
- relation: hand holds smartphone
- relation: hand is in foreground
- relation: hand occupies most of frame
- relation: menu includes search function
- relation: menu is on screen
- relation: phone is in middle of scene
- relation: smartphone is close to camera

第 1 轮相对共同部分的额外表述：

无。

第 2 轮相对共同部分的额外表述：

无。

第 3 轮相对共同部分的额外表述：

无。

## 332570_vista_beam5

Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm Palm

状态：needs_review / needs_review / needs_review

三轮共同事实：


第 1 轮相对共同部分的额外表述：

无。

第 2 轮相对共同部分的额外表述：

无。

第 3 轮相对共同部分的额外表述：

无。

## 332570_vista_greedy

A hand holding a cell phone with a keyboard on it.

状态：success / success / success

三轮共同事实：

- object: cell phone exists
- object: hand exists
- object: keyboard exists
- relation: hand holds cell phone
- relation: keyboard is on cell phone

第 1 轮相对共同部分的额外表述：

无。

第 2 轮相对共同部分的额外表述：

无。

第 3 轮相对共同部分的额外表述：

无。

## 332570_vista_top_p

the palm palm is in the foreground with a hand in the background holding a phone.

状态：success / success / success

三轮共同事实：

- object: hand exists
- object: palm exists
- object: phone exists
- relation: hand holds phone
- relation: hand is in background
- relation: palm is in foreground

第 1 轮相对共同部分的额外表述：

无。

第 2 轮相对共同部分的额外表述：

无。

第 3 轮相对共同部分的额外表述：

无。

## 352478_vanilla_greedy

The image features a large display of fresh vegetables, including a variety of broccoli and lettuce, arranged in a market setting. The broccoli is displayed in two separate piles, one on the left side and the other on the right side of the image. The lettuce is also displayed in two piles, one in the middle and the other on the right side.

In addition to the vegetables, there are several potted plants placed throughout the scene, adding a touch of greenery to the display. A bicycle can be seen in the background, possibly belonging to a customer or a vendor. There are also a few people present in the scene, likely browsing the vegetable selection or attending to the market.

状态：success / success / success

三轮共同事实：

- attribute: vegetables are fresh
- count: a few people
- count: several potted plants
- count: two piles of broccoli
- count: two piles of lettuce
- object: bicycle exists
- object: broccoli exists
- object: lettuce exists
- object: person exists
- object: potted plant exists
- relation: bicycle is in background
- relation: broccoli pile is on left side
- relation: broccoli pile is on right side
- relation: lettuce pile is in middle
- relation: lettuce pile is on right side
- relation: people are in scene
- relation: potted plants are throughout scene
- relation: vegetables are in market setting

第 1 轮相对共同部分的额外表述：

无。

第 2 轮相对共同部分的额外表述：

无。

第 3 轮相对共同部分的额外表述：

无。

## 43324_vanilla_beam5

In the image, a shirtless man is sitting on the ground next to a surfboard. He is wearing a red hooded sweatshirt and appears to be resting or taking a break from surfing. The surfboard is positioned in front of him, occupying a significant portion of the scene.

In the background, another surfboard can be seen leaning against a wall, further emphasizing the surfing theme of the image.

状态：success / success / success

三轮共同事实：

- action: man is sitting
- attribute: hooded sweatshirt is red
- attribute: man is shirtless
- count: at least two surfboards
- object: ground exists
- object: hooded sweatshirt exists
- object: man exists
- object: surfboard exists
- object: wall exists
- relation: man is next to surfboard
- relation: man is on ground
- relation: man wears hooded sweatshirt
- relation: surfboard is in background
- relation: surfboard is in front of man
- relation: surfboard leans against wall

第 1 轮相对共同部分的额外表述：

无。

第 2 轮相对共同部分的额外表述：

无。

第 3 轮相对共同部分的额外表述：

无。

## 54627_vista_greedy

The image depicts a group of horses grazing in a field. There are at least four horses visible in the scene. They are spread out across the field, some are closer to the camera while others are further away. The horses are grazing on grass, and some are positioned near trees.

状态：success / success / success

三轮共同事实：

- action: horses are grazing
- action: horses are grazing on grass
- count: at least four horses
- object: camera exists
- object: field exists
- object: grass exists
- object: horse exists
- object: tree exists
- relation: horses are in field
- relation: horses are spread out across field
- relation: other horses are further away from camera
- relation: some horses are closer to camera
- relation: some horses are near trees

第 1 轮相对共同部分的额外表述：

无。

第 2 轮相对共同部分的额外表述：

无。

第 3 轮相对共同部分的额外表述：

无。

## 561517_vanilla_top_p

The image features a delicious meal consisting of french toast, fries, and salad on a white plate. The plate has a knife placed alongside the food, and a fork is positioned on the left side. A slice of lemon can be seen on the right side of the plate, adding a refreshing touch to the meal. A fork and a knife are also visible within the image, indicating that the person enjoying the meal will likely use them for cutting and eating.

状态：success / success / success

三轮共同事实：

- attribute: plate is white
- object: fork exists
- object: french toast exists
- object: fries exist
- object: knife exists
- object: plate exists
- object: salad exists
- relation: fork is on left side
- relation: french toast is on plate
- relation: fries are on plate
- relation: knife is beside food
- relation: salad is on plate

第 1 轮相对共同部分的额外表述：

- object: slice of lemon exists
- relation: slice of lemon is on right side of plate

第 2 轮相对共同部分的额外表述：

- object: lemon slice exists
- relation: lemon slice is on right side of plate

第 3 轮相对共同部分的额外表述：

- object: lemon slice exists
- relation: lemon slice is on right side of plate
