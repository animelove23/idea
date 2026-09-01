# EOS 归档校验

校验日期：2026-09-01。

## 归档规模

- 文件总数：193（含本校验文件）。
- 总体积：约 240 MiB。
- 编号记录：EOS-00 至 EOS-07，共 8 份 `RECORD`。
- 编号结论：EOS-00 至 EOS-07，共 8 份 `CONCLUSION`。

## 副本一致性

使用递归逐文件比较核对以下主要输出目录，均与原始目录一致：

- EOS-01 `chair_three_decode`；
- EOS-02 w=5、VSV-only、SLA-only；
- EOS-03 M00 baseline；
- EOS-05 fixed-prefix 64；
- EOS-06 greedy trace 与 beam trace；
- EOS-07 path-split 64，包括 64 个 tensor cache。

## EOS-06 outcome 复算

- Greedy：M00/M01/M10 各 64/64 nonempty；M11 为 62 nonempty、2 empty。
- Beam 主跑：M00/M01/M10 各 64/64 nonempty；M11 有 37 个成功记录和 27 个 OOM。
- M11 26 图恢复跑：22 nonempty、4 empty。
- image 116521 单图恢复：nonempty。
- 三个 M11 成功集合 image ID 无重复，合并为 64 图、28 empty、36 nonempty。

## 保留的空文件

归档中有 6 个零字节文件，均为原目录已经存在的空日志或未启动 baseline 文件；为保持审计完整性原样保留，不代表复制失败。具体包括初始空 queue/beam 日志、空 M00 greedy 占位输出、两个 beam trace 外层日志和一个空 recheck 外层日志。

## 版本状态

`eos_experiments/` 是新建的未提交目录。旧目录未移动、未删除、未改名。
