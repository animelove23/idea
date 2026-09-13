# 原图与固定局部视图：实体视觉测试

固定41条实体命题，原提示和原6-shot；每图保留原图并附四个60%边长、重叠的原像素视图。区域不依赖标签或人工主体框。

| 条件 | 正确/41 | 一致率 | Macro-F1 | 错误确定判断 | 输入tokens |
|---|---:|---:|---:|---:|---:|
| control | 33 | 80.49% | 72.29% | 3 | 84938 |
| multiview | 31 | 75.61% | 61.67% | 4 | 123462 |

成对修复1条，回退3条；候选是否通过本轮预设门槛：False。

## 发生变化的样本

- 381925_v1：参考supported；hallucinated → supported。原理由：No dog is visible in the image.；局部视图理由：A small dog is visible being held in the girl's arms.
- 381925_v2：参考uncertain；uncertain → hallucinated。原理由：The small object held in the person's hand is not clearly identifiable as a remote control.；局部视图理由：No remote control is visible in the image; the person is holding a bag and a small dog.
- 303499_v3：参考uncertain；uncertain → supported。原理由：The image shows an outdoor courtyard with riders, but whether it is a public area is not visually verifiable.；局部视图理由：The scene shows a paved courtyard with a large building, consistent with a public area.
- 519838_v2：参考hallucinated；hallucinated → uncertain。原理由：No backpack is visible in the image.；局部视图理由：No backpack is clearly visible in any view of the image.

## 范围

- 旧开发图上的候选参考一致率，不是新图泛化或人工gold准确率。原标签未修改。
- 输入视图改变，不能把不同条件当相同query的随机重复。模型调用均为fresh；无投票、重试、额外裁判。
- 5项局部模块测试覆盖像素一致、几何、全图覆盖、重用和few-shot/原query不变。
- 判断增加局部视图能否帮助识别，不等于实现了实例级自动定位。
- 未修改主框架默认行为。属性和端到端迁移结论尚未在本条件下验证。
