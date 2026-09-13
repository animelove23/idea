# M0 数据配对与图像审计

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "original_rows": 500,
  "steer_rows": 500,
  "roster_rows": 500,
  "paired": 500,
  "pair_coverage": 1.0,
  "image_readable": 62,
  "image_readable_rate": 0.124,
  "unpaired": 0,
  "empty_original": 0,
  "empty_steer": 1,
  "silent_drops": 0
}
```

- 未调用LLM；读取并校验原图，缺图/坏图保留在名册。
- 既有500图是探索数据，不冒称未见测试集。
- 解码设置仅有文件名线索；没有真实EOS/生成trace，停止原因统一unknown。
