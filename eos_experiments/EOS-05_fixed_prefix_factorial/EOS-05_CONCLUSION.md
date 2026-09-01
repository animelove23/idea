# EOS-05 结论

VSV 在固定 M00 状态上会显著提高 EOS relative margin；SLA 单独反而降低该 margin，联合交互只在最早位置小幅为正，之后转为负。该模式在 collapse 与 control 中相似，因此不能解释哪些图会 collapse。

本实验在 beam 之前、固定 prefix 上测量局部 logits，不能据此声称 beam 只是被动放大器，也不能把 EOS-margin 上升直接解释为 EOS raw logit 同幅上升。
