# 实验说明与复现边界

## 输入和控制变量

沿用已有 LLaVA-1.5 greedy baseline／VISTA 成对输出，文件名标识 seed=1994、max_new_tokens=512、VISTA lambda=0.17、层 25/30、logalpha=0.3。不是本次重新生成的 caption；缺少完整生成轨迹，stop_reason/EOS 保持 unknown。

从 500 对共同 image ID 中排除视觉 few-shot 的 5 张图片：3501、8775、54627、212603、275717。用 seed=20260912 从剩余 495 对选 400 对。共有 47 张与历史开发样本重叠，不能称为独立 holdout。图片使用 COCO 2014 val2014；附加官方 trainval2014 annotations 与 CHAIR 数据准备兼容，但本框架输出不是 CHAIR 分数。

输入文本及选择记录：[selected_text_pairs.jsonl](../results/coco400_final_v1/selected_text_pairs.jsonl)、[selection.json](../results/coco400_final_v1/selection.json)。下载脚本校验下载范围、归档并以 CRC 检查解压文件。官方镜像：

- [val2014.zip](https://s3.amazonaws.com/images.cocodataset.org/zips/val2014.zip)，SHA256 `fe9be816052049c34717e077d9e34aa60814a55679f804cd043e3cbee3b9fde0`。
- [annotations_trainval2014.zip](https://s3.amazonaws.com/images.cocodataset.org/annotations/annotations_trainval2014.zip)，SHA256 `031296bbc80c45a1d1f76bf9a90ead27e94e99ec629208449507a4917a3bf009`。

## 实验阶段

| 阶段 | 本阶段变化 | 新模型调用 | 矩阵可分类 / 400 |
|---|---|---:|---:|
| 原 Final v1 | 冻结 M2/M3/M5，首轮端到端 | 5682：M2 800、M3 400、M5 4482 | 187 |
| A_scope_only | 限制问题传播范围，保持全部模型响应 | 0 | 219 |
| B_alignment | 身份与描述变化分离，重跑 M3 | 400 | 195 |
| B2_local_and_rebinding | 局部隔离冲突；拆开不安全的旧视觉共享标签 | 0 | 203 |
| C_reviewed | 定向复核和拆分后独立视觉验证 | 506：418 次复核／相关主体审查＋88 次新绑定 | 269 |

不要把分步可分类数理解为模型准确率曲线：B 改了对齐契约，B2 拆分旧共享标签会暂时增加缺失。A/B/B2/C 保持相同输入文本和原 M2。第一版探针失败与中断批次另列开发历史，未混进正式 400 对。

## 指标定义

- **长度**：spaCy 去除空白及标点后的词数。变化为 steer−original；缩短比例为 `(original−steer)/original`，原词数为零时不能直接相除。400 对中 395 变短、1 不变、4 变长；总词数 35191→16951，减少 51.83%。这是词数，不是生成器 token 数。
- **核心矩阵**：按 shorter/same/longer 分层，真实支持事实 S 与幻觉事实 H 分别分为 unchanged/gained/lost/mixed。必须从对齐的增删事件判断，不只比较净数量；增加和丢失同时存在就是 mixed。
- **不确定边界**：枚举未决事实允许的方向，只有所有合理补全给出同一状态才入确定单元格。未决单独计数，不当作 0、不随意丢弃。矩阵 fraction 分母是该长度层全部样本，包含未决。
- **成分**：entity-S/entity-H/attribute-S/attribute-H 的保留、增加、丢失、修改出入。属性删除再区分主体保留／主体删除；泛化和具体化保留独立事件，不能当成新增独立物体。
- **词语侧**：POS 净减少、相对原词数的贡献、提及次数减实体数的重复代理量。POS 是组成证据，不能替代关系标注，也不能证明因果机制。
- **工程和准确性**：技术未决、语义未决、视觉 uncertain、父子冲突、调用数分别报告。reference agreement/F1 依赖参考质量，不能等同独立人工准确率。

## 最新结果与限制

最终可分类 269/400（67.25%），未决 131。entity-S、entity-H、attribute-S、attribute-H 可分类分别 341、317、328、343。M3 原始响应的语义未决 655→349，技术未决 111→214；后者是尚未解决的回归。最终统计 summary 的技术影响事实数 279 额外包含局部 M2 依赖，不能拿它替换原始 M3 的 214。

原 330 个视觉 uncertain 唯一命题中：74→supported，43→hallucinated，213 保持 uncertain。不是“视觉准确率提高到多少”。另有原先确定但复核不一致的命题降为 uncertain。最终仍有 2 条原技术缺失；严格统计仍排除主体未支持的属性。

“变短＋H 不变＋S mixed”共有 69 对：59 对确认前后 H=0，8 对非零 H 集合不变，2 对 H 成员身份仍有不确定。可以提出“长度压缩伴随信息重组而非仅删除幻觉”的动机；不能称为神经因果证明，也不能把 H 不变自动解释成零幻觉。

更多数值和账本检查见[最终报告](../results/coco400_revision_v2_guard/RESULTS.md)与[comparison.json](../results/coco400_revision_v2_guard/comparison.json)。本轮没有新的独立人工标注，未达到真实准确率 90% 的验收结论。

## 三种复现层级

1. **无模型重算**：`python scripts/check_results.py` 从已发布逐对观测重算 A/B/B2/C 矩阵并检查 CSV、分母和 summary。可核验统计发布一致性，不能重验上游视觉判断。
2. **新输入全链运行**：按[首页](../README.md)准备数据/API，从 `end_to_end` 执行 1 对或 400 对；同目录恢复使用 `--resume`。会重新调用模型，输出因模型服务变化或采样而可能不同于历史结果。
3. **原始逐请求精确回放**：需要本地保存的历史 raw/checkpoints/frozen manifests。仓库不包含约 4 万份原冻结文件，也不声称具备完全逐字节回放条件。`run.py`、`rebind.py`、`report.py` 等历史脚本保留供审计，依赖那些本地原始输出，不能直接当作公开包的自包含命令。

发布验收采用明确的 28 项离线测试范围；整个开发目录的全量测试还包含依赖历史未公开输出的实验测试，不应与本发布验收混用。
