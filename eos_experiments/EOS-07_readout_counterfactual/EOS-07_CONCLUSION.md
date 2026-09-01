# EOS-07 结论

VSV 引起的 k=0 logits 重排更多通过 final-layer readout 体现，SLA early-layer readout 也贡献一部分；联合变化主要来自强非 EOS 候选被压低。collapse 与 control 的模式近似，因此该 readout attribution 不解释 collapse selectivity。

该实验没有 beam、没有选择性 VSV 注入，也没有真正的两模块开关。它不能支持“双路径重复注入导致 collapse”，也不能支持“VSV 先直接推高 EOS、beam 再放大”的机制叙事。
