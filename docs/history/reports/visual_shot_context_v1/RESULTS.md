# X5a：现有6-shot主体字段补齐测试

仅补齐现有示例的entity_context，示例图像、命题、答案、顺序及数量不变；查询使用原图，未叠加局部视图。全部60条固定视觉命题两条件交错、fresh调用。

| 条件 | 实体正确/41 | 属性正确/19 | 整体正确/60 | 整体Macro-F1 |
|---|---:|---:|---:|---:|
| control | 33 (80.49%) | 14 | 47 | 71.80% |
| shot_context | 32 (78.05%) | 15 | 47 | 68.09% |

是否达到预设接受条件：False。

## 变化样本

- 352377_v3（entity）：参考uncertain；uncertain → hallucinated。原理由：The image shows green apples in focus and blurred yellow/orange fruit in the background, but no banana is clearly identifiable.；候选理由：The visible produce consists of apples and citrus fruits; no bananas are present.
- 381925_v1（entity）：参考supported；uncertain → hallucinated。原理由：The object held by the girl is not clearly identifiable as a dog.；候选理由：No dog is visible in the image.
- 565761_v1（attribute）：参考supported；uncertain → supported。原理由：The visible portion of the room does not clearly establish its overall size.；候选理由：The room appears spacious with high ceilings and a large seating area.

## 解释限制

- 参考仍是旧助手候选，图像已用于开发；不是独立人工gold或未见确认集。
- source_window使用原示例命题本身，没有虚构完整caption或视觉边框。此实验衡量输入字段格式对齐，不代表新增视觉定位证据。
- 没有添加或替换示例内容，不归因于某一新增正反例。
- 主框架默认行为未修改；不通过则保留为失败实验。
