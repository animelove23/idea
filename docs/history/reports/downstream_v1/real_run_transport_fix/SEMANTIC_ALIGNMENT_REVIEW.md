# 原句、实际对齐结果及语义审查

以下“系统结果”来自已保存的真实运行；“审查意见”是助手基于原文的初步判断，不是用户审核后的 gold，不计算准确率。未修改模型结果、原始事实或提示词，也未追加 API 请求。

基本标准：①对应的是同一个对象或明确一致的集合；②retained 保留完整事实的数量、作用范围、语气和否定；③modified 必须是同一对象同一窄语义槽位的变化；④removed/added 必须检查完整对侧原文，不能把同义、漏拆或部分重合算作删除；⑤每个事实有可追踪状态，技术回退与语义模糊分开。other 仅展示，不入主线。

`—` 只表示系统没有配对的 fact，不表示对侧原文一定没说。以下保留每一条最终 alignment；失败回退的单边行不人为合并。

## 415015｜花瓶与花

**Vanilla 原句**

> The image features a vase filled with a variety of dried flowers, including daisies and sunflowers. The vase is placed on a table, and the flowers are arranged in a visually appealing manner. The vase is positioned near a window, allowing natural light to illuminate the scene. The combination of the vase, flowers, and the window creates a pleasant and inviting atmosphere.

**Steer 原句**

> The image depicts a glass vase filled with various types of flowers and grasses. The vase is placed on a table next to a window. The flowers and grasses are arranged in such a way that they create a visually appealing bouquet.

**实际系统结果**

| Vanilla fact | Steer fact | 最终状态 / 原因 | 审查意见 |
| --- | --- | --- | --- |
| f1 [entity] There is a vase. | f1 [entity] There is a glass vase. | modified / value_changed | 不满足原子级统计要求：vase 的存在仍保留；glass 已另有新增属性。整条 entity 再标 modified 有重复计算材质变化的风险，现有混合粒度宜标待审查。 |
| f2 [entity] There are dried flowers. | f2 [entity] There are flowers. | modified / value_changed | 不宜直接通过：花仍存在，dried 的限定被省略，没有新的干湿状态值。应区分实体保留与干燥属性缺失；现有事实未独立拆开，宜按粒度问题审查。 |
| f3 [entity] There are daisies. | — | removed / not_expressed | 基本满足：Steer 只写 flowers，不能由上位类别推定仍明确表达 daisies。 |
| f4 [entity] There are sunflowers. | — | removed / not_expressed | 基本满足：Steer 没有明确表达 sunflowers，泛称 flowers 不等于保留具体花种。 |
| f5 [entity] There is a table. | f4 [entity] There is a table. | retained / same_fact | 满足：两侧均明确表达桌子存在。 |
| f6 [entity] There is a window. | f5 [entity] There is a window. | retained / same_fact | 满足：两侧均明确表达窗户存在。 |
| f8 [relation] The dried flowers include daisies and sunflowers. | — | removed / not_expressed | 删除具体种类包含关系基本合理，但原事实同时包含两个花种，仍有上游粒度和重复统计问题。 |
| f9 [relation] The vase is placed on the table. | f8 [relation] The vase is placed on the table. | retained / same_fact | 满足：同一花瓶与桌子、同一放置关系。 |
| f12 [other] The combination of the vase, flowers, and the window creates a pleasant and inviting atmosphere. | — | removed / not_expressed | 合理的范围外记录：Steer 没有该氛围描述；other 不进入主线。 |
| — | f6 [attribute] The vase is made of glass. | added / not_expressed | 满足：Vanilla 未表达玻璃材质，Steer 明确表达；应避免与 entity modified 重复解释同一变化。 |
| f7 [relation] The vase is filled with dried flowers. | — | ambiguous / alignment_validation_error | 拦截合理但未完成对齐：两边都表达花在花瓶内，另有 dried 限定消失及 grasses 新增；不能把整条关系视为完全不同或同对象简单换值。 |
| f10 [relation] The vase is positioned near the window. | — | ambiguous / alignment_validation_error | 拦截合理：原文/现有事实主要对象为 vase，Steer 现有事实为 table，不能直接 modified；Steer 原句修饰附着也值得人工检查。 |
| f11 [other] The flowers are arranged in a visually appealing manner. | — | ambiguous / alignment_validation_error | other；拦截了参与对象变化造成的不可靠 modified。未完成细粒度语义对应，不进入主线。 |
| — | f3 [entity] There are grasses. | ambiguous / alignment_validation_error | 技术性保守回退，不是语义无法判定：grasses 在 Steer 明确出现，按两侧文本很可能应 added；出现多次造成 source 不唯一不等于实体不明确。 |
| — | f7 [relation] The vase is filled with flowers and grasses. | ambiguous / alignment_validation_error | 同 o:f7：有共同关系内容及额外参与对象，需要 partial_overlap/granularity 审查。 |
| — | f9 [relation] The table is next to the window. | ambiguous / alignment_validation_error | 同 o:f10：桌子靠窗与花瓶靠窗不能只因谓词相近而 modified。 |
| — | f10 [other] The flowers and grasses are arranged in such a way that they create a visually appealing bouquet. | ambiguous / alignment_validation_error | other；存在共同审美描述，但参与对象/范围不同。保留待审查，不进主线。 |

**本对是否满足基本标准：部分满足，整对不通过。基础对象及简单关系能对应，但 entity 中混入材质/状态，造成 modified 与属性变化重叠；包含关系和靠窗关系未安全完成对齐。**

被拒绝的模型提议（区别于上表最终状态）：

- ['f7'] → ['f7']，模型提出 modified，程序拒绝原因：retained/modified require same ordered global participants。
- ['f10'] → ['f9']，模型提出 modified，程序拒绝原因：retained/modified require same ordered global participants。
- ['f11'] → ['f10']，模型提出 modified，程序拒绝原因：retained/modified require same ordered global participants。
- [] → ['f3']，模型提出 added，程序拒绝原因：unresolved source requires ambiguous status。

## 299573｜长颈鹿

**Vanilla 原句**

> The image features two giraffes standing in a grassy field, with one giraffe positioned slightly behind the other. They are both facing the same direction, possibly looking at something in the distance. The giraffes are standing close to each other, creating a sense of companionship. The field is filled with tall grass, providing a natural habitat for the giraffes.

**Steer 原句**

> Two giraffes stand side by side in a grassy field.

**实际系统结果**

| Vanilla fact | Steer fact | 最终状态 / 原因 | 审查意见 |
| --- | --- | --- | --- |
| f1 [entity] There are two giraffes. | f1 [entity] There are giraffes. | retained / same_fact | 存在性对应可理解，但不能称为整条事实完全等义：原 fact 还包含 two。数量已有独立 count 属性，需避免混合粒度。 |
| f2 [entity] There is a grassy field. | f3 [entity] There is a grassy field. | retained / same_fact | 满足：两边都描述 grassy field；属性在独立字段也被保留。 |
| f3 [attribute] There are two giraffes. | f2 [attribute] There are two giraffes. | retained / same_fact | 满足：两边明确为 two giraffes，数量和计数对象一致。 |
| f4 [attribute] The field is grassy. | f4 [attribute] The field is grassy. | retained / same_fact | 满足：grassy 属性保留。 |
| f5 [relation] The giraffes are standing. | f5 [relation] The giraffes are standing. | retained / same_fact | 满足：standing / stand 同义，主体相同。 |
| f6 [relation] The giraffes are in the grassy field. | f7 [relation] The giraffes are in the grassy field. | retained / same_fact | 满足：长颈鹿在该草地中的位置关系保留。 |
| f7 [relation] One giraffe is positioned slightly behind the other. | f6 [relation] The giraffes are side by side. | modified / value_changed | 有条件合理：同一对动物的相对布局从稍前后变为并排；但没有逐只对应，且稍前后与并排可能兼容。不能仅凭同一宽泛 spatial slot 就断定修改，建议人工裁定。 |
| f8 [relation] Both giraffes are facing the same direction. | — | removed / not_expressed | 基本满足：side by side 不必然表示朝向相同，不能补充同向的语义。 |
| f9 [relation] The giraffes are possibly looking at something in the distance. | — | removed / not_expressed | 满足：Steer 未表达看向远方，也未表达该推测。 |
| f10 [relation] The giraffes are standing close to each other. | — | removed / not_expressed | 不满足直接判删除的标准：side by side 与 close to each other 有明显共同的邻近语义。Steer 的 f6 已用于另一条 modified，需要联合处理粒度/部分重合，不能因无法再配对就判 removed。 |
| f11 [other] The giraffes create a sense of companionship. | — | removed / not_expressed | other；Steer 没有 companionship 描述，不进主线。 |
| f12 [attribute] The field is filled with tall grass. | — | removed / not_expressed | 待审查：Steer 的 grassy field 保留了有草的语义，但没有 tall/filled 的全部强度；整条直接 removed 容易抹去共同信息，应考虑 partial_overlap。 |
| f13 [other] The field provides a natural habitat for the giraffes. | — | removed / not_expressed | other；未表达 habitat 解释，不进主线。 |
| cov_f1 [attribute] The grass is tall. | — | removed / not_expressed | 满足：tall 是独立限定，Steer 未表达高度，删除合理；与 f12 的 bundled tall 存在计数重叠，须单列上游粒度问题。 |

**本对是否满足基本标准：部分满足，整对不通过，即使运行状态是 ready。主要问题是 close 被误判删除，以及一对一分配与复合位置描述冲突；数量和 tall 有上游事实粒度重叠。**

## 581451｜热狗

**Vanilla 原句**

> The image features a hot dog with a bun, topped with ketchup and green peppers. The hot dog is placed on a piece of paper, which is likely a napkin. The hot dog is positioned in the center of the image, and the peppers are scattered around it, adding a colorful and appetizing touch to the dish.

**Steer 原句**

> A person is holding a hot dog with ketchup and peppers on it.

**实际系统结果**

| Vanilla fact | Steer fact | 最终状态 / 原因 | 审查意见 |
| --- | --- | --- | --- |
| f1 [entity] There is a hot dog. | — | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| f2 [entity] There is a bun. | — | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| f3 [entity] There is ketchup. | — | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| f4 [entity] There are green peppers. | — | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| f5 [entity] There is a piece of paper. | — | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| f6 [entity] There is a napkin. | — | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| f7 [relation] The hot dog has a bun. | — | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| f8 [relation] The hot dog is topped with ketchup. | — | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| f9 [relation] The hot dog is topped with green peppers. | — | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| f10 [attribute] The peppers are green. | — | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| f11 [relation] The hot dog is placed on the piece of paper. | — | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| f12 [relation] The piece of paper is likely a napkin. | — | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| f13 [relation] The hot dog is positioned in the center of the image. | — | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| f14 [relation] The peppers are scattered around the hot dog. | — | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| f15 [other] The peppers add a colorful and appetizing touch to the dish. | — | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| — | f1 [entity] There is a person. | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| — | f2 [entity] There is a hot dog. | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| — | f3 [entity] There is ketchup. | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| — | f4 [entity] There are peppers. | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| — | f5 [relation] The person is holding the hot dog. | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| — | f6 [relation] The hot dog has ketchup on it. | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |
| — | f7 [relation] The hot dog has peppers on it. | ambiguous / stage_failed | 技术失败：没有事实对齐响应，不能评价该对应语义是否正确。 |

**本对是否满足基本标准：未完成，不能判为满足。实体响应将 paper 与 napkin 合在一个 original_only 行，违反接口约束，导致事实步骤未调用。全部 stage_failed 是技术回退，不代表22条事实语义真的模糊。**

仅作为审查方向、不是系统输出：hot dog、ketchup 和 topping 关系应有可比内容；person/holding 可能新增，bun、paper、green 限定等可能删除。paper 与 speculative napkin 的身份及语气应保留，不能凭常识合并。

## 417586｜长椅与鞋

**Vanilla 原句**

> The image features a wooden bench with two pairs of shoes placed on it. The shoes are positioned close to each other, with one pair located towards the left side of the bench and the other pair on the right side. The bench appears to be made of wood and is situated in a grassy area, possibly a park or a garden. The shoes seem to be old and worn, suggesting that they have been used for a long time.

**Steer 原句**

> The image depicts two pairs of shoes resting on a wooden bench. One pair of shoes is positioned on the left side of the bench, while the other pair of shoes is on the right side. Both pairs of shoes are black in color.

**实际系统结果**

| Vanilla fact | Steer fact | 最终状态 / 原因 | 审查意见 |
| --- | --- | --- | --- |
| f1 [entity] There is a bench. | f2 [entity] There is a bench. | retained / same_fact | 满足：bench 存在保留。 |
| f2 [entity] There are shoes. | f1 [entity] There are shoes. | retained / same_fact | 满足：shoes 存在保留。 |
| f3 [attribute] The bench is wooden. | f4 [attribute] The bench is wooden. | retained / same_fact | 满足：wooden 材质保留。 |
| f4 [attribute] There are two pairs of the described shoes. | f3 [attribute] There are two pairs of the described shoes. | retained / same_fact | 满足：数量为 two，单位为 pairs，而非两只鞋。 |
| f5 [relation] The shoes are on the bench. | f5 [relation] The shoes are on the bench. | retained / same_fact | 满足：resting on / placed on 在此都表达鞋在长椅上。 |
| f6 [relation] The shoes are positioned close to each other. | — | removed / not_expressed | 基本满足：分居左/右不等于距离相近，Steer 未明确表达 close。 |
| f7 [relation] One pair of shoes is located towards the left side of the bench. | f6 [relation] One pair of shoes is on the left side of the bench. | retained / same_fact | 满足：通过左侧位置匹配对应的一双鞋，不只按 shoes 类别匹配。 |
| f8 [relation] The other pair of shoes is on the right side of the bench. | f7 [relation] The other pair of shoes is on the right side of the bench. | retained / same_fact | 满足：通过右侧位置匹配另一双鞋。 |
| f9 [attribute] The bench appears to be made of wood. | — | ambiguous / partial_overlap | 保守合理但不可当作新增发现：原文同时有 asserted wooden 和 speculative appears to be made of wood；Steer 只保留 asserted。已有木制事实已被配对，此条是重复内容加不同语气，ambiguous 比直接 removed 更稳妥。 |
| f10 [relation] The bench is situated in a grassy area. | — | removed / not_expressed | 满足：Steer 未描述 grassy area。 |
| f11 [other] The grassy area is possibly a park or a garden. | — | removed / not_expressed | other；未表达 park/garden 推测，不进主线。 |
| f12 [attribute] The shoes seem to be old. | — | removed / not_expressed | 满足：old 的推测被省略，不与新增 black 合成 modified。 |
| f14 [other] The shoes suggest that they have been used for a long time. | — | removed / not_expressed | other；未表达长期使用推断，不进主线。 |
| — | f8 [attribute] Both pairs of shoes are black. | added / not_expressed | 满足：两双鞋均 black 是新增颜色信息，保留 both 的作用范围。 |
| f13 [attribute] The shoes seem to be worn. | — | ambiguous / alignment_validation_error | 语义上未完成：Steer 确实没说 worn，原文 old and worn 明确承载该推测；模型 proposed removed 基本合理，但伪连续引文校验失败。最终 ambiguous 属于格式/证据失败。 |

**本对是否满足基本标准：大部分满足，仍未完全通过。实体、数量、左右关系、old 删除与 black 新增都合理；worn 证据格式失败，木制的重复/语气差异仍需审查。**

被拒绝的模型提议（区别于上表最终状态）：

- ['f13'] → []，模型提出 removed，程序拒绝原因：evidence must be from that caption。

## 总体判断

本轮没有一对可以不经审查就作为完全正确的语义对齐 gold。鞋子对最接近要求；长颈鹿对虽通过结构校验，仍有实质语义问题；花瓶对存在混合粒度与对象混淆；热狗对为接口失败。

工程完整性（不改原事实、每条事实有且只有一个状态）已满足，完整语义对应标准尚未全部满足。不能把28条主线 ambiguous 都解释成原文本身不确定；其中包含技术回退。
