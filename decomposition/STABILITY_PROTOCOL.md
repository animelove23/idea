# entity-facts-v4 测量边界

执行协议为 prompts/entity_facts_v4.txt 与 schemas.py。旧三规则协议已归档到 legacy/three_rules_v3/decomposition/STABILITY_PROTOCOL.md。

分别报告结构合法率、人工实体/事实精确率与召回率、类型/语气/数量强度正确率，以及无缓存重复输出的语义一致性。不得把缓存一致性或 JSON 合法率当准确率。跨 caption、跨独立运行的局部实体 ID 不可直接比较，必须先明确实例对应关系；未实现这种匹配前不输出伪语义稳定性分数。

人工标注按图片分组划分 few-shot 与测试，避免同图 vanilla/steer 跨集合泄漏。助手示例不是人工金标准。caption 层 POS 单独统计；decomposition 阶段 verification=pending。测试详见 ENTITY_SCHEMA_TEST_REPORT.md。
