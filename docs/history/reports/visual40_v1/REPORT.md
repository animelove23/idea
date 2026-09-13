# 40图视觉幻觉分析

视觉标注者为 Codex 助手，逐图判断；不是独立人工金标准。图片未发送 DeepSeek。所有样本在看图前随机选定；使用真实模型拆分/Coverage/对齐输出，不使用 CHAIR 真假标签。

## Table 1：整体结果

| 项目 | 结果 |
| --- | --- |
| Vanilla / Steer tokens | 4847 / 2046 |
| Length Ratio | 0.4221 |
| Vanilla / Steer core facts | 723 / 494 |
| Fact Ratio | 0.6833 |
| Vanilla / Steer true facts | 512 / 392 |
| TSR | 38.42% |
| HMR | 98.46% |
| TCR | 0.26% |
| NHR | 26.61% |
| Vanilla / Steer TID（每100 tokens） | 10.56 / 19.16 |
| Unresolved Rate | 38.87% |
| 对齐未解决率 / 原始视觉 uncertain 率 | 29.58% / 12.41% |

## Table 2：五类别核心结果

| Component | N True | N Hall | TSR | True Damage | HMR | TCR | New Hall | UR |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Object | 168 | 18 | 55.95% | 44.05% | 94.44% | 0.00% | 30.00% | 35.53% |
| Attribute | 49 | 5 | 22.45% | 77.55% | 100.00% | 0.00% | 15.79% | 26.67% |
| Action | 21 | 0 | 38.10% | 61.90% | N/A | 0.00% | 22.22% | 58.89% |
| Relation | 130 | 41 | 23.08% | 76.92% | 100.00% | 0.77% | 25.00% | 40.09% |
| Count | 12 | 1 | 25.00% | 75.00% | 100.00% | 0.00% | 50.00% | 54.72% |

## Table 3：原始迁移数量

| Component | T_RETAIN | T_REMOVE | T_TO_T | T_TO_H | H_RETAIN | H_REMOVE | H_TO_T | H_TO_H | ADD_T | ADD_H |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Object | 94 | 65 | 9 | 0 | 1 | 15 | 2 | 0 | 28 | 12 |
| Attribute | 11 | 35 | 3 | 0 | 0 | 4 | 1 | 0 | 16 | 3 |
| Action | 8 | 13 | 0 | 0 | 0 | 0 | 0 | 0 | 7 | 2 |
| Relation | 30 | 90 | 9 | 1 | 0 | 38 | 3 | 0 | 36 | 12 |
| Count | 3 | 9 | 0 | 0 | 0 | 1 | 0 | 0 | 4 | 4 |

## 计数口径与局限

TSR、HMR、TCR 按指导公式，仅对已解决的迁移计算分母；对齐 other、技术失败、视觉 uncertain 以及 retained 两侧真假矛盾不进入迁移分母，全部保留在 unresolved_audit.jsonl。UR 将对侧视觉不确定传播到该迁移的两侧事实，因此不等于两个原始比例简单相加。高 UR 的类别不能据此断言 steering 效果。

Length 使用公开 LLaVA SentencePiece tokenizer 对保存的 caption 重编码，排除 BOS/EOS；原始生成 token 轨迹未保存。Fact Ratio/TID 使用全部已抽出的非 other 类型事实；对齐不确定不改变单条事实的视觉标签。Action/Count 仅按原有 category=action/counting 拆出统计，不改动底层 v6 类型。配对迁移按 Vanilla 类别归类，新增按 Steer 类别；action/relation 分类漂移本身不判为对齐失败。

事实类型 other 共 91 条，不纳入主线。模型只拆出来的内容才能进入此分析；这不是对未抽出语义的完整召回评估。

一次40图样本不支持因果结论，也不能证明重复稳定性；若继续实验，应优先人工复核高UR类别及 removed/modified 边界。
