# EOS-04 数值、batch 与 cache 控制记录

## 目的

检查 VSV wrapper 的 zero/no-op、beam batch repeat 和 cached/non-cached 前向是否引入足以改变 EOS 决策的数值偏差。

## 运行

- 初始 4 图 sanity；
- 放宽 all-vocabulary tolerance 的复查；
- 加入 EOS rank、top non-EOS 和 top-5 decision logging 的运行及 rerun。

## 结果

- strict no-op：通过，所有位置和精度路径最大差异为 0。
- batch1 vs repeat×5：严格 `2e-3` all-vocabulary 门槛失败，最大差异约 0.0703。
- cached vs full-prefix：严格门槛失败，最大差异约 0.03125。
- top non-EOS：batch 与 cache 各 240/240 比较保持一致。
- EOS rank：batch 仅 97/240 完全一致；cache 仅 141/240 完全一致。

## 输出

`outputs/` 下按 initial、tol007、decision initial、decision rerun 保存全部 config、metrics 和 summary，包括失败门禁记录。
