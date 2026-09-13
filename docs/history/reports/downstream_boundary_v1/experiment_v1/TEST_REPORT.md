# Alignment v1.1 实时测试指标

8条caption、4对样本，8-shot独立重复3轮。对照为先前版本的3轮历史运行；同时修改了提示词和校验器，因此不是仅提示词的消融实验。无完整人工gold，不报告准确率/F1。

| 指标 | 旧v1 8-shot | 新v1.1 8-shot |
| --- | --- | --- |
| 完成轮数 | 3 | 3 |
| API请求 | 48 | 48 |
| 实体步骤状态 | {'ready': 12} | {'ready': 12} |
| 事实步骤状态 | {'needs_review': 11, 'ready': 1} | {'ready': 7, 'needs_review': 4, 'failed': 1} |
| 主线事实技术回退率 | 12.8% | 12.8% |
| 全量事实跨轮成功且严格一致 | 84.2% | 78.6% |
| 双方非技术失败时严格一致率 | 98.0% | 97.9% |
| 每轮Coverage补充 | [1, 1, 1] | [1, 1, 1] |

分母固定为每轮78条原始主线事实，不含Coverage新增和other。跨轮比较状态及对侧事实语义字符串签名，技术失败不获得一致性分数。签名不做额外LLM同义判断；一致的错误仍可能得高一致率。关联引用不重复计作主对应，其稳定性单独保存在metrics.json。

## 用户反馈项逐轮结果

| 项目 | 第1轮 | 第2轮 | 第3轮 |
| --- | --- | --- | --- |
| 415015 grass explicitly in steer | added/not_expressed →  | added/not_expressed →  | added/not_expressed →  |
| 581451 condiment relation | retained/same_fact → f6 | retained/same_fact → f6 | retained/same_fact → f6 |
| 581451 pepper relation | retained/same_fact → f7 | retained/same_fact → f7 | retained/same_fact → f7 |
| 417586 asserted material | retained/same_fact → f4 | retained/same_fact → f4 | retained/same_fact → f4 |
| 417586 speculative material | ambiguous/qualifier_difference →  | ambiguous/qualifier_difference →  | ambiguous/qualifier_difference →  |
| 299573 relative layout | ambiguous/partial_overlap → f6 | ambiguous/stage_failed →  | ambiguous/partial_overlap → f6 |
| 299573 static closeness | ambiguous/partial_overlap → f6 | ambiguous/stage_failed →  | ambiguous/partial_overlap → f6 |
| 299573 bundled tall-grass fact | removed/not_expressed →  | ambiguous/stage_failed →  | removed/not_expressed →  |

## 新版完整机器指标

```json
{
  "runs_observed": 3,
  "pair_outputs": 12,
  "api_calls": 48,
  "entity_status": {
    "ready": 12
  },
  "alignment_status": {
    "ready": 7,
    "needs_review": 4,
    "failed": 1
  },
  "main_alignment_rows": {
    "added": 15,
    "ambiguous": 41,
    "removed": 56,
    "retained": 58
  },
  "original_main_fact_assignments": 234,
  "technical_original_main_fact_assignments": 30,
  "technical_failure_rate": 0.1282051282051282,
  "coverage_added": [
    1,
    1,
    1
  ],
  "pairwise_primary_consistency": [
    {
      "repeats": [
        1,
        2
      ],
      "all_facts": 78,
      "both_nontechnical": 58,
      "exact_agree": 56,
      "status_agree": 56
    },
    {
      "repeats": [
        1,
        3
      ],
      "all_facts": 78,
      "both_nontechnical": 72,
      "exact_agree": 72,
      "status_agree": 72
    },
    {
      "repeats": [
        2,
        3
      ],
      "all_facts": 78,
      "both_nontechnical": 58,
      "exact_agree": 56,
      "status_agree": 56
    }
  ],
  "success_and_exact_agreement_all": 0.7863247863247863,
  "exact_agreement_when_both_nontechnical": 0.9787234042553191,
  "status_agreement_when_both_nontechnical": 0.9787234042553191,
  "contextual_reference_consistency": [
    {
      "repeats": [
        1,
        2
      ],
      "pairs": 4,
      "same": 4
    },
    {
      "repeats": [
        1,
        3
      ],
      "pairs": 4,
      "same": 4
    },
    {
      "repeats": [
        2,
        3
      ],
      "pairs": 4,
      "same": 4
    }
  ],
  "ambiguous_reasons": {
    "partial_overlap": 10,
    "alignment_validation_error": 12,
    "qualifier_difference": 3,
    "stage_failed": 21
  },
  "usage": {
    "prompt_tokens": 340090,
    "completion_tokens": 20464,
    "total_tokens": 360554,
    "prompt_cache_hit_tokens": 301440,
    "prompt_cache_miss_tokens": 38650
  }
}
```

每轮原始响应、关联引用、校验警告和完整对应分别在s8_r1、s8_r2、s8_r3中保留。ready仅表示程序契约通过；放宽不合理的硬门槛会直接改善通过率，不能据此推断语义全对。
