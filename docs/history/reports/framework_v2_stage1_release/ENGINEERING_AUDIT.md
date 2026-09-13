# E0/E1工程审计

最终实现位于 analysis_skeleton/framework_v2。测试结果见test_results.json，故障测试ID见fault_injection_report.json；原输入和旧结果来源见BASELINE_LOCK.json。

| 原问题 | 改进 | 测试证据 |
|---|---|---|
| reason:null会在startswith处使校验退出 | 在规范化前隔离字段类型错误；连接到同一坏ID的冲突也隔离 | ContractsTests；40条M2与20组M3保存响应完全一致 |
| M2非字符串ID可在duplicate集合计算时异常 | 先隔离坏结构，同时保留重复ID的冲突语义 | 非字符串字段、坏属性占用实体ID测试 |
| 图像准备在调用try之外，异常可能中断整批 | 输入/传输/解析/校验纳入请求边界；坏图和缺图留pending | TransportTests、GenericPipelineTests |
| 已完成请求不能恢复，缓存重复key会覆盖 | 校验身份及checksum，指定task_key选择来源，重复选择拒绝 | 完成恢复、响应保存后中断、未知结果、改输入、改repeat、篡改checkpoint测试 |
| 恢复时可能不清楚服务端是否已执行 | started无响应标outcome_unknown，默认不重发 | KeyboardInterrupt故障注入 |
| 固定20图runner依赖旧分解bundle | 通用pairs入口具备真实M2路径；缓存可选 | 新caption离线替身集成、缺caption、缺图、单claim失败后继续 |
| caption ID重复会在评价字典中覆盖 | 运行前和参考评价前检查caption唯一性 | duplicate_caption_id及duplicate_reference测试 |
| M2漏抽参考从生产分母消失 | 单独保留300条参考全集及missing状态 | reference_denominator_ledger.csv；缺事实、整文档失败的测试 |
| Macro指标难以说明更多U的代价 | 可决错误率含参考U上的错误确定；独立报告可决覆盖 | StabilityTests |

最终离线回归84项通过，网络被测试runner阻止；未调用付费模型。全链259个请求检查点严格replay及resume通过，新增调用0。合法保存响应的文档、对齐、词语、视觉回填和M6统计与repair_v1相同。

这证明本轮故障边界与计数实现符合已列测试，不等于任意输入都无错误，也不等于模型语义准确率提升。reason异常、缺图等技术失败不被改成视觉uncertain或hallucinated。
