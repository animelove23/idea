# 最终3图端到端冒烟测试的M2复核

## 结论

未发现M2集成代码路径与独立测评不一致。端到端使用的同一6条caption在之前40条测评中本来就是较难子集，联合F1为80.77%，不是全40条的88.51%。本次该子集重跑为81.55%；不能把不同样本范围的88.51%与81.55%解释为集成后下降。

| 相同6条caption | 联合F1 | 实体F1 | 属性F1 | 匹配/预测/参考事实 |
|---|---:|---:|---:|---:|
| 正式M2的owner_final子集 | 80.769% | 77.273% | 100% | 42/50/54 |
| 端到端smoke | 81.553% | 78.161% | 100% | 42/49/54 |

两次匹配的参考事实集合完全相同：实体34/46、属性8/8，共42/54。12条参考未匹配也完全相同，额外预测从8条变成7条。属性100%仅指这8条参考属性，不代表全部开发集或真实总体准确率。

## 身份与代码路径核验

- 6/6的原文及发送给模型的audit.input完全相同。
- 6/6的模型、官方目的地、温度、thinking、max_tokens、重试数、8-shot数、prompt_sha、shots_sha、final_code_sha及追加规则哈希完全相同。两次均请求并返回deepseek-flash。
- 6/6的smoke原始checkpoint经过normalize_final离线重放，与bundles中的规范化文档逐字段完全一致。
- 正式M2与smoke的check_frozen均通过，代码、规则和示例没有冻结后漂移。
- 6/6原始JSON响应不完全相同，响应ID均为独立调用。差异主要是提及范围、词形、excluded记录与实体ID编号；5/6的计分结果完全一致。不能要求temperature=0在不同服务端调用中逐字重现，但本次没有证据指向客户端路径错误。

## 唯一影响分数的变化

565761_original正式M2输出了other people对应的person实体，smoke漏掉它。由于旧参考写people且固定计分器不将person/people合并，原实体被计为额外预测，遗漏后预测数12→11、匹配数仍9，因此该caption联合F1从75.0%变为78.26%。

这不是可解释的语义改善：other people在原文明示，smoke实际漏抽了一个实体，固定命名口径却让分数提高。这是一次可观察的覆盖波动，也说明不能把候选参考符合度直接等同于真实准确率。

## 保持不变的问题

- 303499_original：people/rider命名不匹配，horse仍合并群体，漏对应的两个子群。
- 303499_steer：red仍正确归coat，black/brown仍归不同horse；person/rider与public area漏抽未解决。
- 316617_original：三人、三个frisbee、两个handbag仍正确分开，但woods仍漏。
- 316617_steer：两个shirt及red/white归属稳定正确；参考people群体与模型两个人冲突，wooded area仍漏。
- 565761_original：man引用范围/群体口径、attire遗漏和people命名问题仍在；smoke另外漏掉了原先输出的other people。
- 565761_steer：两次参考匹配均9/9，仅chair/bench/cup等单复数输出变化，lemma计分后相同。

本审阅未调用API、未修改代码、参考或指标。机器可复核的逐条身份、响应哈希、分数与匹配集合保存在M2_SMOKE_REVIEW.json。
