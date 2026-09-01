# EOS-01 初始 greedy/beam5 collapse 记录

## 设置

- 模型：LLaVA-1.5-7B。
- 数据：MSCOCO 2014 validation images。
- Prompt：`Please help me describe the image in detail.`
- 完整方法：VSV `lambda=0.17`，SLA `alpha=0.3`，layers `25,30`，max new tokens 512。
- 对比：greedy 与 beam size 5。

## 原始观察

- VISTA greedy：500 图中 2 个空 caption。
- VISTA beam5：原运行完成 407/500，其中 127 个空 caption，约 31.2%。
- 空 caption 已核对为首个生成 token 是 EOS（token id 2），不是 JSON 写入或后处理错误。

## 输出

`outputs/EOS-01_chair_three_decode/` 保存原始 greedy、beam5、nucleus 输出、日志和已有 CHAIR 评分。

## 完整性限制

beam5 原始运行只完成 407/500，因此 `127/407` 是问题发现用 observation，不能作为无偏总体发生率估计。
