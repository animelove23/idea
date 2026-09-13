# 双粒度文本分析与视觉事实验证：从描述收缩到有针对性的 steering

日期：2026-09-12。状态：研究规划，未运行新实验、未修改现有 pipeline。

## Problem Anchor
- 核心问题：保留 decompose → align，并接入参考FaithScore的多模态逐事实验证，以实体、属性和POS联合分析steering前后真实信息与幻觉的迁移，再用机制证据选择steer改进。
- 必须解决的瓶颈：长度差不能区分表达压缩、对象省略和对象仍在时的属性省略；抽取/对齐错误不能被记作模型语义消退。
- 非目标：不扩回动作/关系/数量全语义图，不建立复杂在线视觉核验系统，不直接外推总体生成能力下降，不预先决定所有细节都应恢复；对齐后离线多模态标记为当前必需步骤。
- 约束：复用本地 LLaVA-1.5 / COCO / Vanilla–VISTA 数据与 POS 代码；先小样本校准，再扩规模；当前任务是规划，服务器可用性与 GPU 预算尚未验证。
- 成功条件：得到可审计的双粒度变化数据、关键混淆因素对照及明确的继续/停止判据；只有证据支持时才开发一个最小 steering 改动。

## 本地证据与问题定位

已读三个根目录背景文档、decomposition/evaluation 当前 README、v1.3 规则与诊断、40图 FINDINGS、跨 decoding 分析和20对定性审查。

- 40图报告：7/40 对实体对应校验失败，总未解决 473/1217=38.87%；属性低保留率只能当线索，不能作为稳定真实损伤结论。视觉标签为助手初标。
- v1.3：3/30 对技术失败影响105/857事实；同一新参考下主线 Edge F1 92.02%→87.52%。工程复杂化尚未带来整体可靠性改善。
- 旧500图/解码报告显示大量缩短，也有 CHAIR 对象集合不变的缩短；“对象集合不变”并不等于属性不变。
- 20对定性样本已发现评价、推测、重复、细节省略和泛化共存；样本为分层挑选，不能拿其比例估计总体。
- 旧代码将空输出作为 early-EOS 的描述性代理。没有生成 trace 时，空白、停止字符串、解码清洗或 max_new_tokens 截断不能被确定为 EOS 原因。

## 技术主线与贡献边界

候选主论点：steering 的描述收缩可能由不同过程组成，其中“同一对象仍被表达但具体属性被省略”需要与对象整体退出、重复压缩和停止效应分开。

主贡献定位为对象条件下的细节变化诊断以及由诊断验证的一个干预；双粒度工具是支撑，不把“使用POS/原子事实”本身宣称为新颖贡献。

路线A（优先）：复用分析器，先证伪“仅长度/停止造成属性下降”，再选择单一小改动。路线B：在线完整语义计划器/视觉核验器，复杂度过高且改变当前问题，暂不选。

## 最小系统

```text
Vanilla / Steer 原文分别处理
   ├─ spaCy：原词、lemma、POS、字符偏移、句号位置
   └─ decompose：entity、attribute、原文证据
                  ↓
        align：实体对应 → 属性对应
                  ↓
     多模态逐事实标记 → 真假迁移 + 语义/POS交叉诊断
                  ↓
    长度/停止/同前缀干预 → 选定一个 steer 改动
```

### 语义边界

entity 指 caption 明确提到的对象/场景对象，不是 NER 人名识别。使用 caption 内局部实体锚点，重复提及同一对象合并为一个语义单位，但保留所有 mention。多个同类对象身份不清可保留集合锚点/unknown，不猜实例。

attribute 首批只做明确、单对象的颜色、材质、大小、形状、可观察状态（如 open/broken/wet）。动作 running、关系 wearing/holding/near、人数/count 及主观评价不纳入属性主指标。边界有疑问的状态保留 out_of_scope/ambiguous，不靠POS强行分配。

单独保存否定、明确推测语气及其作用范围；not red 与 red 不同。推测属性可以保留，但 asserted/speculative 分层，不根据是否视觉真实删文本。

范围外内容保存 source span，不用“未抽到entity/attribute”认定为无意义或冗余。第一版只主张范围内信息变化；“实体/属性不变”不能说全语义无损。仅用词汇重复指标也不能证明语义冗余。

### 数据合同

- token：caption_id, word_id, text, lemma, upos, char_start/end, sentence_id。
- entity：entity_id, canonical, mention_spans, mention_count, scope_status。
- attribute：fact_id, entity_id, slot, value, polarity, assertion, evidence_spans, value_spans。
- span必须回指原始caption，允许不连续片段；同时保存第一次出现位置和全部出现位置。
- POS来自原文 value_spans，不来自改写的fact句子；wooden/ADJ 和 made of wood/NOUN可表达同一material。一个语义事实可对应多个词，不能强行一一对应。

### 对齐和统计状态

保留 retained / removed / added / modified / unresolved。modified 仅确定同对象同槽位值变化；实体类别泛化/具体化保留方向子标签。对侧原文明确表达但未抽出 → unresolved/extraction_gap，不算removed。

属性在对象消失时记 removed 且 reason=entity_absent；对象保留时属性省略记 reason=attribute_omitted。实体对应不清时，依赖它的属性归未决；局部失败不能污染其他可判定对象。新增与修改单独统计，不能用前后数量差代替丢失量。

不增加第二个LLM coverage模块。用一套统一解析规则与人工抽查；自动校验 span/ID/字段，局部错误隔离。两边独立抽取，pair align 可看两边原文和事实；隐藏方法名称。

## 主指标

1. caption：word_len、model_token_len（有真实tokenizer/trace时）、sentence_count、空输出/重复退化/未知停止；POS绝对数和每100词频率并列，空文本密度N/A。
2. entity：等义保留、删除、新增、泛化/具体化、未决比例；同时报告提及次数和唯一实体数。
3. attribute：等义保留、删除、新增、值改变、语气改变、未决。
4. 核心指标 CAR：在实体确定仍对应的 Vanilla 属性中，等义保留数 / 全部此类原属性数。修改不自动当保留；分列值改变/语气改变。未决属性仍在分母，报告保留下界 K/N 和上界 (K+U)/N。
5. 分开报告对象消失伴随的属性删除、对象保留时的属性删除、未知对象对应下的属性数。CAR是条件描述指标，实体是否保留受steering影响，因此不能单凭CAR宣称因果选择性；同时报告全部原属性的无条件状态分布。
6. 原属性本身漏抽不在自动分母内：用独立原文人工标注估计召回，单独报告。以 image 为 bootstrap 单位，跨 seed/条件保持图片聚类；有零分母时N/A，报告宏/微平均和有效样本量。

## 三个核心实验块

### A. 建立可靠的现象图谱

先以旧20/30/40图作为开发/疑难案例，另取不重叠50对随机真实caption作冻结文本审核集。两名标注者若可用应独立标注后裁决；若只有单人必须如实报告。主审实体/属性抽取召回、removed precision、实体对应、跨度正确率、未决和整对失败。

暂定工程门槛（不是已有结果）：removed precision ≥95%，属性召回 ≥90%，未决 ≤10%，无静默整对丢失；置信区间过宽需补样本。门槛不替代对所观察效应的误差判断。重复20对3次估计输出稳定性，不用缓存充当稳定。

通过后扩到既有500图 greedy 全体，包含变长、等长、变短及异常；开发/审核过的图片只作探索结果，后续机制与方法确认使用新图片。再用 beam5/top-p 检查解码依赖。top-p 若缺多seed先只报单次描述结果。

分析六类可共存模式：范围内表达压缩、重复提及减少、实体整体退出、实体保留但属性省略、类别泛化/属性值或语气变化、后段内容缺失。后段缺失是文本模式，EOS/内容抑制是待验证机制，不做互斥“原因饼图”。范围外删减另列，不重新做全语义taxonomy。

### B. 区分停止效应与内容选择

1. 长度与位置：按Vanilla原始长度、属性首次出现绝对词位/相对词位、句子序号分层。补POS/slot分层，报告同一实体的局部上下文；不能以回归控制生成后长度宣称因果。
2. 长度对照：Vanilla机械截到Steer长度（边界被截断的事实不算完整）和用简洁prompt生成的Vanilla；二者仅为诊断参照，截尾不是自然压缩金标、prompt改变语义选择。独立留出确认使用预先固定长度预算，不按测试结果挑预算。
3. 固定同前缀诊断：同一图、同一原文prefix，steering开/关分别算 EOS margin 与目标实体/属性短语的条件log-prob。既看Vanilla前缀也看Steer前缀，分离终止前/后前缀；长短词组按subtoken平均，保留整短语概率作敏感性检查。不要比较两条自由生成轨迹同一t的logit当因果证据。
4. 内容概率显式条件化到 non-EOS，避免仅因EOS概率增加就把其他概率下降误叫内容抑制；比较属性与实体/功能词的匹配跨度或同义词组，单个词rank下降不是整个语义不再可表达。
5. 自由生成干预：标准Steer、统一减弱Steer、仅限制早期EOS（开发集固定策略）、终止概率校准对照。EOS实验记录原生token IDs、stop_reason、raw/processed logits、实际停止串及max_new_tokens；greedy为主，beam另外处理长度惩罚与搜索结束。
6. VISTA含VSV和SLA，先核对原实验实际启用组件。小样本做 baseline/VSV-only/SLA-only/full 以定位来源，不把所有改变都归给单个向量。

这些实验能支持特定设置下的干预效果，不能把几种因素的差值直接相加为完整因果分解。

### C. 一条机制、一种改动

优先验证的机制：实体保留时的属性省略，在停止控制后是否仍存在。

- 若主要是停止改变：先把终止控制作为最小改动/强基线，不将EOS分析本身宣称新颖。一个可复现的实验分布为 p*(EOS)=r_t，p*(w≠EOS)=(1-r_t)p_s(w|nonEOS)；r_t=sigmoid((1-gamma)logit p_0(EOS)+gamma logit p_s(EOS))，gamma在开发集固定。p_0和p_s在同一prefix、同图、同处理设置下计算；额外baseline前向和KV缓存要计成本。先greedy，处理多停止token时用集合概率推广。
- 若停止控制后仍有稳定的属性损失，并且同前缀nonEOS诊断支持局部抑制：再验证“仅在属性实现位置减弱steering”的oracle上限。oracle使用离线人工span，明确不可部署，不作为最终方法。
- oracle若有效，下一阶段才设计无未来信息的近似：当前prefix加候选短续写判断属性值是否依附已提实体，gate触发时将steering从alpha降到alpha_low。先做有限候选/完整词续写探针，测触发precision/recall、延迟与幻觉；不能把完整输出的POS或Vanilla未来事实当在线输入。阈值和候选规模须由开发集确定。此路线目前未验证可用，不包装成完成的方法。
- 若统一减弱steering已达到相同/更好效果，或停止控制完全解释差异：保留诊断结论，停止叠模块。若变化主要为表达/重复压缩，不设“恢复更多文字”的优化目标。

当前无新增训练组件。LLaVA冻结；DeepSeek只作离线抽取/对齐；spaCy离线解释，不声称未来POS已知。方法参数仅开发集选择，不能借审核过的测试结果调优。

## 必须产出的分析文件与图

| 产物 | 内容与用途 |
|---|---|
| protocol.md + frozen_split.json | 范围、状态、分母、图像隔离、配置与版本 |
| captions.csv | 原文、长度、POS、异常与真实可用的停止信息 |
| tokens.jsonl / units.jsonl | 原词与span、entity/attribute、重复mention和范围外文本 |
| alignment.jsonl | 对齐边、五状态、变化方向、失败原因和双方证据 |
| pair_metrics.csv | 每图净数量变化、gross增删、实体条件属性保留与上下界 |
| audit.csv + audit_report.md | 冻结人工文本参考、parser/align误差、未决、重跑稳定性 |
| mechanism_traces.jsonl | 新生成时才记录，同前缀EOS与nonEOS内容诊断 |
| casebook.html | 原文双栏高亮，12–20例含反例/不确定例，避免只挑最漂亮的损失样本 |
| findings.md | 每条观察绑定图表、替代解释、证据层级、下一步干预 |

主图：①长度保留比例×实体/属性保留（两面板，未决区间）；②实体退出伴随属性删减 vs 实体仍在的属性省略；③POS×变化状态（原词数量与语义单位分母分开）；④原始位置/预算匹配后的CAR；⑤同前缀EOS和nonEOS属性变化；⑥只在方法阶段画质量—信息量—成本对照。正文最终挑3张，其他留补充。

## 与近期工作的区别及风险

- VISTA官方实现把VSV与SLA分别暴露，应做组件消融：[official code](https://github.com/LzVv123456/VISTA)。
- SumGD已经做POS相关分析与选择性控制，单纯“按POS调steer”不能作为新颖点：[NAACL 2025](https://aclanthology.org/2025.findings-naacl.235/)。
- MESA已分析固定前缀EOS竞争及生成行为扰动，并提出选择性干预；“steering导致early EOS”不能作为核心新发现：[arXiv 2604.07914](https://arxiv.org/html/2604.07914v1)。
- 文件夹2609.01888论文已研究保守输出与信息量权衡，其限制明确包含未覆盖属性/关系幻觉。本计划的潜在区别是对象条件下的属性迁移和机制对照，尚未完成穷尽新颖性审核：[arXiv 2609.01888](https://arxiv.org/html/2609.01888v1)。

根据用户补充，对齐后即调用多模态模型，对全部可用实体/属性事实按图像支持性标记；视觉验证不再后置到最终方法验收。先用独立人工视觉审核校准，再报告真实保留/删除、幻觉保留/删除、修改与新增。词语层的取得方式、共享验证规则、三值标签和分母见文末新增合同；视觉模型判断仍不等同于人工金标。

## 节奏、预算与交接

先完成协议与50对文本审核，再完成500图文本分析，再决定100图量级机制试验，最后决定是否实现新干预。工作日粗估分别2–3、2–3、3–5天，不含人工排队和环境故障；不是硬承诺。

离线单对约2次独立decompose + 1次joint align（内部按实体→属性顺序），500对文本阶段约1500次逻辑API调用，重跑/审核额外计；新增视觉成本由对齐后的唯一待验事实数决定。现有旧v6结果可以作对照，不直接过滤成新版金标，因为两版覆盖率不同。

GPU时长不能由当前文本资料准确给出。先测20图吞吐，然后按生成次数×平均时长估算；同前缀双路径与oracle额外计。机制初筛按100图、4–6条件，三seed仅对随机解码；不全量展开所有轴。

确认性实验使用未参与旧分析/提示优化的新图片。最终比较至少包括 Vanilla、原Steer、统一减弱Steer、停止控制、所选局部改动；如果主张跨方法/模型普适，再补第二模型或方法，不凭LLaVA单例外推。

停止判据：解析误差与观察效应同量级；剩余属性差异在停止/预算对照后不稳定；oracle无效；部署gate收益不超统一减弱；或恢复仅提高字数/幻觉。均应缩小论点或停止方法开发。

## 统计与验证的具体约定

本节细化前述指标和执行顺序。

### 核对结果

现有greedy Vanilla/Steer原始文件各500行、各500个唯一image_id，两侧ID集合完全一致；Vanilla无空输出，Steer有1条空输出。两侧记录都只有image_id/caption，无法从原始结果恢复真实EOS、生成token数或logits。文件名标记VSV lambda=0.17、SLA层25/30及alpha=0.3、greedy和最大512新token；它们是配置线索，正式复现实验必须补运行命令/版本/配置核对。

### 主比较预先定义

当前500对只估计描述统计CAR及其不确定性，不做EOS机制判断。后续新生成预先固定主比较：标准Steer(S) vs 终止校准Steer(C)，Vanilla(V)作为同图参考。C的gamma在独立开发集选定并冻结，不在确认集挑结果最好者。

对图i、条件m，以V侧人工审核或自动提取的属性为参考；D_i^m为其实体确定在m侧仍有对应的属性，K_i^m为其中等义保留数，U_i^m为属性迁移未决数。总体微平均CAR_m=sum K_i^m / sum |D_i^m|；上界加sum U_i^m。主效应ΔCAR=CAR_C−CAR_S，是各条件下的条件描述差异，不是自然直接因果效应，因为D随输出变化。

必须并列两项敏感性结果：

1. 共同锚点集D_i*=D_i^S∩D_i^C，固定此集合比较两侧CAR；报告它覆盖全部V属性的比例。它仍是事后选择子集，不能据此代表所有实体。
2. 全部V属性上按原样保留/修改/对象退出伴随删除/对象在但属性删除/未决分类，分母固定，避免只在幸存对象上报告改善。

如果涉及实体类别改变，主体是否对应与类别是否等价分开记录；类别改变不会自动抹除主体对应，也不会自动证明对应。

固定主比较使用按image配对bootstrap的95%区间。未决带来Δ的识别区间[CAR_C下界−CAR_S上界, CAR_C上界−CAR_S下界]；分别bootstrap端点。抽取遗漏不在此区间覆盖内，另用50对独立原文审核的误差统计，并对同一审核集自动值与裁决值重算差异；做按长度、状态、方法分层的误差敏感性分析。审核样本不足或误差修正可翻转效应时，标为证据不足并补标，不宣布类别抑制。

探索性POS/slot/位置多重切片只产生假设；发现后在独立确认图像上只检验冻结主比较。至少要求效应区间排除0、未决和审核误差不会轻易翻转方向，才继续方法开发；这只是继续研究门槛，不是已成立结果。

### 机制块最小顺序

1. 现有文本：长度/位置/实体条件属性差异；不把空输出标为已知early EOS。
2. 新trace：greedy、同prefix开关steering、EOS及nonEOS内容分布；先核对真实配置，完整VSV/SLA消融仅小样本定位。
3. 新生成：标准Steer vs统一减弱 vs停止控制；必要时才做属性span oracle。只有oracle支持局部干预且能超过统一减弱，才研究部署gate。

### 逐条贡献区分

| 已有工作 | 已覆盖的论点 | 本计划允许的增量（待验证） | 禁止当作新发现 |
|---|---|---|---|
| SumGD | POS相关视觉依赖与选择性解码 | 同实体、同属性slot的保留/省略，并比较不同词性实现 | 首次用POS选择性控制 |
| MESA | steering扰动生成行为、fixed-prefix EOS竞争 | 终止控制后是否仍有对象条件属性省略，并以此决定是否需要局部改动 | 首次发现steering导致EOS偏移 |
| 2609.01888 | 幻觉分数与信息量/能力权衡 | 配对文本中的实体—属性迁移与反事实干预证据 | 首次发现保守生成与信息减少 |

三篇已核对页面链接见前文。差异表是有限范围文献核对后的研究定位，不等于系统性新颖性证明。

### 首批交付压缩

优先交付 protocol、units/alignment、pair_metrics、audit、findings 五组文件，raw captions与tokens为其追溯附表。casebook只是已有证据的浏览界面。先完成三张图：长度×范围内语义保留、属性删除的对象条件分解、原始位置×属性省略。logit图和方法对比图等对应实验完成后再产出，不画假数据。



## 用户补充后的词语与视觉标记合同

日期：2026-09-12。根据用户补充，视觉模型逐事实标记现在是主流水线必需步骤，不再仅作未来可选验收。当前仅更新规划，未运行标记。

## 1. 新主流程

caption → 独立decompose（entity/attribute）→ pair align → 多模态事实验证 → semantic type × transition × visual label；spaCy原词记录作为旁路，通过source span关联到事实。

参考FaithScore的描述性内容→原子事实→图像一致性验证范式。FaithScore本身不是Vanilla–Steer迁移评估，align及共享claim验证是本项目的组织方式。参考：[论文](https://aclanthology.org/2024.findings-emnlp.290/)、本地references/faithscore/src/faithscore/framework.py的stage3。

## 2. 词语层是什么

词语层是一张原始caption的词语记录表，不是第二套语义分解。它提供三种功能：测语言构成变化、定位信息在原文中的位置、把语义真假变化回连到具体表达。

| 字段 | 取得方法 | 用途 |
|---|---|---|
| token_id/text | spaCy token.i/token.text | 原词回溯；含标点，另存is_punct标记 |
| lemma | 配有lemmatizer的spaCy token.lemma_ | dogs/dog合并作词汇频次，不代表同实例 |
| upos | spaCy token.pos_ | NOUN/ADJ等词性统计 |
| char_start/end | token.idx及idx+len(text)，半开区间 | 原文高亮及与fact span匹配 |
| word_index | 程序给非空白、非标点token重新顺序编号 | 绝对词位置；不要混同token.i |
| sentence_id | spaCy句子划分后枚举 | 句首/句尾、前后句位置 |
| relative_position | (word_index+0.5)/非标点词数 | 前中后段切片；空文本N/A |
| lexical_count | 对小写text或lemma用Counter计数，注明口径 | 词面重复频次 |
| entity/fact_id | decompose原文span与词偏移相交关联 | 属于哪个对象/属性，非spaCy自动真值 |

spaCy字段参考：https://spacy.io/api/token 。当前decomposition/pos_parser.py只返回caption级POS计数和句数，尚未导出上述逐词表；这是后续实现要补的轻量记录功能。

lemma依赖NLP模型，错误可能发生；原词/偏移为确定性记录。不要把lemma当同义词归一器，也不要用同名词匹配不同人/物。

### 记录示例（约定schema，非已跑输出）

```json
{"caption_id":"v1","token_id":1,"text":"red","lemma":"red","upos":"ADJ","char_start":2,"char_end":5,"word_index":1,"sentence_id":0,"fact_ids":["f_color"]}
```

该例对应原文“A red car.”，属性事实为car.color=red，value_span=[2,5)，entity另有car的原文span。字段值例子仅说明格式。

## 3. 如何记录重复

词面重复：Counter统计，完全不需要LLM。输出中car出现3次就是3次词面提及，不能据此断言有3个车或有两次冗余。

实体重复：decompose为同一caption内确定同指的mentions保留同一个entity_id和全部source spans；如car/the vehicle/it确有共同指代，才能一起计mention_count。只要求清晰的局部指代；复杂多对象场景记未决，不加独立coreference模块。

事实重复：在同实体、同slot/value、同polarity/assertion的确定等义事实下保留多个原文证据，程序计数。不能用同lemma、同slot或近似embedding自动合并不同事实。“car is red”与“car is not red”必须分开。

重复不是首批主指标；保留词频和已有明确mention即可。不要为完整识别跨句语义重复重新堆解析模块。

## 4. 词语层具体分析

1. POS数量/每100词频次：并列显示ADJ/NOUN/VERB/ADP/功能词变化，不能由ADJ下降直接推出属性损失。
2. 事实首次及全部出现位置：查看属性删除是否集中在原文后段；重复事实取首次出现与末次出现作敏感性对照。
3. semantic type × POS × transition × visual label：例如“被视觉模型判为supported的颜色属性中，ADJ实现的删除率”。POS按属性value span标，多词事实可有多个POS；分母用唯一fact，交叉标签允许重叠，不能把多标签比例相加。
4. 同义改写控制：“wooden table”→“table made of wood”可能材质保留而ADJ→NOUN；由align决定等义，POS只解释表达改变。
5. 重复提及次数下降但唯一事实数不变，支持范围内重复表达减少；不是全语义无损结论。

无需做全词表Vanilla–Steer token强制一对一对齐。生成模型subtoken日志是后续机制实验的独立层，不与spaCy词语记录混用。

## 5. align后怎样视觉标记

### 构造verification queue

- retained：只有语义完全等价且主体确定对应时，构造shared claim验证一次，回填双方。缓存key含image、主体语境、完整命题、verifier/prompt版本，不跨图复用。
- removed：验证Vanilla事实，区分真实内容删除与错误内容删除。
- added：验证Steer事实，区分真实新增与新幻觉。
- modified：分别验证前后完整事实，得到supported→supported、hallucinated→supported等迁移；不是一个标签覆盖两个值。
- unresolved alignment：两边事实可各自验证，但不能凭视觉结果反推文本配对；迁移仍未决。抽取/结构失败独立保留，不伪装成视觉uncertain。

### 输入输出

输入：原图 + 完整原子命题 + 最小主体定位语境。不要只问“red是否正确”；应问“指定的这辆车是红色的”是否被图支持。定位语境不预设待验证属性为真，不把caption其他事实当视觉证据。隐藏vanilla/steer方法名、迁移状态与预期结论。

输出建议：

```json
{"claim_id":"c12","fact_ids":["v_f2"],"label":"supported","target_resolution":"resolved","reason":"车辆车身呈红色","verifier_version":"...","prompt_version":"..."}
```

label为supported/hallucinated/uncertain。supported要求主体及完整命题获图像支持；hallucinated用于明确不符或明确不存在；uncertain用于模糊、遮挡、身份难定位等证据不足。模型生成reason只是审核线索，不是独立视觉证明。不输出未经校准的confidence数字。

FaithScore本地stage3使用yes/no并转为1/0。三值标签是本项目为避免不确定项被硬算成假而提出的扩展，不能宣称完全复现原始FaithScore。原始实现里的宽松字符串匹配不直接照搬；要求解析明确枚举，格式错误保留为技术失败。

属性主指标采用完整命题口径：主体类别/身份本身不成立时，不能随意换成相似对象把属性判真。证据不足则uncertain；主体明确不存在则命题不受支持。先用校准案例统一口径。若希望研究“类别说错但对应视觉物体的颜色仍对”，须另设条件属性诊断，不能混入主计数。

speculative/polarity字段保留。明确肯定陈述作为主分析；推测声明另分层，并区分被推测内容的图像支持性与语言承诺强度，不能因may/might无法反驳就自动判supported。

## 6. 最终主表与指标

| 类别 | 真实保留 | 真实删除 | 幻觉保留 | 幻觉删除 | 真实新增 | 新幻觉 |
|---|---|---|---|---|---|---|
| Entity | 待实验 | 待实验 | 待实验 | 待实验 | 待实验 | 待实验 |
| Attribute | 待实验 | 待实验 | 待实验 | 待实验 | 待实验 | 待实验 |

modified另表列真假迁移，unresolved/uncertain另列数量及分母，不能从名册消失。明确标注“视觉模型判断”，经独立人工校准后才可估计标签可靠性；其输出本身不是gold。

主分析同时测真实删除率与幻觉删除率。对已判supported的原事实，总数N_T分解为保留/删除/修改/迁移未决；真实删除下界=T_removed/N_T，上界=(T_removed+U_T)/N_T。原事实视觉uncertain另报，其潜在真值不包含在这个条件区间内。幻觉删除同理；modified纠错另列，不混入简单删除。

对象确定保留时的真实属性保留率是重点切片，并列报告完整原属性分母和共同对象集的敏感性结果。新增真实信息/新幻觉必须一起看，避免仅恢复旧句子被当成进步。

可另报已判定事实上的supported/(supported+hallucinated)，并同时报告视觉判定覆盖率、真实事实绝对数、每100词真实事实密度和空输出比例。因三值标签、范围缩减和去重协议不同，这不是原版FaithScore；空输出或零事实的比例记N/A而非完美分数。

## 7. 最小执行与验收

先50对冻结文本审核集做decompose/align检查，同时抽取涵盖entity/attribute、各迁移状态与真假困难案例的独立视觉校准子集。视觉评审不得使用实验方法标签。若采用困难样本过采样，校准总体误差须按采样权重汇总，不用其频率推断总体。

通过后对500对所有可用事实执行视觉标记，包括removed/added/modified；同图shared claims仅验证一次。优先选择与被测生成器不同的视觉模型并固定版本；具体模型以可用环境、小样本核验准确性和成本决定，尚未选定，不假设任何候选天然可靠。

新增verification.jsonl、transitions.csv和visual_audit.csv。成本在原decompose/align之外再加Q个唯一claim验证工作项；Q由冻结对齐实际统计，批处理减少请求数但不减少需验证的事实数。未先跑真实API，不能给出确定费用。

前三张分析图调整为：长度变化×真实实体/属性保留；真实属性删除按对象退出/对象仍在分解；POS及原始位置×真假迁移。停止/logit实验仍用于解释机制，视觉标签不能单独证明因果。

已有两轮评审针对上一版文本规划，不自动覆盖本次新增视觉协议。本次是用户确认范围后的规划更新，不新增评审循环或模型实验。
