# Alignment v1.1 离线回放

使用旧8-shot三轮已经保存的原始模型响应。没有重新请求模型；新提示词的效果未在本轮测试。旧输入、旧结果不修改。

| 轮次 | Pair | 旧校验状态 | 新校验状态 | 主对齐行 | 关联引用 |
| --- | --- | --- | --- | --- | --- |
| 1 | 415015 | needs_review | ready | 14 | 0 |
| 1 | 299573 | needs_review | ready | 13 | 0 |
| 1 | 581451 | needs_review | ready | 17 | 0 |
| 1 | 417586 | needs_review | ready | 15 | 1 |
| 2 | 415015 | needs_review | ready | 14 | 0 |
| 2 | 299573 | needs_review | ready | 13 | 0 |
| 2 | 581451 | needs_review | ready | 17 | 0 |
| 2 | 417586 | needs_review | ready | 15 | 1 |
| 3 | 415015 | needs_review | ready | 14 | 0 |
| 3 | 299573 | ready | ready | 14 | 0 |
| 3 | 581451 | needs_review | ready | 17 | 0 |
| 3 | 417586 | needs_review | ready | 15 | 1 |

## 具体变化

- 草：同一词多次出现不再否决明确的Steer新增；三轮均恢复added。Vanilla无草，Steer明确表达grasses。
- 番茄酱关系：topped_with与has_on不再因为名称不同被拒绝，三轮原模型提出的retained均通过程序。
- 木制关系：明确断言f3↔f4三轮均保留；带推测的f9保留关联引用及其语气，不重复算第二条retained。
- 长颈鹿：前两轮重复引用组成一个partial_overlap组，保留两条原侧事实与一条Steer事实的关联。没有将距离、并排布局和移动自动合并为相同语义。

## 未解决的语义问题

第三轮旧模型响应仍把稍后方→并排判modified、站得近判removed；离线回放不会重写模型语义决定。原事实中混入颜色/数量等限定的粒度问题也仍存在。ready只是新程序契约通过，不是人工语义准确。新版提示词已明确静态距离/布局/动作边界，但需要独立的新模型调用验证。

116项本地测试通过。全部12对回放的输入未变，每个fact仍恰好有一个主归属。保留旧数据可检查本次改善仅来自校验器调整。
