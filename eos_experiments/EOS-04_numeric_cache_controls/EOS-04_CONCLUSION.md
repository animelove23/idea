# EOS-04 结论

zero-lambda wrapper 不是问题来源；普通 FP16 数值漂移也没有改变最强非 EOS token。但 EOS rank 对 batch repeat 和 cache 路径较敏感，因此现有控制不能排除 beam-expanded batch/cache 数值差异参与边界 case。不能声称 beam implementation artifact 已被完全排除。
