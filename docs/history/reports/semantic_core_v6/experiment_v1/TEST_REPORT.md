# v6 首次 DeepSeek 测试报告

**结论：8-shot 在小型合成验收句上表现良好，但真实长句仍有漏拆、合并事实及共同遗漏，尚不能据此宣称真实语义准确率达到 97.8%。**

## 执行与参考来源

- 模型：deepseek-v4-pro；官方 API；temperature=0；thinking=disabled。
- 33 次独立拆分 / 33 次实际请求，无重试、无网络失败；30 条 ready，3 条 needs_review。所有 33 条均返回可解析 JSON。
- 8 条新合成验收句属于 4 个相近的控制族，分别跑 0/8-shot；8 条既有真实 caption 跑 8-shot；3 条 caption 各额外重复 2 次；3 条同义改写。8-shot 示范和合成测试句无完全相同文本，但任务模板相近，不能当独立自然分布泛化测试。
- 8 条验收参考及 46 条主线原子事实 + 2 条 other 均在 API 前冻结。参考与评分审核均由当前助手完成，未经用户或独立人工审核。参考不发给 DeepSeek。
- 主指标：对程序产物做原子命题一对一语义匹配，再检查 coarse type；不是字符串精确匹配。一个合并事实最多获得一个主要命题 TP；存在、材质等未独立拆出会损失原子单元召回，即使信息以修饰语保留。原始字段错误导致的损失单列。
- 本轮生产代码、提示词和参考标注均未在看到结果后修改。语义审核映射公开在 semantic_review.json，源/预测摘要防止混淆。

## 合成验收：原子单元与主类联合匹配

| 类别 | 0-shot Precision | Recall | F1 | 8-shot Precision | Recall | F1 |
| --- | --- | --- | --- | --- | --- | --- |
| entity | 81.8% | 50.0% | 62.1% | 100.0% | 100.0% | 100.0% |
| relation | 100.0% | 78.6% | 88.0% | 92.9% | 92.9% | 92.9% |
| attribute | 100.0% | 78.6% | 88.0% | 100.0% | 100.0% | 100.0% |
| other | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| main_joint | 93.9% | 67.4% | 78.5% | 97.8% | 97.8% | 97.8% |

- 0-shot 主线 TP/FP/FN = 31/2/15，8-shot = 45/1/1。
- Attribute 的 8-shot 100% 只对应这 8 条简单合成句的 14 条属性（含 counting），不能与上一版真实 caption 的 Attribute F1 直接比较。
- 2 条 subjective/peaceful 均正确进入 other，未见这组验收中清晰主线事实被挪入 other；样本不足以校准置信度。
- 不检查 coarse type、只检查独立主要命题时：0-shot F1 83.5%，8-shot 97.8%。0-shot 的两条材料属性被标成 entity，是分类错误。

## 必须分开的两种评分影响

1. **程序标签约束**：c0/c1 零示例输出把狗/桌子的 category 写成 entity，而协议细标签只能是 animal/object 等。四条存在事实语义正确，却被存到 invalid_elements。它们没有丢失原文，也不是模型没理解。若仅在离线诊断中接受这四条粗类标签，0-shot 联合 F1 为 84.3%，而不是 78.5%。此诊断没有修改主成绩或代码。
2. **语气范围的参考选择**：原文 `A dog may be sleeping under a round table.`。冻结参考把 may 作用于 sleeping 和 under-table 两个命题；8-shot 将 under 写为 asserted，因此记一个 FP 和一个 FN。若人工裁定位置可作确定背景，成绩会改变；该项不应被包装成无争议模型错误。改写中也存在相同范围敏感性。

## 重复与改写

- 3 条 caption 各跑 3 次，9 个两两比较。忽略顺序/ID/细类、统一大小写标点后的主类事实措辞 F1 为 97.9%。这是措辞一致性，不是语义正确率。
- girl 短句与 shoes 长句各三次主线输出一致；长颈鹿长句产生 11/12/11 条主线事实，仍有属性增减。
- 3 组同义改写经助手语义核对，一致性 F1 97.1%；18 条原始主线事实中 1 条在改写后消失（5.6%）。缺失来自倒装 `Beside a bicycle stands a girl...` 中的 standing。
- `ceramic` / `made of ceramic` 被接受为同义，未按措辞不同扣分。狗的两种说法共同把位置断言为确定，因此一致不代表都符合冻结参考。
- 已知变化恢复：删除 green、改变 two/four 与 left/right、增加 not red 都恢复；may 范围变化只恢复 sleeping，未恢复位置的范围变化。按 added/removed 操作统计 TP/FP/FN=8/0/2，F1=88.9%。这些结果仅来自 4 组控制族。

## 真实 caption 回归：不能被简单句高分掩盖的问题

| 样本 | 观察 |
| --- | --- |
| 415015_vanilla | dried 只在 dried flowers 修饰语中出现，没有独立 Attribute；natural light illuminate the scene 被完全漏掉，未进入 other；include daisies and sunflowers 仍合成一条关系。 |
| 415015_vista | filled with flowers and grasses 合成一条关系；grasses 引用有两处匹配，因此标记来源待审。next to window 的附着选择为 table，原句本身有歧义，不能简单说它一定错。 |
| 299573_vanilla | 三次分别有无 grassy/tall 的独立属性变化；field is filled with tall grass 还混合了地点/容纳和高度，不是稳定的最小属性单元。三次均未独立列出 grass 存在事实。 |
| 417586_vanilla | old/worn 分开且保留 speculative；两对鞋、左右方位和木材保留。但 grassy 仍藏在地点描述中；主观/可能场景进入 other，不能把较高一致性当作完整覆盖。 |
| 581451_vanilla | green 已独立提取；likely napkin 以推测实体和同一性关系两种形式出现，身份信息仍可能重复计数。 |
| 299573_vista / 581451_vista / 417586_vista | 分别保留数量与站姿/空间、持有及配料、鞋的 pair 单位/左右/木材/黑色；这些是局部检查，不是完整人工金标 F1。 |

- 8 条真实 caption 共 86 条提取记录，其中 other 8 条（9.3%）；vanilla 为 7/54（13.0%），vista 为 1/32（3.1%）。分流比例受长度/内容影响，且两组解码设置不同，不据此推断 steering 的因果效应。
- other 不是完整覆盖检查：natural light 的共同遗漏不会自动反映在 other_rate 中。因此主线覆盖还需独立人工标注。

## 下一步优先处理

1. 接受不歧义的粗类 entity 标签，减少纯格式造成的假漏拆，并在新版本重新冻结。
2. 加强修饰语独立化与并列关系拆分示范；修复倒装句中动作的抽取边界。
3. 用真实 caption 的人工审核参考检查遗漏和 other 误分流，不能继续靠合成集 100% 属性分数验收。
4. 先裁定 may 的作用范围；同义改写稳定性需与真实覆盖同时达标。

## 文件

- [实际模型输出](MODEL_OUTPUTS.md)
- [冻结参考](REFERENCE_REVIEW.md)
- [逐条语义匹配审核](semantic_review.json)
- [语义指标](semantic_metrics.json)
- [结构、other 与措辞稳定性](structural_metrics.json)
- [CSV 指标](METRICS.csv)
- [冻结一致性检查](post_run_integrity.json)

API token 用量：prompt=87593，completion=13981。无图像、无验收参考标签外发。
