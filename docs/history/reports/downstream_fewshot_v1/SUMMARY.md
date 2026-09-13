# few-shot 对照结论

新增每阶段8个few-shot演示，来自另外16条合成caption。原8条测试caption（4对）分别在0-shot/8-shot下独立重复3次，共6轮、92次API请求。DeepSeek思考模式关闭。Decomposer、既有事实、下游系统规则和校验器保持不变。

**本轮结果：few-shot改善了技术可用性和重复一致性，但还不能证明语义准确率达到要求。**

| 指标 | 0-shot | 8-shot |
| --- | --- | --- |
| 实体步骤通过结构校验 | 8/12 | 12/12 |
| 整对失败 | 4/12 | 0/12 |
| 事实对齐无需结构复核（ready） | 3/12 | 1/12 |
| 事实对齐 needs_review | 5/12 | 11/12 |
| 原始主线事实的技术回退率 | 93/234 = 39.7% | 30/234 = 12.8% |
| 跨轮双方成功且严格一致 / 全量事实比较 | 116/234 = 49.6% | 197/234 = 84.2% |
| 跨轮双方非技术失败时，严格一致率 | 116/124 = 93.5% | 197/201 = 98.0% |
| Coverage新增/轮 | 1、1、1 | 1、1、1 |
| 人工语义准确率 / F1 | 未评估 | 未评估 |

技术回退率分母为78条固定原始主线事实×3轮，不含Coverage新增或other。跨轮比较为3轮的三个两两组合，共78×3次事实比较；严格一致指状态及对侧完整事实签名一致。签名允许ID无关，但文字不同即算不一致，可能低估同义对应的一致性。成功且一致包括模型自己选择的语义ambiguous，所以必须结合其分布和具体错误看；不能将它称作正确率。

一个系统可以反复犯同一个错误。这里没有人工对齐gold，不能把自一致率改名为准确率。测试集已用于发现问题和设计新示例，属于开发集。不同pair/重复观察也不独立，不能由这些数字推断总体显著性。

## 案例检查

- 热狗：0-shot三轮都因实体单边行格式错误而整对失败；8-shot三轮均通过实体步骤。但“topped with”与“has ... on”被赋不同slot，事实对应仍被拒绝。这是可用性改善，尚非完整语义成功。
- 花瓶：8-shot将花瓶存在配为retained、干花/花和包含关系标为partial_overlap，减少粗暴modified；但glass已在实体fact中混入，是否满足“整条事实完全等义”仍需人工裁定。grasses的出处不唯一问题三轮都未解决。
- 长颈鹿：8-shot前两轮识别到相对位置描述有重合，但重复使用同一个Steer fact，导致校验回退；第三轮又出现close被判removed。说明关键语义边界尚不稳定。
- 鞋子：8-shot三轮都成功将worn判为removed，原引文失败改善；但木制事实的重复匹配导致材质对应被拒绝。这是一项退步，不能只展示改善案例。
- Coverage：两组每轮都只新增“The grass is tall.”，没有观察到few-shot带来的覆盖提升。dried等独立属性遗漏仍需检查。

## 工程检查和复现

106项本地测试通过；六轮冻结代码/提示词哈希一致；所有原始事实保持原样；每条事实恰好分配一次；522条验证记录全部pending；实际请求中0-shot为2条message，8-shot为18条message。没有任何视觉验证调用或测试后语义调参。

```powershell
.venv\Scripts\python.exe -m evaluation.run prepare --pairs outputs/downstream_v1/pairs.jsonl --output <新的运行目录> --shots 8
.venv\Scripts\python.exe -m evaluation.run execute --output <新的运行目录>
```

冻结的本轮完整配置在experiment.json；重新执行现有目录只恢复检查点，不算新的独立重复。各轮的中间JSON/原始请求/原始响应均在s0_r1等目录。

- [完整逐事实六轮对照](COMPARISON_REPORT.md)
- [机器可读指标](comparison.json)
- [新增示例及解释](../../evaluation/examples/README.md)
- [完整性检查](integrity_checks.json)
