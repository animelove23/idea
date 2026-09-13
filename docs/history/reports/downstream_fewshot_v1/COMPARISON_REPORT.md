# 下游 0-shot / 8-shot 对照

使用4对既有真实caption；每组3次独立请求运行。例子为助手编写的另外16条合成caption，每阶段8个示例。没有改Decomposer、原始事实或语义规则。当前是已见开发集，不是独立泛化测试。

没有人工gold，因此不报告准确率、Precision/Recall/F1。此处比较技术可用性、状态分布、重复一致性；具体语义仍需审核。

| 条件 | 已运行轮数 | 请求数 | Coverage新增/轮 | Entity状态 | Alignment状态 |
| --- | --- | --- | --- | --- | --- |
| 0-shot | 3 | 44 | [1, 1, 1] | {'ready': 8, 'failed': 4} | {'needs_review': 5, 'ready': 3, 'failed': 4} |
| 8-shot | 3 | 48 | [1, 1, 1] | {'ready': 12} | {'needs_review': 11, 'ready': 1} |

## 重复一致性

只比较固定的原始主线事实，不因Coverage追加数量变化改变原始分母。比较状态及对侧完整事实签名；技术失败不计作语义一致。严格签名会把同义改写算作不同，不能当语义准确率。

### 0-shot

```json
{
  "runs_observed": 3,
  "requests": 44,
  "coverage_added": [
    1,
    1,
    1
  ],
  "entity_status": {
    "ready": 8,
    "failed": 4
  },
  "alignment_status": {
    "needs_review": 5,
    "ready": 3,
    "failed": 4
  },
  "main_alignment_rows": {
    "added": 6,
    "ambiguous": 95,
    "modified": 7,
    "removed": 30,
    "retained": 45
  },
  "ambiguous_reason_counts": {
    "entity_uncertain": 1,
    "alignment_validation_error": 13,
    "stage_failed": 88,
    "partial_overlap": 2
  },
  "original_main_fact_assignments": 234,
  "technical_original_main_fact_assignments": 93,
  "pairwise_stability": [
    {
      "repeats": [
        1,
        2
      ],
      "original_main_facts": 78,
      "both_nontechnical": 50,
      "exact_agree": 48,
      "status_agree": 48,
      "strict_agreement_all": 0.6153846153846154,
      "strict_agreement_nontechnical": 0.96
    },
    {
      "repeats": [
        1,
        3
      ],
      "original_main_facts": 78,
      "both_nontechnical": 37,
      "exact_agree": 34,
      "status_agree": 35,
      "strict_agreement_all": 0.4358974358974359,
      "strict_agreement_nontechnical": 0.918918918918919
    },
    {
      "repeats": [
        2,
        3
      ],
      "original_main_facts": 78,
      "both_nontechnical": 37,
      "exact_agree": 34,
      "status_agree": 35,
      "strict_agreement_all": 0.4358974358974359,
      "strict_agreement_nontechnical": 0.918918918918919
    }
  ]
}
```

### 8-shot

```json
{
  "runs_observed": 3,
  "requests": 48,
  "coverage_added": [
    1,
    1,
    1
  ],
  "entity_status": {
    "ready": 12
  },
  "alignment_status": {
    "needs_review": 11,
    "ready": 1
  },
  "main_alignment_rows": {
    "added": 12,
    "ambiguous": 38,
    "removed": 61,
    "retained": 58,
    "modified": 1
  },
  "ambiguous_reason_counts": {
    "partial_overlap": 10,
    "alignment_validation_error": 30,
    "granularity": 1
  },
  "original_main_fact_assignments": 234,
  "technical_original_main_fact_assignments": 30,
  "pairwise_stability": [
    {
      "repeats": [
        1,
        2
      ],
      "original_main_facts": 78,
      "both_nontechnical": 67,
      "exact_agree": 67,
      "status_agree": 67,
      "strict_agreement_all": 0.8589743589743589,
      "strict_agreement_nontechnical": 1.0
    },
    {
      "repeats": [
        1,
        3
      ],
      "original_main_facts": 78,
      "both_nontechnical": 67,
      "exact_agree": 65,
      "status_agree": 65,
      "strict_agreement_all": 0.8333333333333334,
      "strict_agreement_nontechnical": 0.9701492537313433
    },
    {
      "repeats": [
        2,
        3
      ],
      "original_main_facts": 78,
      "both_nontechnical": 67,
      "exact_agree": 65,
      "status_agree": 65,
      "strict_agreement_all": 0.8333333333333334,
      "strict_agreement_nontechnical": 0.9701492537313433
    }
  ]
}
```

## 逐条可审核对照

| pair / side / fact | 原始事实 | 0-shot r1/r2/r3 | 8-shot r1/r2/r3 |
| --- | --- | --- | --- |
| 299573/original/f1 | There are two giraffes. | retained/same_fact → f1<br>retained/same_fact → f1<br>retained/same_fact → f1 | retained/same_fact → f1<br>retained/same_fact → f1<br>retained/same_fact → f1 |
| 299573/original/f10 | The giraffes are standing close to each other. | removed/not_expressed → <br>removed/not_expressed → <br>modified/value_changed → f6 | ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error → <br>removed/not_expressed →  |
| 299573/original/f12 | The field is filled with tall grass. | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 299573/original/f2 | There is a grassy field. | retained/same_fact → f3<br>retained/same_fact → f3<br>retained/same_fact → f3 | retained/same_fact → f3<br>retained/same_fact → f3<br>retained/same_fact → f3 |
| 299573/original/f3 | There are two giraffes. | retained/same_fact → f2<br>retained/same_fact → f2<br>retained/same_fact → f2 | retained/same_fact → f2<br>retained/same_fact → f2<br>retained/same_fact → f2 |
| 299573/original/f4 | The field is grassy. | retained/same_fact → f4<br>retained/same_fact → f4<br>retained/same_fact → f4 | retained/same_fact → f4<br>retained/same_fact → f4<br>retained/same_fact → f4 |
| 299573/original/f5 | The giraffes are standing. | retained/same_fact → f5<br>retained/same_fact → f5<br>retained/same_fact → f5 | retained/same_fact → f5<br>retained/same_fact → f5<br>retained/same_fact → f5 |
| 299573/original/f6 | The giraffes are in the grassy field. | retained/same_fact → f7<br>retained/same_fact → f7<br>retained/same_fact → f7 | retained/same_fact → f7<br>retained/same_fact → f7<br>retained/same_fact → f7 |
| 299573/original/f7 | One giraffe is positioned slightly behind the other. | modified/value_changed → f6<br>modified/value_changed → f6<br>removed/not_expressed →  | ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error → <br>modified/value_changed → f6 |
| 299573/original/f8 | Both giraffes are facing the same direction. | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 299573/original/f9 | The giraffes are possibly looking at something in the distance. | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 299573/steer/f1 | There are giraffes. | retained/same_fact → f1<br>retained/same_fact → f1<br>retained/same_fact → f1 | retained/same_fact → f1<br>retained/same_fact → f1<br>retained/same_fact → f1 |
| 299573/steer/f2 | There are two giraffes. | retained/same_fact → f3<br>retained/same_fact → f3<br>retained/same_fact → f3 | retained/same_fact → f3<br>retained/same_fact → f3<br>retained/same_fact → f3 |
| 299573/steer/f3 | There is a grassy field. | retained/same_fact → f2<br>retained/same_fact → f2<br>retained/same_fact → f2 | retained/same_fact → f2<br>retained/same_fact → f2<br>retained/same_fact → f2 |
| 299573/steer/f4 | The field is grassy. | retained/same_fact → f4<br>retained/same_fact → f4<br>retained/same_fact → f4 | retained/same_fact → f4<br>retained/same_fact → f4<br>retained/same_fact → f4 |
| 299573/steer/f5 | The giraffes are standing. | retained/same_fact → f5<br>retained/same_fact → f5<br>retained/same_fact → f5 | retained/same_fact → f5<br>retained/same_fact → f5<br>retained/same_fact → f5 |
| 299573/steer/f6 | The giraffes are side by side. | modified/value_changed → f7<br>modified/value_changed → f7<br>modified/value_changed → f10 | ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error → <br>modified/value_changed → f7 |
| 299573/steer/f7 | The giraffes are in the grassy field. | retained/same_fact → f6<br>retained/same_fact → f6<br>retained/same_fact → f6 | retained/same_fact → f6<br>retained/same_fact → f6<br>retained/same_fact → f6 |
| 415015/original/f1 | There is a vase. | modified/value_changed → f1<br>modified/value_changed → f1<br>ambiguous/stage_failed →  | retained/same_fact → f1<br>retained/same_fact → f1<br>retained/same_fact → f1 |
| 415015/original/f10 | The vase is positioned near the window. | ambiguous/alignment_validation_error → <br>ambiguous/partial_overlap → <br>ambiguous/stage_failed →  | ambiguous/partial_overlap → f9<br>ambiguous/partial_overlap → f9<br>ambiguous/partial_overlap → f9 |
| 415015/original/f2 | There are dried flowers. | modified/value_changed → f2<br>modified/value_changed → f2<br>ambiguous/stage_failed →  | ambiguous/partial_overlap → f2<br>ambiguous/granularity → f2<br>retained/same_fact → f2 |
| 415015/original/f3 | There are daisies. | ambiguous/entity_uncertain → f3<br>removed/not_expressed → <br>ambiguous/stage_failed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 415015/original/f4 | There are sunflowers. | ambiguous/entity_uncertain → f3<br>removed/not_expressed → <br>ambiguous/stage_failed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 415015/original/f5 | There is a table. | retained/same_fact → f4<br>retained/same_fact → f4<br>ambiguous/stage_failed →  | retained/same_fact → f4<br>retained/same_fact → f4<br>retained/same_fact → f4 |
| 415015/original/f6 | There is a window. | retained/same_fact → f5<br>retained/same_fact → f5<br>ambiguous/stage_failed →  | retained/same_fact → f5<br>retained/same_fact → f5<br>retained/same_fact → f5 |
| 415015/original/f7 | The vase is filled with dried flowers. | ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error → <br>ambiguous/stage_failed →  | ambiguous/partial_overlap → f7<br>ambiguous/partial_overlap → f7<br>ambiguous/partial_overlap → f7 |
| 415015/original/f8 | The dried flowers include daisies and sunflowers. | ambiguous/alignment_validation_error → <br>removed/not_expressed → <br>ambiguous/stage_failed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 415015/original/f9 | The vase is placed on the table. | retained/same_fact → f8<br>retained/same_fact → f8<br>ambiguous/stage_failed →  | retained/same_fact → f8<br>retained/same_fact → f8<br>retained/same_fact → f8 |
| 415015/steer/f1 | There is a glass vase. | modified/value_changed → f1<br>modified/value_changed → f1<br>ambiguous/stage_failed →  | retained/same_fact → f1<br>retained/same_fact → f1<br>retained/same_fact → f1 |
| 415015/steer/f2 | There are flowers. | modified/value_changed → f2<br>modified/value_changed → f2<br>ambiguous/stage_failed →  | ambiguous/partial_overlap → f2<br>ambiguous/granularity → f2<br>retained/same_fact → f2 |
| 415015/steer/f3 | There are grasses. | ambiguous/entity_uncertain → f3,f4<br>ambiguous/alignment_validation_error → <br>ambiguous/stage_failed →  | ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error →  |
| 415015/steer/f4 | There is a table. | retained/same_fact → f5<br>retained/same_fact → f5<br>ambiguous/stage_failed →  | retained/same_fact → f5<br>retained/same_fact → f5<br>retained/same_fact → f5 |
| 415015/steer/f5 | There is a window. | retained/same_fact → f6<br>retained/same_fact → f6<br>ambiguous/stage_failed →  | retained/same_fact → f6<br>retained/same_fact → f6<br>retained/same_fact → f6 |
| 415015/steer/f6 | The vase is made of glass. | added/not_expressed → <br>added/not_expressed → <br>ambiguous/stage_failed →  | added/not_expressed → <br>added/not_expressed → <br>added/not_expressed →  |
| 415015/steer/f7 | The vase is filled with flowers and grasses. | ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error → <br>ambiguous/stage_failed →  | ambiguous/partial_overlap → f7<br>ambiguous/partial_overlap → f7<br>ambiguous/partial_overlap → f7 |
| 415015/steer/f8 | The vase is placed on the table. | retained/same_fact → f9<br>retained/same_fact → f9<br>ambiguous/stage_failed →  | retained/same_fact → f9<br>retained/same_fact → f9<br>retained/same_fact → f9 |
| 415015/steer/f9 | The table is next to the window. | ambiguous/alignment_validation_error → <br>added/not_expressed → <br>ambiguous/stage_failed →  | ambiguous/partial_overlap → f10<br>ambiguous/partial_overlap → f10<br>ambiguous/partial_overlap → f10 |
| 417586/original/f1 | There is a bench. | retained/same_fact → f2<br>retained/same_fact → f2<br>retained/same_fact → f2 | retained/same_fact → f2<br>retained/same_fact → f2<br>retained/same_fact → f2 |
| 417586/original/f10 | The bench is situated in a grassy area. | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 417586/original/f12 | The shoes seem to be old. | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 417586/original/f13 | The shoes seem to be worn. | ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 417586/original/f2 | There are shoes. | retained/same_fact → f1<br>retained/same_fact → f1<br>retained/same_fact → f1 | retained/same_fact → f1<br>retained/same_fact → f1<br>retained/same_fact → f1 |
| 417586/original/f3 | The bench is wooden. | retained/same_fact → f4<br>retained/same_fact → f4<br>retained/same_fact → f4 | ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error →  |
| 417586/original/f4 | There are two pairs of the described shoes. | retained/same_fact → f3<br>retained/same_fact → f3<br>retained/same_fact → f3 | retained/same_fact → f3<br>retained/same_fact → f3<br>retained/same_fact → f3 |
| 417586/original/f5 | The shoes are on the bench. | retained/same_fact → f5<br>retained/same_fact → f5<br>retained/same_fact → f5 | retained/same_fact → f5<br>retained/same_fact → f5<br>retained/same_fact → f5 |
| 417586/original/f6 | The shoes are positioned close to each other. | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 417586/original/f7 | One pair of shoes is located towards the left side of the bench. | retained/same_fact → f6<br>retained/same_fact → f6<br>retained/same_fact → f6 | retained/same_fact → f6<br>retained/same_fact → f6<br>retained/same_fact → f6 |
| 417586/original/f8 | The other pair of shoes is on the right side of the bench. | retained/same_fact → f7<br>retained/same_fact → f7<br>retained/same_fact → f7 | retained/same_fact → f7<br>retained/same_fact → f7<br>retained/same_fact → f7 |
| 417586/original/f9 | The bench appears to be made of wood. | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  | ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error →  |
| 417586/steer/f1 | There are shoes. | retained/same_fact → f2<br>retained/same_fact → f2<br>retained/same_fact → f2 | retained/same_fact → f2<br>retained/same_fact → f2<br>retained/same_fact → f2 |
| 417586/steer/f2 | There is a bench. | retained/same_fact → f1<br>retained/same_fact → f1<br>retained/same_fact → f1 | retained/same_fact → f1<br>retained/same_fact → f1<br>retained/same_fact → f1 |
| 417586/steer/f3 | There are two pairs of the described shoes. | retained/same_fact → f4<br>retained/same_fact → f4<br>retained/same_fact → f4 | retained/same_fact → f4<br>retained/same_fact → f4<br>retained/same_fact → f4 |
| 417586/steer/f4 | The bench is wooden. | retained/same_fact → f3<br>retained/same_fact → f3<br>retained/same_fact → f3 | ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error →  |
| 417586/steer/f5 | The shoes are on the bench. | retained/same_fact → f5<br>retained/same_fact → f5<br>retained/same_fact → f5 | retained/same_fact → f5<br>retained/same_fact → f5<br>retained/same_fact → f5 |
| 417586/steer/f6 | One pair of shoes is on the left side of the bench. | retained/same_fact → f7<br>retained/same_fact → f7<br>retained/same_fact → f7 | retained/same_fact → f7<br>retained/same_fact → f7<br>retained/same_fact → f7 |
| 417586/steer/f7 | The other pair of shoes is on the right side of the bench. | retained/same_fact → f8<br>retained/same_fact → f8<br>retained/same_fact → f8 | retained/same_fact → f8<br>retained/same_fact → f8<br>retained/same_fact → f8 |
| 417586/steer/f8 | Both pairs of shoes are black. | added/not_expressed → <br>added/not_expressed → <br>added/not_expressed →  | added/not_expressed → <br>added/not_expressed → <br>added/not_expressed →  |
| 581451/original/f1 | There is a hot dog. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | retained/same_fact → f2<br>retained/same_fact → f2<br>retained/same_fact → f2 |
| 581451/original/f10 | The peppers are green. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 581451/original/f11 | The hot dog is placed on the piece of paper. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 581451/original/f12 | The piece of paper is likely a napkin. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 581451/original/f13 | The hot dog is positioned in the center of the image. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 581451/original/f14 | The peppers are scattered around the hot dog. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 581451/original/f2 | There is a bun. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 581451/original/f3 | There is ketchup. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | retained/same_fact → f3<br>retained/same_fact → f3<br>retained/same_fact → f3 |
| 581451/original/f4 | There are green peppers. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | retained/same_fact → f4<br>retained/same_fact → f4<br>retained/same_fact → f4 |
| 581451/original/f5 | There is a piece of paper. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 581451/original/f6 | There is a napkin. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 581451/original/f7 | The hot dog has a bun. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | removed/not_expressed → <br>removed/not_expressed → <br>removed/not_expressed →  |
| 581451/original/f8 | The hot dog is topped with ketchup. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error →  |
| 581451/original/f9 | The hot dog is topped with green peppers. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error →  |
| 581451/steer/f1 | There is a person. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | added/not_expressed → <br>added/not_expressed → <br>added/not_expressed →  |
| 581451/steer/f2 | There is a hot dog. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | retained/same_fact → f1<br>retained/same_fact → f1<br>retained/same_fact → f1 |
| 581451/steer/f3 | There is ketchup. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | retained/same_fact → f3<br>retained/same_fact → f3<br>retained/same_fact → f3 |
| 581451/steer/f4 | There are peppers. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | retained/same_fact → f4<br>retained/same_fact → f4<br>retained/same_fact → f4 |
| 581451/steer/f5 | The person is holding the hot dog. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | added/not_expressed → <br>added/not_expressed → <br>added/not_expressed →  |
| 581451/steer/f6 | The hot dog has ketchup on it. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error →  |
| 581451/steer/f7 | The hot dog has peppers on it. | ambiguous/stage_failed → <br>ambiguous/stage_failed → <br>ambiguous/stage_failed →  | ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error → <br>ambiguous/alignment_validation_error →  |
