# 词语记录与对齐后视觉标记合同

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
