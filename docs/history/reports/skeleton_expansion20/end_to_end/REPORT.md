# 冻结模块串联运行

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "selected_pairs": 20,
  "pair_statuses": [
    {
      "pair_id": "326667",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "352377",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "195269",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "69584",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "317188",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "373677",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "279634",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "45094",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "381925",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "54264",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "256003",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "462687",
      "status": "needs_review",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "450500",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "69946",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "265462",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "303499",
      "status": "needs_review",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "316617",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "519838",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "565761",
      "status": "needs_review",
      "image_available": true,
      "analysis_available": true
    },
    {
      "pair_id": "483723",
      "status": "ready",
      "image_available": true,
      "analysis_available": true
    }
  ],
  "verified_claims": 196,
  "pending_claims": 0
}
```

- 无参考答案输入；串联分布不等于端到端准确率。
- M2技术失败的pair禁止正常对齐推断；保留可用事实，但总体召回未知，不能解释为零事实。
- 选择的pair必须已获得所需数据外发授权；不会隐式扩大到整个清单。
