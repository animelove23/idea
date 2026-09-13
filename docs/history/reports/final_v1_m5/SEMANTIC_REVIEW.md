# M5最终完整测评的独立语义复核

完整1158条结果完成后，重新以同一579条旧参考计算；不改参考、预测、主metrics或冻结代码。旧参考由助手标注，未经独立人工裁决。

## 完整指标

| 条件 | 实体 | 属性 | 全体 | 实体Macro-F1 | 实体错误确定判断 |
|---|---:|---:|---:|---:|---:|
| context | 434/508 (85.43%) | 57/71 (80.28%) | 491/579 (84.80%) | 60.34% | 55 |
| proposition | 435/508 (85.63%) | 63/71 (88.73%) | 498/579 (86.01%) | 55.32% | 67 |

实体严格超过90%：{'context': False, 'proposition': False}。

## 同样本配对变化

| 类型 | 修正 | 退化 | 净增加正确 | 标签变化总数 |
|---|---:|---:|---:|---:|
| all | 25 | 18 | +7 | 52 |
| entity | 17 | 16 | +1 | 41 |
| attribute | 8 | 2 | +6 | 11 |

修正/退化均以冻结候选参考定义；完整case ID清单保存在JSON中。

## 复用原composite标记诊断

| 原有标记 | 数量 | context一致率 | proposition一致率 |
|---|---:|---:|---:|
| false | 451 | 388/451 (86.03%) | 388/451 (86.03%) |
| true | 57 | 46/57 (80.70%) | 47/57 (82.46%) |

标记完全沿用references现有字段。它只是文本筛查：false组不等于纯object金标；主指标始终508分母，未排除争议样本。

## 逐图审阅的剩余实体分歧

以下样本为有目的地选择的诊断例，不据此估计全体错误类别比例；所有标签保持原值。

| 样本及原图 | 命题 | 参考 | context | proposition | 主要问题 |
|---|---|---|---|---|---|
| [565761:original:f2](../visual40_v1/images/565761.jpg) | There are two men. | supported | supported | hallucinated | 限定命题/计数范围 |
| [565761:original:f12](../visual40_v1/images/565761.jpg) | The other man is present. | supported | uncertain | uncertain | 指代/场景边界 |
| [565761:original:f16](../visual40_v1/images/565761.jpg) | There is a dining table. | hallucinated | uncertain | supported | 纯object类别误认 |
| [265462:steer:f1](../visual40_v1/images/265462.jpg) | There is a group of skateboarders. | uncertain | supported | supported | 限定命题/主体身份 |
| [265462:original:f9](../visual40_v1/images/265462.jpg) | There are other skateboarders following behind the foreground skateboarder. | uncertain | supported | supported | 限定命题/主体身份 |
| [388829:steer:f6](../visual40_v1/images/388829.jpg) | There is a hat. | hallucinated | hallucinated | supported | 纯object类别误认 |
| [388829:steer:f1](../visual40_v1/images/388829.jpg) | There is a man. | uncertain | supported | supported | 参考争议/细分类别 |
| [399741:original:f3](../visual40_v1/images/399741.jpg) | There is a teddy bear. | hallucinated | supported | supported | 纯object类别误认 |
| [399741:original:f5](../visual40_v1/images/399741.jpg) | There is a toy car. | supported | hallucinated | hallucinated | 纯object误认/小目标 |
| [399741:steer:f7](../visual40_v1/images/399741.jpg) | There is a toy car. | supported | hallucinated | hallucinated | 纯object误认/小目标 |
| [462687:original:f8](../visual40_v1/images/462687.jpg) | There are slices of pizza. | hallucinated | supported | supported | 纯object类别误认 |
| [578655:original:f6](../visual40_v1/images/578655.jpg) | There is a parasailer. | hallucinated | supported | supported | 纯object细类/场景边界 |
| [402623:original:f11](../visual40_v1/images/402623.jpg) | There are two other umbrellas. | hallucinated | supported | supported | 限定命题/other计数 |
| [281711:original:f8](../visual40_v1/images/281711.jpg) | There is a sink. | supported | uncertain | uncertain | 小目标/低光证据 |
| [281711:original:f19](../visual40_v1/images/281711.jpg) | There is a potted plant. | uncertain | supported | supported | 参考争议/可见部件 |
| [483723:original:f17](../visual40_v1/images/483723.jpg) | There is a cell phone. | uncertain | hallucinated | hallucinated | 指代/遮挡下缺席判断 |
| [32284:original:f21](../visual40_v1/images/32284.jpg) | There is a truck. | hallucinated | hallucinated | supported | 纯object类别误认 |
| [110196:steer:f14](../visual40_v1/images/110196.jpg) | There is another sign. | uncertain | supported | supported | 指代/参考争议 |
| [22461:original:f4](../visual40_v1/images/22461.jpg) | There is a cup. | hallucinated | supported | supported | 纯object类别边界 |
| [22461:original:f7](../visual40_v1/images/22461.jpg) | There are Cheerios. | uncertain | supported | supported | 限定命题/品牌身份 |

**565761:original:f2**：原图前方有两位谈话者，同时可见听众。原caption中的two men指谈话者子群；模型以全图超过两人否定命题，混淆子群计数与全图精确总数。

**565761:original:f12**：原caption可把the other指向两位谈话者中另一人。恢复全文后模型仍不确定，说明文本上下文并未自动变成图像主体绑定。

**565761:original:f16**：原图前方高脚椅、讲台及电视支撑物可见，未见明确餐桌；模型以任意桌状表面支持dining table，忽略细类别。

**265462:steer:f1**：图像呈现相似着装滑板者的多个连续位置，具有动作合成特征。人形存在容易识别，但多位置不等于多个不同人；旧U合理表达身份不确定。

**265462:original:f9**：后方人形可能是同一滑板者的连续曝光；模型直接支持other skateboarders following behind，未检查不同主体这一限制。

**388829:steer:f6**：可见头带/绑头巾，而非典型带帽冠的帽子。模型把头部覆盖物直接认作hat。类别边界应独立固定。

**388829:steer:f1**：人物存在无疑；图像不能稳妥确定man这一细分类别，且模型提到的beard/hat与可见特征不吻合。此题不能作为纯person存在难度的代表。

**399741:original:f3**：毛绒玩具白底黑斑、口鼻突出，外观更接近牛；模型只凭圆头和四肢支持teddy bear，未使用区分类别特征。旧参考仍需独立审核，未在本轮改标。

**399741:original:f5**：左下玩具区域有黄色小车辆，但其车种细节有限；模型对不同命题分别称toy car、train、truck，说明区域观察和细类命名不稳定。

**399741:steer:f7**：黄色小车辆位于左下边缘的红色玩具设施旁，容易被主玩具遮挡和忽略；没有证据证明增加语义字段即可补足视觉细节。

**462687:original:f8**：人手中的食物可见面包/夹心形态，未见足以区分披萨的顶部配料；模型以三角形与边缘直接支持pizza，证据不充分。

**578655:original:f6**：人位于水面、上方是牵引风筝；模型将可能的风筝冲浪者称parasailer。需要区分水面受牵引与空中悬挂主体。

**402623:original:f11**：图上共两把伞。原文先提一把伞，随后two other umbrellas要求另外两把；模型把总共两把误作额外两把。完整命题字段仍未解决集合指代。

**281711:original:f8**：厨房工作台和局部反光结构可见，水槽区域较暗且被杂物遮挡。S与U之争包含证据阈值差异；不能仅由旧参考S反推视觉判断必错。

**281711:original:f19**：门边确有下垂叶片，盆容器不清晰。旧U与模型S反映potted是否必须见盆的证据口径；保留参考不改标签。

**483723:original:f17**：近处坐着的人双手附近很小且受遮挡，手机候选不易识别。未识别到手机不足以证明整个相关区域可排除手机。

**32284:original:f21**：摩托车后方左侧是旅行拖挂/房车，右侧为厢式车；模型以大型箱体支持truck，是近邻交通类别混淆。

**110196:steer:f14**：画面可见两个标牌，但caption反复使用above/another；独立another sign命题的所指和是否新增第三块不明确。旧U不能直接当作没有第二块牌。

**22461:original:f4**：绿色盛葡萄容器呈敞口碗状；模型以cup-like container支持cup，未明确杯碗边界。旧H有根据，但应固定容器类别约定。

**22461:original:f7**：环状谷物可见，不存在可读品牌包装；外形类似Cheerios不足以确定品牌身份。模型将外形类别与具体品牌混用。

## 结论边界

出现的失败至少包含四种机制：真实视觉/细类误认、完整命题的数量与主体限定、指代和场景边界、旧参考证据标准争议。增加proposition_status能显式记录整句判断，但并不保证模型正确识别集合范围或观察到正确物体。

例如two men可能指谈话者子群，不能自动解释为全图恰好两人；two other umbrellas还要求把此前已提及对象排除。动作合成图中的多个人形位置也不自动构成多个不同主体。

本轮两种新条件使用相同恢复上下文，故可以比较整个proposition合同的变化；它同时改变了提示语义与输出schema（包括可见表示/装饰的解释），不能单独归功于一个新增字段。与旧名词片段版本的比较仅为历史对照。

无论是否超过旧参考90%，这里都不能宣布独立人工准确率达标。技术测试通过也不能替代语义测评。
