# entity-facts-v4 本地验证

本次替换模型输入/输出协议、实体与事实校验、结构化精确去重、缓存指纹、checkpoint 和导出，以及标注模板。API 配置保持原位置，thinking 强制 disabled；旧缓存不兼容本版指纹。

测试：`.venv/Scripts/python.exe -m unittest discover -s tests -v`，33 项通过。其中 31 项为结构、引用、语气保留、实例区分、失败隔离、缓存、导出与续跑验证；2 项使用实际 spaCy 做 caption 层 POS 回归。API 客户端测试使用本地注入响应，不联网。

另对已有 12 条研究 caption 执行了真实 CLI `--prepare-only`：12/12 prepared、0 failed、0 API calls，结果保存在 `outputs/entity_v4_prepare/`。这仅验证输入、POS 和新版请求准备；decomposed=0、pending=12 是预期状态，不是模型拆解结果。

用户网球示例通过校验：4 实体、9 事实。新结构示例另有同类双实例与模糊数量/推测边界演示。所有示例是待人工确认草稿，不算新增人工金标准；模板与 few-shot 来自规则示范，不作为准确率测试集。

这些测试不证明语义准确率上升。原文片段匹配不能证明事实蕴含正确，引用合法不能证明指代正确；分类、覆盖率与原子性仍需人工评估。下一轮应使用用户的人工标注，按图片隔离提示示例与测试数据，再进行关闭思考、绕过缓存的独立重复测试。跨样本实体 ID 不能直接比较。

此次不运行旧版按类别自动补物体或平面 fact 文本评估器，不把缺失实体编号靠猜测补齐。旧实现和测试已归档到 `legacy/three_rules_v3/`，旧实验输出保留。未来 Verifier/Aligner 尚未实现；本版只预留 verification 并允许独立校验器读取后续状态。
