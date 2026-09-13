# FaithScore-inspired decomposer v2：实现与测试

日期：2026-09-09。**工程改造完成；复杂 caption 的自动语义稳定性未通过验收。** 当前适合审计和小规模人工复核，不能把输出直接当作已验证的主实验测量值。

## 实现范围

只修改 decomposer 与必要输入、审计、测试接口。参考 [FaithScore 论文](https://aclanthology.org/2024.findings-emnlp.290/) 与 [官方源码](https://github.com/bcdnlp/FAITHSCORE)，按总体实验目标采用：完整上下文 → 描述/分析范围记录及五类原子事实 → 带原文证据的覆盖审查 → 有界校验修补 → 保守规范化、缓存与审计。

保留 object/attribute/action/relation/count、caption 级 POS、数量单位/下界、否定、限定语和必要指称。穿着与衣物颜色分开；不增加实体 ID、token anchor、POS 事实绑定或隐含归属。Verifier/Aligner 未实现，truth/change 留空。普通样本通常两次调用；错误反馈有界，未解决问题不发布部分事实。

论文原始类别是 entity/relation/color/count/others；自动覆盖审查与程序校验是本项目新增设计。没有运行论文仓库或借用论文分数作为本模块成绩。详见 [来源与差异](../../decomposition/FAITHSCORE_REFERENCE.md)。

## 最终版本与验证方法

- 本地自动测试：**36/36**。覆盖来源、事务编辑、限定语、空/重复状态、缓存、盲化、禁用思考、有限重试、静态分类及近景覆盖。
- 固定合成回归：19 条，期望预先写在 fixture；属于开发回归集，不是未见金标。
- 真实数据：此前授权的 12 captions / 7 images，独立完整运行三次，均 `--bypass-cache`。
- 使用已有 API 配置；实际返回模型 `deepseek-v4-pro`；请求全部 `thinking.type=disabled`、temperature=0、JSON 模式。只传 caption、来源句、候选及审查依据；未传图片、method/decode、真假标签。
- 四个最终目录协议完全相同，代码和提示词 hash 与当前实现相符，全部完成。离线脚本已检查这些条件。运行代码及提示词另存于 [runtime_snapshot](runtime_snapshot)，未复制密钥配置。
- `ready/success` 只表示流程及已有程序规则通过，不代表语义完整。退化样本虽然 CLI 以非零退出提醒待审，其语义状态是 not_applicable，不是 API 错误。

## 最终结果

| 数据 | 完成处理 | 退化 N/A | API 失败 | 事实数 | API 调用 |
|---|---:|---:|---:|---:|---:|
| 合成回归 19 条 | 18 | 1 | 0 | 66 | 34 |
| 真实第 1 轮 | 11 | 1 | 0 | 123 | 26 |
| 真实第 2 轮 | 11 | 1 | 0 | 129 | 25 |
| 真实第 3 轮 | 11 | 1 | 0 | 128 | 25 |

合成回归严格文本匹配 **18/19**。唯一差异：期望 `surfboard is on ground`，实际 `another surfboard is on ground`。原句确实描述另一块板；这是保留指称的表述差异。没有修改期望或放宽评估来变成满分。

| 无缓存重复比较 | 完全相同事实集 | type + 规范文本 micro Jaccard |
|---|---:|---:|
| 第 1 / 2 轮 | 8/11 | 78.72% |
| 第 1 / 3 轮 | 7/11 | 74.31% |
| 第 2 / 3 轮 | 6/11 | 77.24% |

三轮同时完全一致 **6/11**；五类数量向量同时一致 **8/11**。Jaccard 不包含局部 ID 和顺序，但同义改写仍算不同；这些不是语义准确率。

| 轮次 | object | attribute | action | relation | count |
|---|---:|---:|---:|---:|---:|
| 1 | 50 | 7 | 4 | 56 | 6 |
| 2 | 53 | 7 | 4 | 59 | 6 |
| 3 | 51 | 7 | 4 | 60 | 6 |

attribute/action/count 数量相同不能证明正确；下面有三轮共同遗漏的反例。

## 具体通过项与未通过项

**网球样本 `116887_vista_top_p`：** 三轮相同的 10 条事实。`wears uniform` 与 `uniform worn by tennis player is white` 分开；黄色球拍、手、持拍、球和 `prepares to serve` 均保留，没有把准备发球变成正在发球，也没有增加 hand belongs to player。

**马群样本 `54627_vista_greedy`：** 三轮同为 11 条，保留至少四匹、吃草、分布、远近和树旁。跨句重复删除的证据误拦截已修复；修改仍需原文与被保留候选支持。

**蔬菜长句 `352478_vanilla_greedy`：语义验收失败。**

- 原文 `fresh vegetables` 在三轮 initial.excluded 中均被标为 subjective；审查均未恢复。若按本研究的可见状态属性口径，fresh 应保留为 caption 的属性主张，真假另由 Verifier 处理。当前范围筛选有过度过滤风险，不能称作“稳定提取正确”。
- 第 1 轮审查删除了原文 `arranged in a market setting` 对应的关系，理由是 not_in_caption，但引用的正是该短语。证据字符串存在并不能证明编辑正确。
- 第 2/3 轮同时留下 `potted plants are throughout scene` 和 `potted plants are placed throughout the scene` 等同义关系；审查把已有信息当作 missing 再添加。
- 三轮 object 为 6/9/7，relation 为 9/12/13；pile/display 是否单独计对象、摆放与数量如何避免重复，仍有粒度漂移。静态摆放错归 action 已消除，但没有解决全部原子性问题。

**手机长句：覆盖验收失败。** `332570_vanilla_beam5` 原文明确有 screen，三轮都保留 `menu is on screen` 却缺少 `screen exists`。`332570_vanilla_top_p` 则仅第 2 轮漏 screen。近景、前景、占据画面等仍保留，但对象覆盖检查并不完备。共同遗漏不会在重复性指标中暴露。

**冲浪板 `43324_vanilla_beam5`：** 三轮均保留数量下界、坐姿、shirtless 与穿红衣的原文矛盾。第 3 轮 action 为 `man is sitting on ground`，同时另有 on-ground relation，存在复合动作与关系重复承载的问题；another 的保留差异则需要区分指称与纯措辞。

**餐盘 `561517_vanilla_top_p`：** 三轮保留刀叉、白盘、柠檬切片和食物；第 2 轮额外加入 `meal exists`，违反当前泛类/具体类口径。`lemon slice` / `slice of lemon` 属于同义变化，不能解释成切片信息丢失。

**退化 `332570_vista_beam5`：** 三轮均在本地识别重复 Palm，0 次 API、语义 N/A；未当作普通空事实或全部信息被删除。短文本中的 Palm/Palm Palm 指称仍需结合原 caption 人工复核，不能仅凭大小写和重复词猜实体身份。

上述失败原因中，过度范围排除、重复添加和错误删除有审计记录直接支持；模型对前阶段结果的依赖、同模型审查的相关错误，是合理机制解释，但本次没有专门消融来证明因果。

## 如何使用这些结果

改造解决了输出结构、可追溯性、若干固定分类和工程复现问题；**没有证据证明自动语义稳定性已经达标或整体优于旧版**。之前 validated 开发轮 Jaccard 为 84.3%–89.5%，之后为修补静态分类和共同遗漏改变了提示词；最终指标如上，未挑选最好的一轮发布。

当前先用于人工复核与冻结事实集。保留全部困难样本和退化状态，不通过取交集或删样本提高一致率。缓存只能冻结某次输出，不能修正其遗漏。后续主实验需要按 image 分离、含长短配对的人工金标，分别测提取前后审查的漏提、过提取和类型错误；尤其核查长 vanilla 与短 steered 的差异性误差，防止拆分器误差被误报成 steering 信息损失。

初始 scope/excluded 与审查 edits 在不同阶段记录；不要将初始排除片段直接当成经人工确认的最终排除统计。本报告没有实施 Verifier、Aligner 或正式 steering 效应估计。

## 复核入口

- [完整逐条原文与三轮差异](CASE_REVIEW.md)
- [机器可读指标、协议 hash、逐样本计数和事实](metrics.json)
- [第 1 轮事实表](../faithscore_v2_acceptance_run1/facts.csv)、[第 2 轮](../faithscore_v2_acceptance_run2/facts.csv)、[第 3 轮](../faithscore_v2_acceptance_run3/facts.csv)
- [第 1 轮完整审计](../faithscore_v2_acceptance_run1/audit.jsonl)、[第 2 轮](../faithscore_v2_acceptance_run2/audit.jsonl)、[第 3 轮](../faithscore_v2_acceptance_run3/audit.jsonl)
- [合成严格回归结果](../faithscore_v2_acceptance_gold/gold_evaluation.json)
- [模块说明](../../decomposition/README.md)

离线复核命令（不调用 API）：

```powershell
.venv/Scripts/python.exe -m tests.report_decomposer --gold outputs/faithscore_v2_acceptance_gold --runs outputs/faithscore_v2_acceptance_run1 outputs/faithscore_v2_acceptance_run2 outputs/faithscore_v2_acceptance_run3 --output outputs/faithscore_v2_acceptance_report/metrics.json
```
