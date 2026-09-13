# v6 本地验证记录

- 版本：semantic-core-v6.0。
- 新增单元/集成测试：24 / 24 通过。
- 全部测试：80 / 80 通过（含旧版 56 项）。
- 命令：`.venv/Scripts/python.exe -m unittest discover -s tests -v`。
- 真实 caption 准备模式：`outputs/semantic_core_v6/prepare_smoke`；不读取密钥、不发送 API。
- 原有 API 配置未修改，思考关闭；真实语义生成通常 1 请求，顶层失败至多再试 1 次。
- 8 条助手编写示例全部通过字段/来源校验。
- 示例主类分布：{"entity": 24, "relation": 16, "attribute": 14, "other": 2}。
- 0-shot 系统提示词字符数：5090；8-shot：13555。

验证了类别映射、other 保留/不进入主线、数量单位及推测/否定文本不被程序更改、局部异常隔离、原文来源回填、JSON 截断/认证错误、有界重试、准备/续跑/导出。模拟传输测试不证明真实模型遵守规则。

本轮 DeepSeek 请求数为 0；未测语义 precision/recall、独立重复稳定性或视觉真伪。输出示例由助手标注再经程序归并，不标为模型预测。other_rate 只描述已提取元素的分流，不是原文完整覆盖率。
