# M2 唯一候选参考分歧

样本：397351_steer。原句片段：`appears to be selling these vegetables at a market`。

DeepSeek输出market实体，并将整段放入action排除项；候选参考将market置于推测作用域内，未收入肯定实体。

这是范围判断/参考边界待审，不能仅凭字符串分数断定真实场景中是否存在market。当前参考明确排除推测命题，因此本轮照冻结答案计为1个额外实体；不事后修改分数。

尚需审核：appears的作用域是否包含地点存在；实体vegetables与其carrots/radishes子类的重叠提及是否符合所需信息计数。后者在模型和候选参考中一致，因此F1不会揭露协议自身的潜在重复计数问题。

原始响应、候选参考和评分均保留。下一轮若更改范围规则或示例，必须独立命名实验，不覆盖本轮。
