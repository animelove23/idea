# EOS-02 结论

在这 10 个已知 collapse case 上，VSV-only 和 SLA-only 均不足以产生空 caption，而联合方法在两个 SLA layer window 下均产生 8/10 empty。该结果说明“联合配置”是这些 case 的必要条件之一，并排除 layer-window off-by-one 是主因。

它不证明总体上的统计交互，也不证明单模块没有改变 EOS relative margin；它测到的是最终首 token EOS/empty outcome。
