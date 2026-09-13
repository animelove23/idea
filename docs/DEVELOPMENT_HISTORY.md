# 开发历史与报告导航

以下按阶段组织，避免把不同模型、不同样本和不同参考口径串成一条“准确率不断上升”的曲线。原报告保留用于追踪当时结论，最新状态以[首页](../README.md)和[最新实验说明](EXPERIMENTS.md)为准。

原开发规划也已归档：[模块构建规划](history/plans/MODULE_BUILD_PLAN.md)、[Astra 框架改进计划](history/plans/FRAMEWORK_IMPROVEMENT_PLAN_ASTRA.md)、[词语与视觉协议](history/plans/LEXICAL_AND_VISUAL_PROTOCOL.md)、[阶段方案](history/plans/FINAL_PROPOSAL.md)、[迭代说明](history/plans/REFINEMENT_REPORT.md)。同目录保留较早草案和带时间戳版本，属于开发历史，不应覆盖当前模块契约。

## 1. 原 VISTA 与多维语义实验

项目最初关注 steering 抑制幻觉及输出缩短。早期把实体、属性、动作、关系、数量等多个变量同时纳入，类别和示例边界不够稳定，难以定位错误来源。随后收缩为 entity＋attribute，并增加独立词语/POS 视角，保留 decompose→align→visual verification 的主线。

- [旧仓库 VISTA 框架](history/previous_repository/VISTA_paper_experiment_framework.md)
- [研究背景](history/background/VLM_STEERING_EXPERIMENT_CONTEXT.md)
- [早期实现规划](../decomposition/MINIMAL_STABLE_IMPLEMENTATION_PLAN.md)
- 早期源码可从旧提交 `4b41ff0` 恢复；当前仓库不再以生成 VISTA caption 为主入口。

## 2. 分析骨架与 20 图扩展

确立逐模块测评、few-shot 固定示例、entity 与 attribute 的 owner 约束。20 图/40 caption 试验暴露引文定位、词形还原计分偏差、跨主体 ID 约束和视觉上下文缺失。

- [骨架实验卡](../analysis_skeleton/EXPERIMENT_CARD.md)
- [20 图结果](history/reports/skeleton_expansion20/RESULTS.md)
- [首次修复报告](history/reports/skeleton_repair_v1/RESULTS.md)

旧对齐联合 F1 93.1% 来自 Pro、固定 20 组/300 条参考事实及格式修复回放，不能解释为当前 Flash 在 400 对上已超过 90%。

## 3. 视觉证据、定位与 Flash 迭代

反复审查“主体不确定、属性却支持”、具体类别与可见物体混淆、上下文不足。加入主体定位、证据编译、按事实类型固定路由及严格父主体资格；逐步改为 Flash。候选参考有人工审阅参与的历史记录，但不能统称为独立人工 gold。

- [证据验证器](history/reports/evidence_verifier_v1/RESULTS.md)
- [Flash 结果](history/reports/evidence_verifier_v2_flash_network/RESULTS.md)
- [复用旧标记数据：39 图、579 命题](history/reports/legacy_visual_full_flash_v1/RESULTS.md)
- [分解 Flash 迭代](history/reports/decompose_iteration_v1_flash/RESULTS.md)

## 4. Final v1 冻结

M2 同 40 caption 的 entity/attribute/joint F1 约 88.50/88.61/88.51%；M5 组合路由在旧 579 条候选参考中 entity 434/508=85.43%，attribute 63/71=88.73%。组合路由是看过开发结果后的固定选择，不是独立 holdout 验证；不能宣布实体准确率已达 90%。

- [冻结报告](history/reports/final_v1_release/RESULTS.md)
- [M2 审查](history/reports/final_v1_m2/SEMANTIC_REVIEW.md)
- [M5 审查](history/reports/final_v1_m5/SEMANTIC_REVIEW.md)
- [原冻结入口说明](../analysis_skeleton/final_v1/README.md)

## 5. COCO 400 对首轮实验

下载 COCO 2014 validation，固定 400 对已有 baseline/VISTA 文本，全链运行。213 对矩阵未决，其中 211 对文本缩短；原报告暴露样本级过度隔离、视觉 uncertain 和主体对齐问题。未决数是“受影响样本对”，不等于一个模块错了同样多次。

- [原 400 对报告](../results/coco400_final_v1/RESULTS.md)
- [未决与案例审查](../results/coco400_final_v1/CASE_REVIEW.md)
- [原动机观察](../results/coco400_final_v1/MOTIVATION.md)

## 6. Revision v2 guard 候选版（当前）

先只改局部统计传播，再改 M3 身份/描述变化契约，随后离线隔离冲突、重绑不安全的共享视觉命题，最后执行一次视觉复核。旧冻结文件保持不动，候选有独立目录。

首个新 M3 合成探针 7/8；身份反证提示修订后 8/8。这些探针已用于调试，不是独立准确率测评。首版大批运行中断留下 80 complete＋1 technical 及 8 started 无返回记录；8 个远端结果未知，不自动补发、不记作正式成功。全部开发记录共 1003 次有记录调用，此外 8 次远端结果未知；正式修订比较使用 400 M3＋506 M5。

最新矩阵覆盖 269/400，但 M3 技术未决增至 214。该候选没有取代旧入口的准确率验收资格。下一步应独立抽样审查 ID/主体错误并修复技术约束，再谈真实语义改善；不能靠消除 uncertain 人为提高指标。

- [候选模块说明](../experiments/coco400_revision_v2/README.md)
- [最新详细报告](../results/coco400_revision_v2_guard/RESULTS.md)
- [全部阶段数值](../results/coco400_revision_v2_guard/comparison.json)

## 7. 本次仓库整理

未重新运行模型、未改变历史统计值。发布改动包括相对图片路径、依赖说明、数据准备和结果核验脚本、报告归档与索引；保留旧 Git 历史，以正常提交覆盖工作树内容。原报告中的 `outputs/...` 等路径指当时完整本地实验工作区，部分原始文件未入库；完整边界见[发布说明](PUBLICATION.md)。
