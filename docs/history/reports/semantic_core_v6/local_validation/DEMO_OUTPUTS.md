# v6 示例输出（助手标注，本地归并；不是 DeepSeek 实测）

细类别由示例给定，type 和 in_main 由程序映射。示例供审核，不是准确率评估金标。

## example_1

> A woman in a red cotton shirt holds a blue cup.

| type | category | fact | assertion | polarity | reason |
| --- | --- | --- | --- | --- | --- |
| entity | human | There is a woman. | asserted | positive |  |
| entity | object | There is a shirt. | asserted | positive |  |
| entity | object | There is a cup. | asserted | positive |  |
| attribute | color | The shirt is red. | asserted | positive |  |
| attribute | material | The shirt is cotton. | asserted | positive |  |
| attribute | color | The cup is blue. | asserted | positive |  |
| relation | relation | The woman wears the shirt. | asserted | positive |  |
| relation | relation | The woman holds the cup. | asserted | positive |  |

## example_2

> An old wooden bench stands beside a tall tree.

| type | category | fact | assertion | polarity | reason |
| --- | --- | --- | --- | --- | --- |
| entity | object | There is a bench. | asserted | positive |  |
| entity | object | There is a tree. | asserted | positive |  |
| attribute | state | The bench is old. | asserted | positive |  |
| attribute | material | The bench is wooden. | asserted | positive |  |
| attribute | size | The tree is tall. | asserted | positive |  |
| relation | spatial | The bench is beside the tree. | asserted | positive |  |

## example_3

> Three men stand near a wall. One of them wears a black hat.

| type | category | fact | assertion | polarity | reason |
| --- | --- | --- | --- | --- | --- |
| entity | human | There is a group of men. | asserted | positive |  |
| attribute | counting | The described group contains three men. | asserted | positive |  |
| entity | object | There is a wall. | asserted | positive |  |
| relation | action | The men are standing. | asserted | positive |  |
| relation | spatial | The men are near the wall. | asserted | positive |  |
| entity | human | One of those three men is present. | asserted | positive |  |
| entity | object | There is a hat. | asserted | positive |  |
| attribute | color | The hat is black. | asserted | positive |  |
| relation | relation | One of those three men wears the hat. | asserted | positive |  |

## example_4

> Two pairs of shoes lie under a table. Several apples are in a bowl.

| type | category | fact | assertion | polarity | reason |
| --- | --- | --- | --- | --- | --- |
| entity | object | There are shoes. | asserted | positive |  |
| entity | object | There is a table. | asserted | positive |  |
| entity | food | There are apples. | asserted | positive |  |
| entity | object | There is a bowl. | asserted | positive |  |
| attribute | counting | There are two pairs of the described shoes. | asserted | positive |  |
| attribute | counting | There are several of the described apples. | asserted | positive |  |
| relation | spatial | The shoes are under the table. | asserted | positive |  |
| relation | spatial | The apples are in the bowl. | asserted | positive |  |

## example_5

> A hand holds a phone with a bright screen. The phone may be broken.

| type | category | fact | assertion | polarity | reason |
| --- | --- | --- | --- | --- | --- |
| entity | body_part | There is a hand. | asserted | positive |  |
| entity | object | There is a phone. | asserted | positive |  |
| entity | object | There is a screen. | asserted | positive |  |
| relation | relation | The hand holds the phone. | asserted | positive |  |
| relation | relation | The phone has a screen. | asserted | positive |  |
| attribute | attribute | The screen is bright. | asserted | positive |  |
| attribute | state | The phone may be broken. | speculative | positive |  |

## example_6

> A man sits on a bench and prepares to throw a ball. He is not holding a bag.

| type | category | fact | assertion | polarity | reason |
| --- | --- | --- | --- | --- | --- |
| entity | human | There is a man. | asserted | positive |  |
| entity | object | There is a bench. | asserted | positive |  |
| entity | object | There is a ball. | asserted | positive |  |
| relation | action | The man is sitting. | asserted | positive |  |
| relation | spatial | The man is on the bench. | asserted | positive |  |
| relation | action | The man prepares to throw a ball. | asserted | positive |  |
| relation | relation | The man is not holding a bag. | asserted | negative |  |

## example_7

> A surfboard leans against a wall. Another surfboard is on the sand.

| type | category | fact | assertion | polarity | reason |
| --- | --- | --- | --- | --- | --- |
| entity | object | There is a surfboard. | asserted | positive |  |
| entity | object | There is a wall. | asserted | positive |  |
| entity | object | There is another surfboard. | asserted | positive |  |
| entity | object | There is sand. | asserted | positive |  |
| relation | spatial | The first-mentioned surfboard leans against the wall. | asserted | positive |  |
| relation | spatial | The other surfboard is on the sand. | asserted | positive |  |

## example_8

> Some flowers look dry and damaged. The arrangement feels beautiful and comforting, suggesting a celebration.

| type | category | fact | assertion | polarity | reason |
| --- | --- | --- | --- | --- | --- |
| entity | object | There are flowers. | asserted | positive |  |
| attribute | state | Some flowers look dry. | speculative | positive |  |
| attribute | state | Some flowers look damaged. | speculative | positive |  |
| other | other | The arrangement feels beautiful and comforting. | asserted | positive | subjective |
| other | other | The arrangement suggests a celebration. | speculative | positive | scope |
