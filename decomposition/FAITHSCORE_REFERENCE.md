> v3 更新：用户进一步要求三条规则；已取消下文 v2 的第二次 LLM 覆盖审查，改为本地名词短语候选检查、小规则补充与警告。当前流程见 README.md。下文保留论文参考与 v2 设计来源，不代表 v3 仍有自动模型审查。

# FaithScore 参考与实现差异

参考论文：Liqiang Jing, Ruosen Li, Yunmo Chen, Xinya Du. FaithScore: Fine-grained Evaluations of Hallucinations in Large Vision-Language Models. Findings of EMNLP 2024, 5042–5063. https://aclanthology.org/2024.findings-emnlp.290/

本地论文：`论文集/2024.findings-emnlp.290.pdf`。核对了第 3.2 节（印刷页 5045–5046）、第 4.1 节的原子事实修订说明、附录 L 的 Figure 15/16（5062–5063），并检查原文渲染。

官方代码：https://github.com/bcdnlp/FAITHSCORE

锁定 commit：`52179e5cfd3721b017132c5d90c1a639c5627480`。只下载阅读了 framework.py、prompts、README 和 LICENSE，保存在 references/faithscore；没有执行或安装该仓库，也未加载其视觉模型。原仓库 MIT 许可随参考文件保存。

## 借鉴

- 描述性与分析性子句的区分：避免把常识解释、意图和主观分析当作图像事实。
- 按类别明确列出原子事实：避免依赖全段自由列表。
- 最小独立事实与衣物属性分离：原始源码示例将 jacket / bow tie 与穿着关系分开，颜色与其他属性另列。
- 论文人工标注阶段的事实修订：删除重复/非原子项、修正表述并补充遗漏。

## 主动调整

| FaithScore | 当前 decomposer |
|---|---|
| 先 [D]/[A] 标记，再生成事实 | 一次提取请求中显式记录句子 scope、排除原文及五类事实；审查仍读完整原文 |
| entity/relation/color/count/others | object/attribute/action/relation/count；活动与关系分开，颜色并入 attribute |
| 人工事实修订用于标注质量 | 增加自动覆盖审查与原文证据，但它不能替代人工金标 |
| 行标题/句点切分解析 | 严格 JSON、每句覆盖检查、编辑事务校验 |
| call_openai 中无限重试循环 | 每阶段次数有界；保留失败和待审，不空集兜底 |
| 图像事实验证和最终 FaithScore | 当前不实现；truth/change 留空，后续模块独立处理 |

覆盖审查和程序协议校验是本项目的新增设计，不是声称官方代码已经实现的功能。当前自然语言提示词和模块为本项目重新编写；参考源码仅存档，不在运行时导入。论文报告的模型/相关性结果不能移用于当前 DeepSeek 实现。

## 稳定性边界

小范围程序规则覆盖 holding/wearing、隐含归属、摄影效果、显式支撑物对象、部分数量线索等已定义情形。它们拒绝明显不合规输出并请求修正，不直接生成新事实，不进行任意语义去重。规则只覆盖明确定义的模板，仍可能漏掉复杂绑定、同义重复或更深的语义遗漏。

复测补充了静态陈列的 relation 归类和 close-up 近景的覆盖提示。跨句重复删除必须引用原文，并由事务中仍保留的同类同断言候选支持；仅接受相同规范文本或不含否定/模态的 action + on 补语前缀，不能用任意跨句证据删除事实。此检查只批准审查模型提出的删除，不自行开展全局语义合并。

二次审查曾在开发测试中错误增添归属/框架对象，因此不能以审查次数当作质量保证。所有开发运行保留，并在 release 测试中独立测量覆盖与重复性。
