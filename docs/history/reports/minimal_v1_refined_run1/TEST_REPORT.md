# Minimal Decomposer v1 修改与测试报告

当前实现已按八张截图收缩为五类事实、caption 层 POS、两张研究主表。DeepSeek 思考始终关闭。格式和固定回归测试通过，但真实长句仍有遗漏与措辞波动，尚不能称为完全稳定。

## 实现变化

- API 每条事实仅 id/type/fact；类型仅 object、attribute、action、relation、count。
- 移除 subtype、entity_id、主谓宾结构、token anchor、事实 POS、双模型 POS 比较、隐含关系补全和复杂语义去重。
- 对象存在性按类；another 用至少两个表达；穿着为 attribute，holding 为 relation；坐姿与位置分别提取。
- 默认每条单次提取；重试限错误恢复；独立两轮作为测试，不因字面差异拒绝整条。
- facts.csv 严格六列；truth/change 留空。captions.csv 独立记录五种 POS 计数。
- 配置沿用原本本地配置，未修改 API 密钥。历史代码归档到 legacy/semantic_v2，历史输出保留。

## 测试结果
| 检查 | 结果 |
|---|---|
| 本地测试 | 15/15 通过（含真实 spaCy、禁用思考、隔离退化输入、断点续跑、六列表） |
| 固定例句最终回归 | 12/12 符合预期；10 次真实 API 调用；空文本和重复退化不调用 |
| 真实样本 | 已授权的同批 12 条、7 张图片；无新增研究样本 |
| 最终真实第一轮 | 11 success，114 facts；0 failed；1 needs_review |
| 最终真实第二轮 | 11 success，112 facts；0 failed；1 needs_review |
| 请求 | 每轮 11 次；所有 finish_reason=stop；thinking=disabled，temperature=0 |
| 完全一致事实集合 | 6/11；忽略 ID、顺序、大小写、空白和末尾句号 |
| 严格文本 micro Jaccard | 99/127 = 77.95%；同义改写也算差异，不是语义准确率 |
| 可复核性 | 两轮与最终固定例句的代码 hash、提示词 hash 均匹配当前实现 |

fixed gold 含计数、another、重复餐具、服装、准备动作、主观空集、否定、推测、手持、矛盾、空文本、重复退化。这是预先编写的开发回归集，不是未见测试集。

最初简化提示词的固定回归为 9/12，收紧规则后为 12/12。初版真实文本一致性为 8/11、81.98%，修订后为 6/11、77.95%；修订增加了事实覆盖，同时增加了输出变化。因此不能宣称整体重复稳定性已经提升。保留初版输出供追溯。

## 原来四条失败的现状

| 样本 | 修改后 |
|---|---|
| 43324_vanilla_beam5（冲浪板） | 两轮都是 15 条事实，完全一致；surfboard exists 一次，at least two surfboards exist；保留坐姿和穿红色卫衣 |
| 561517_vanilla_top_p（餐具） | 两轮都是 14 条事实；fork/knife 各一个存在性事实；仅关系措辞不同，仍有 lemon slice 粒度问题 |
| 116887_vista_top_p（网球） | 两轮都是 9 条事实，完全一致；白色球服、黄色球拍、准备发球、手持关系均保留，无 hand belongs to player |
| 332570_vista_beam5（Palm 重复） | 两轮都 needs_review；本地识别 256 次重复，不调用 API、不当成正常零事实样本 |

## 残留问题与原因可能性

以下为对源 caption 和两轮输出的文本抽查，不是图片真假验证。

- **352478_vanilla_greedy**：实质遗漏：第二轮没有提取 two piles of broccoli exist / two piles of lettuce exist；其余差异主要是单复数。两轮均还输出 vegetables/vegetable 泛类，未严格遵循排除已有子类对应泛类的约定。
- **332570_vanilla_greedy**：关系措辞与方向变化：screen contains menu / menu is on screen；smartphone displays screen / screen is on smartphone 并非严格等价。两轮均漏掉原文 phone is open（原文 open 的含义也有歧义），字面一致性不能检测共同遗漏。
- **332570_vanilla_top_p**：phone fills middle of scene / Palm Treo smartphone is in middle of scene，后一表述弱化 fills 的占据程度。两轮均未单独保留手占据大部分画面的描述。
- **54627_vista_greedy**：some horses are further away / some horses are further from camera，结合原文主要是措辞差异。
- **561517_vanilla_top_p**：关系 positioned/placed 可省略，主要是措辞差异；但两轮都将 lemon slice 简化为 lemon，存在切片形态损失。餐具存在性各保留一次，无虚构 diner 或 delicious 属性。

可能原因：长句的覆盖要求仍会与原子化、类级去重规则竞争；自然语言 fact 没有唯一表述，即使关闭思考、temperature=0，独立调用仍会出现不同分解。两轮还可能共同遗漏同一事实，一致性不能代替准确性审查。当前版本把这些问题保留在原始输出和差异报告中，没有通过补隐含事实或复杂合并来掩盖。

该系统现在适合继续做小规模语义审查。下一步应针对长句建立独立人工金标，评估覆盖率/误提取率；不能直接把结构 success 当作可发布的语义准确率，也不能将范围外的主观/场景信息记作 steering 删除的幻觉。

## 两张结果表

[Caption Table](captions.csv) · [Fact Table](facts.csv) · [逐条机器差异](repeatability.json) · [人工抽查](manual_review.json)

下列原失败样本输出来自最终第一轮，未经人工修补。

### 43324_vanilla_beam5

In the image, a shirtless man is sitting on the ground next to a surfboard. He is wearing a red hooded sweatshirt and appears to be resting or taking a break from surfing. The surfboard is positioned in front of him, occupying a significant portion of the scene.

In the background, another surfboard can be seen leaning against a wall, further emphasizing the surfing theme of the image.

| type | fact |
|---|---|
| object | ground exists |
| object | hooded sweatshirt exists |
| object | man exists |
| object | surfboard exists |
| object | wall exists |
| attribute | man is shirtless |
| attribute | man wears red hooded sweatshirt |
| action | man is sitting |
| relation | man is next to surfboard |
| relation | man is on ground |
| relation | surfboard is in background |
| relation | surfboard is in front of man |
| relation | surfboard leans against wall |
| relation | surfboard occupies significant portion of scene |
| count | at least two surfboards exist |

### 561517_vanilla_top_p

The image features a delicious meal consisting of french toast, fries, and salad on a white plate. The plate has a knife placed alongside the food, and a fork is positioned on the left side. A slice of lemon can be seen on the right side of the plate, adding a refreshing touch to the meal. A fork and a knife are also visible within the image, indicating that the person enjoying the meal will likely use them for cutting and eating.

| type | fact |
|---|---|
| object | fork exists |
| object | french toast exists |
| object | fries exist |
| object | knife exists |
| object | lemon exists |
| object | plate exists |
| object | salad exists |
| attribute | plate is white |
| relation | fork is positioned on left side |
| relation | french toast is on plate |
| relation | fries are on plate |
| relation | knife is placed alongside food |
| relation | lemon is on right side of plate |
| relation | salad is on plate |

### 116887_vista_top_p

A tennis player in a white uniform with a yellow tennis racquet in hand prepares to serve the ball.

| type | fact |
|---|---|
| object | ball exists |
| object | hand exists |
| object | tennis player exists |
| object | tennis racquet exists |
| object | uniform exists |
| attribute | tennis player wears white uniform |
| attribute | tennis racquet is yellow |
| action | tennis player prepares to serve ball |
| relation | tennis player holds tennis racquet |
