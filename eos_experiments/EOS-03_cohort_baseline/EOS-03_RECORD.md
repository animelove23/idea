# EOS-03 M00 baseline 与机制 cohort 记录

## 目的

建立可复现的固定实验对象，避免继续只在最初 10 个 collapse case 上分析，并用 M00 greedy 长度匹配 control。

## 产物

- M00 baseline：160/160 完成，无异常。
- 机制 cohort：32 个历史 M11+beam collapse 样本与 32 个 M00-length-matched controls。
- 平均匹配长度差：约 0.34 词。

## 输出

- `outputs/EOS-03_m00_baseline/`：M00 配置、JSONL 和 summary。
- `outputs/EOS-03_manifests/`：候选、配对和最终 64 图 manifest。

## 代码

- `code/EOS-03_generate_m00_baseline_v2.py`
- `code/EOS-03_build_cohorts_v2.py`
- `code/EOS-03_provenance.py`

## 用途限制

该 cohort 被有意富集 collapse case，只用于机制比较，不可用来估计 COCO 上的总体 empty prevalence。
