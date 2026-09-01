# EOS 归档源路径映射

本表记录编号归档与旧目录的对应关系。旧目录仍是原始生成位置；编号目录是整理后的独立副本。

| 编号 | 编号归档 | 主要旧路径 |
|---|---|---|
| EOS-00 | `EOS-00_scope/` | `newest_find_out/basement_by_YE/VISTA_observation_research_goal.md`、`refine-logs/EXPERIMENT_PLAN.md`、`refine-logs/EXPERIMENT_TRACKER.md`、`findings.md`、`MANIFEST.md` |
| EOS-01 | `EOS-01_initial_beam_collapse/` | `exp_results/chair_three_decode/` |
| EOS-02 | `EOS-02_module_ablation/` | `exp_results/new_observation/`、`exp_results/chair_beam_empty32_recheck/`、`chair_beam_empty10_*` |
| EOS-03 | `EOS-03_cohort_baseline/` | `newest_find_out/result/termination_audit/manifests/`、`m00_baseline/`；旧 proxy/manifest 位于 `exp_results/termination_audit/` |
| EOS-04 | `EOS-04_numeric_cache_controls/` | `newest_find_out/result/termination_audit/sanity_*` |
| EOS-05 | `EOS-05_fixed_prefix_factorial/` | `newest_find_out/result/termination_audit/fixed_prefix_64/`、`CLAIMS_FROM_RESULTS.md` |
| EOS-06 | `EOS-06_greedy_beam_trace/` | `newest_find_out/result/termination_audit/greedy_trace_64/`、`beam_trace_64/` |
| EOS-07 | `EOS-07_readout_counterfactual/` | `newest_find_out/result/termination_audit/path_split_smoke_2*`、`path_split_64/` |

## 解释优先级

1. 编号目录中的 `EOS-XX_CONCLUSION.md`：按现有全部证据修订后的结论。
2. 编号目录中的 `EOS-XX_RECORD.md`：实验设计、完整性和产物索引。
3. `outputs/` 原始数据与配置：发生冲突时以原始记录为准。
4. 文件名含 `SOURCE` 或 `LEGACY` 的文档：历史快照，可能包含后来被修正的假设或术语。

## EOS-06 合并规则

M11 beam5 的 64 个最终记录来自三个互不重复的集合：

- 主运行中成功的 37 图：24 empty、13 nonempty；
- `resume_m11_beam5_26_20260831` 的 26 图：4 empty、22 nonempty；
- `resume_smoke_116521_v2` 的 1 图：nonempty。

合并后为 64 图、28 empty、36 nonempty。主运行中的 27 条 OOM exception 保留作审计，但不能与恢复后的成功记录重复计入最终 outcome。
