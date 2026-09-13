# 三条规则版 Decomposer v3 测试报告

日期：2026-09-09。**已按用户截图完成改造；本批重复稳定性明显改善，仍有局部重复和共同遗漏。** 本次只处理 decomposer，未构建知识图谱、Verifier 或 Aligner。

## 改了什么

1. **Object 范围收紧。** meal、vegetable display、market setting/market、broccoli pile/pile 等聚合/场景名词不再计作 Object；screen、menu、hand、phone 等明确视觉实体保留。数量单位、空间关系不因其名词不单列 Object 而被删除。
2. **最小新增信息。** 固定静态模板把 `are placed throughout the scene` 与 `are throughout scene`、`is arranged in market setting` 与 `is in market setting` 规范为同一事实，合并来源并保存修改记录。否定、模态、正在放置、by-actor、方向和排列方式不随意抹去。
3. **覆盖检查移到本地。** 正常只做一次 DeepSeek 提取。spaCy noun chunks/依存 + 小型视觉名词表独立检查候选；明确肯定提及可由小规则补充，否定/假设/归属等仅记录警告。未知名词不自动等于 Object。取消第二次 LLM coverage review 和自由编辑。

完整说明：[decomposition/README.md](../../decomposition/README.md)。关键实现：[object_coverage.py](../../decomposition/object_coverage.py)、[normalizer.py](../../decomposition/normalizer.py)、[semantic_decomposer.py](../../decomposition/semantic_decomposer.py)。旧版代码/测试存档于 legacy/faithscore_v2。

## 工程与数据验证

- **22/22 本地测试通过**：包含截图中的两组去重、聚合对象排除、screen 补充、名词非对象、否定/假设/possessor 限制、混合句范围、can be seen、限定语、单请求、缓存完整性和禁止思考。
- 仍使用已有配置，DeepSeek 全程 thinking.type=disabled、temperature=0；未发送图片、真假标签或方法标识。
- 原 12 captions / 7 images 三次独立 API 提取，均绕过缓存。每轮 11 条完成、1 条重复 Palm 为 N/A，0 个 API 失败。实际调用分别 **14、14、15 次**，多于 11 的部分为提取协议错误的有限重试，不是第二次覆盖审查。
- 最后仅修正了本地范围检查：不能因后半句出现 `or` 就将前半句的 screen 判成范围不确定。随后用三组已保存响应离线复放到最终代码；**每条请求 messages 与录制请求逐字校验一致**，没有新增 API 调用，三组事实集与对应 API 运行相同。
- `final_run*` 保存真实网络运行；`checked_run*` 保存最终程序的离线复放，后者 api_calls=0，并记录 replay_of/source_api_calls。它们不是六次独立实验。当前代码/提示词 hash 已由报告脚本核验；无密钥代码快照见 runtime_snapshot。

## 三轮稳定性

分母为 11 条可拆分 caption；重复退化 N/A 单列，没有当作普通零事实。

| 比较 | 原始规范文本完全相同 | 原始文本 micro Jaccard | 有限等价规则后完全相同 | 有限等价规则后 Jaccard |
|---|---:|---:|---:|---:|
| 1 / 2 | 9/11 | 96.09% | 10/11 | 99.21% |
| 1 / 3 | 10/11 | 96.85% | 11/11 | 100.00% |
| 2 / 3 | 10/11 | 99.21% | 10/11 | 99.21% |

三轮同时原始文本一致 **9/11**；五类计数向量一致 **10/11**。

| 轮次 | Object | Attribute | Action | Relation | Count | 总事实 |
|---|---:|---:|---:|---:|---:|---:|
| 1 | 51 | 8 | 5 | 55 | 6 | 125 |
| 2 | 51 | 8 | 5 | 56 | 6 | 126 |
| 3 | 51 | 8 | 5 | 55 | 6 | 125 |

“有限等价”只使用两条明确列出的规则：`slice of lemon = lemon slice`；count 末尾的 exist/exists/are present 可省略。没有用另一个模型打分，没有全局合并 phone 品牌、主客体、否定或数量强度；**这不是完整语义准确率**。

上一版同批三轮原始文本同时一致为 6/11，计数向量为 8/11，Jaccard 74.31%–78.72%。本轮更稳定，但 Object 口径已经改变且反复使用了这批开发数据，不能据此声称未见数据准确率提升。

## 截图问题的直接验证

**历史失败结果离线回放，0 次 API：**

- 对 v2 的 `332570_vanilla_beam5` 和 `332570_vanilla_top_p`，本地规则均发现并补入缺失的 `screen exists`。后半句的使用意图/假设不再遮蔽前半句明确的 screen。
- 对 v2 蔬菜样本，删除 broccoli pile、lettuce pile、market setting、vegetable display 四个不应单列的对象；同义静态摆放关系合并。原数量单位及明确空间信息保留在 count/relation 中。
- 对 v2 餐盘样本，删除额外的 `meal exists`，保留刀叉、具体食物、白盘与柠檬切片。

回放记录：[historical_replay.json](historical_replay.json)。这是本地规则验证，不冒充新 LLM 运行。

**本轮真实提取：** 蔬菜样本三轮均为 18 条相同事实，Object 为 bicycle/broccoli/lettuce/person/potted plant 五类，fresh 保留，数量有 few people、several plants 和两种蔬菜的 pile 数量。静态摆放只保留一条表述。手机 screen 三轮均存在；未从 a person's hand 补出可见 person。

## 尚未解决的语义问题

1. `116887_vista_top_p` 的第 2 轮额外出现 `tennis racquet is in hand`，同时已有 `tennis player holds tennis racquet`，属于上下文中的重复关系。这是有限等价规则后唯一的跨轮差异，未静默删除以提高成绩。当前局部静态模板没有实现一般逆向关系去重。
2. 蔬菜长句三轮均漏掉 large display 的大小信息。Object 不单列 display 并不意味着其明确大小描述应自动删除；这是仍需处理的属性覆盖问题。
3. 冲浪板长句三轮均未保留“占据画面较大部分”的关系。稳定输出仍可能共同漏提，Object coverage 不能代替属性/关系召回评估。
4. 视觉词表与依存范围检查有限。未知词保留在 mentions 中，不强行补充；否定、假设等警告不自动代表错误。需在新样本上人工核查误补、漏补和指称问题。规则补的是 caption 的实体主张，不是图片真实性。

因此，本批可确认三条规则的目标行为和重复性改善，不能宣称整个拆分系统已经完全正确。后续应使用未见、按 image 分离的人工金标评估，不用缓存命中率或文本一致率替代语义覆盖率。

## 原有 19 条固定回归

严格文本匹配 **12/19**，实际 18 条完成处理、1 条退化 N/A。保留原期望，没有为本轮输出修改金标。

七条文本不匹配中：count/another/exact_count/lower_bound 涉及数量表达省略 exist（count 例还涉及 cats are / cat is）；clothing/contradiction 涉及单一衣物的简短指称 `uniform is white` / `sweatshirt is red`；hand 例是真正额外生成了 `tennis racquet is in hand`。这些差异逐项保留在 [metrics.json](metrics.json)，没有把 12/19 直接称作语义准确率，也没有将措辞不一致一律判作信息损失。

## 复核文件

- [逐条原文、共同事实及差异](CASE_REVIEW.md)
- [完整指标、有限等价规则与版本来源](metrics.json)
- [第 1 轮事实](../three_rules_v3_checked_run1/facts.csv)、[第 2 轮](../three_rules_v3_checked_run2/facts.csv)、[第 3 轮](../three_rules_v3_checked_run3/facts.csv)
- [本地覆盖警告示例](../three_rules_v3_checked_run1/object_coverage_warnings.jsonl)
- [原始 API 审计示例](../three_rules_v3_final_run1/audit.jsonl)

离线重算指标：

```powershell
.venv/Scripts/python.exe -m tests.report_decomposer --gold outputs/three_rules_v3_checked_gold --runs outputs/three_rules_v3_checked_run1 outputs/three_rules_v3_checked_run2 outputs/three_rules_v3_checked_run3 --output outputs/three_rules_v3_report/metrics.json
```
