# 拆分系统真实 API 测试报告

测试日期：2026-09-09。配置使用用户填写的 `deepseek-v4-pro`，API 根地址为 `https://api.deepseek.com`；未修改用户密钥或模型配置。

## 结论

Caption → DeepSeek facts → spaCy POS → CSV/JSONL 的真实调用链路已跑通。
六条输入中，五条产生 62 条通过结构校验的事实；一条退化文本返回空事实，被保守地标为失败/待人工复核，没有把它当作“零信息损失”的成功样本。

当前结果可用于检查管线和完善协议，尚不足以冻结 prompt 或开始最终研究统计。六条 caption 均来自 image_id=332570，覆盖六组实验配置，仅涉及一张图片，不是有代表性的质量评估集。

## 逐组结果

| 方法 | 解码 | 词数 | 事实数 | 状态 |
|---|---|---:|---:|---|
| vanilla | greedy | 70 | 16 | 结构校验通过 |
| vista | greedy | 11 | 5 | 结构校验通过 |
| vanilla | beam5 | 91 | 17 | 结构校验通过 |
| vista | beam5 | 256 | — | 空事实，待人工复核 |
| vanilla | top_p | 67 | 18 | 结构校验通过 |
| vista | top_p | 16 | 6 | 结构校验通过 |

本次成功输出涉及 object=22、attribute=9、action=3、relation=18、subjective=10；真实试运行尚未覆盖 count 和 scene，二者仅在本地 schema 测试中覆盖。

## 已完成验证

- 29 项本地回归测试通过，包括新增的思考模式参数测试。
- 六条 caption 均保留来源标识；原始文件未提供 token_len/eos_step，导出保留为空。
- 62 条事实的复合 ID 唯一、token 引用有效、字符偏移对应原文、POS 与 spaCy token 逐项一致。
- `facts.csv` 与 `decomposed.jsonl` 中事实内容一致；`truth` 和 `change` 全部为空。
- API 用户消息仅包含 caption 与 token 的 id/text，不含方法标签、图片、POS 或真值。
- 在临时副本上验证续跑：五条成功 checkpoint 保持字节级一致且没有再次进入拆分器，仅失败样本进入离线探针，facts.csv 不变。该续跑测试没有网络请求，也没有修改原始 API 结果。

## 本轮发现及处理

### 1. V4 思考模式需要显式配置

最初未指定思考模式，首条请求长时间未保存结果，随后主动中断。该次远端调用是否已消耗 token 无法从本地判断，旧运行记录保存在 `../decomposition_pilot/`。

查阅官方说明后，新增可选 `thinking` 配置与 `--thinking` 参数，省略配置时默认 `disabled`；开启时不发送无效的 temperature 参数，模式写入运行指纹。用户原有 API 配置保持不变。

当前目录是显式 `--thinking disabled` 的独立试运行，共保存 8 次 API 响应：五条成功样本各一次，退化样本三次。已保存响应的耗时累计 36.781 秒，usage 累计报告 26,318 tokens；不包含前一次中断请求的未知消耗。

依据：[DeepSeek Thinking Mode](https://api-docs.deepseek.com/guides/thinking_mode/)：V4 默认开启 high 思考，思考模式下 temperature 不生效。

### 2. 重复 Palm 文本被正确送入复核

`332570_vista_beam5` 原文是 256 个重复的 `Palm`，三次均返回 `{"facts": []}`，不是网络或鉴权错误。
当前非空 caption 的零事实规则使其留在 `failed_samples.jsonl`，避免在后续分析中将退化生成直接视为无事实。没有根据图片或其他方法的 caption 猜测 Palm 是手掌、品牌或其他对象。

后续应明确制定退化生成的人工处理规则；不应为了提高接口成功率而强制生成存在事实。

### 3. holding 分类不一致，prompt 尚不能冻结

- vanilla greedy 的 f4、vanilla top_p 的 f4 将 `holding` 标为 `action.interaction`。
- vista greedy、vanilla beam5、vista top_p 中相同持有语义标为 `relation.possession`。

这违反了当前 prompt 中 holding 使用 relation 的约定。结构校验仅检查类别是否合法，无法保证同类语义跨样本的一致性。本轮未以词面硬编码自动改写类别，也未覆盖原始模型响应。

### 4. 核心 token 粒度仍需统一

vanilla greedy 的 f3/f13 将 `person` 与所有格 `'s` 一起作为 possession 的核心 token，可能把对象名词引入 relation 的 POS 统计。
前景关系有时仅引用 `foreground`，有时引用 `in, foreground`。这类差异是核心词选择协议问题，不能解释为 steering 引起的真实语言学差异。

### 5. spaCy POS 存在个别明显误标

vanilla top_p 的 `Palm Treo smartphone` 中，原始 token 11 的 `smartphone` 被 spaCy 标为 VERB。系统忠实回填了该标签，映射逻辑本身无误。
如后续以 POS 做辅助统计，需抽查专有名词和片段文本，评估是否改用更强的英文 pipeline；本轮没有把误标手工改成 NOUN 来掩盖问题。

## 下一步范围

先统一 holding、所有格、空间关系核心词的示例协议，再扩展到不同图片的 100–200 条人工抽查，并补充 count、scene、否定、指代和不确定表达。此次未进行全量调用，也未进入真实性核验或 vanilla/VISTA 事实对齐。

## 结果文件

- `facts.csv`：62 条事实。
- `captions.csv`：六条 caption 及长度/来源。
- `decomposed.jsonl`：五条成功拆分的完整审计信息。
- `failed_samples.jsonl`：退化样本及三次空事实响应。
- `review.md`：逐条原文、事实、核心 token 与 POS，便于人工核查。
- `validation_report.json`：导出一致性与 token/POS 自动检查结果。
- `resume_validation.json`：使用临时副本完成的离线续跑验证。
