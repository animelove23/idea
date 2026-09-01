# EOS-00 结论

EOS-00 是研究设计而不是结果实验。它确定了两个关键约束：不能只用最终空输出推断 EOS 机制，也不能只用 fixed-prefix logits 推断 beam 机制。后续实验必须同时保留局部 logits 指标和真实自由解码 outcome。
