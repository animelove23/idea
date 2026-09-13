# Coverage / Alignment 首轮测试

Decomposer、v6 few-shot 和既有事实均未修改；使用先前独立拆分的真实 caption。所有视觉验证保持 pending。

## 状态计数

```json
{
  "pairs_planned": 4,
  "pairs_completed": 4,
  "coverage_captions": 8,
  "coverage_added": 1,
  "coverage_status": {
    "ready": 8
  },
  "entity_status": {
    "ready": 3,
    "failed": 1
  },
  "alignment_status": {
    "needs_review": 2,
    "ready": 1,
    "failed": 1
  },
  "alignment_rows_all": {
    "added": 2,
    "ambiguous": 31,
    "modified": 3,
    "removed": 14,
    "retained": 16
  },
  "alignment_rows_main": {
    "added": 2,
    "ambiguous": 28,
    "modified": 3,
    "removed": 9,
    "retained": 16
  },
  "main_fact_status_counts": {
    "original": {
      "added": 0,
      "ambiguous": 20,
      "modified": 3,
      "removed": 9,
      "retained": 16
    },
    "steer": {
      "added": 2,
      "ambiguous": 10,
      "modified": 3,
      "removed": 0,
      "retained": 16
    }
  },
  "extraction_gap_rows": 0,
  "api_calls": 15,
  "pending_claims": 87,
  "note": "Alignment outputs are not human gold; ambiguous/extraction_gap are never counted as removed/added. All verifier labels pending."
}
```

注意：alignment 行数与事实数不同，ambiguous 可以多对多；主线不统计 other。未完成/失败另列，不用它们制造信息删除。

## Coverage 追加事实

### 581451_vanilla — ready

无已接收新增事实。

### 299573_vista — ready

无已接收新增事实。

### 417586_vanilla — ready

无已接收新增事实。

### 581451_vista — ready

无已接收新增事实。

### 417586_vista — ready

无已接收新增事实。

### 299573_vanilla — ready

- cov_f1 [attribute] The grass is tall.（source: tall grass）

### 415015_vanilla — ready

无已接收新增事实。

### 415015_vista — ready

无已接收新增事实。

## Entity Alignment

### 417586

```json
{
  "pair_id": "417586",
  "status": "ready",
  "original_entities": [
    {
      "id": "o1",
      "mention": "a wooden bench",
      "fact_ids": [
        "f1",
        "f3",
        "f9",
        "f10"
      ],
      "description": "The bench in the image, made of wood, situated in a grassy area."
    },
    {
      "id": "o2",
      "mention": "two pairs of shoes",
      "fact_ids": [
        "f2",
        "f4",
        "f5",
        "f6",
        "f12",
        "f13",
        "f14"
      ],
      "description": "Two pairs of shoes placed on the bench, close to each other, old and worn."
    },
    {
      "id": "o3",
      "mention": "one pair located towards the left side of the bench",
      "fact_ids": [
        "f7"
      ],
      "description": "The pair of shoes on the left side of the bench."
    },
    {
      "id": "o4",
      "mention": "the other pair on the right side",
      "fact_ids": [
        "f8"
      ],
      "description": "The pair of shoes on the right side of the bench."
    },
    {
      "id": "o5",
      "mention": "a grassy area",
      "fact_ids": [
        "f10",
        "f11"
      ],
      "description": "The grassy area where the bench is situated, possibly a park or garden."
    }
  ],
  "steer_entities": [
    {
      "id": "s1",
      "mention": "two pairs of shoes",
      "fact_ids": [
        "f1",
        "f3",
        "f5",
        "f8"
      ],
      "description": "Two pairs of shoes resting on the bench, both black."
    },
    {
      "id": "s2",
      "mention": "a wooden bench",
      "fact_ids": [
        "f2",
        "f4",
        "f5"
      ],
      "description": "The wooden bench on which the shoes rest."
    },
    {
      "id": "s3",
      "mention": "One pair of shoes is positioned on the left side of the bench",
      "fact_ids": [
        "f6"
      ],
      "description": "The pair of shoes on the left side of the bench."
    },
    {
      "id": "s4",
      "mention": "the other pair of shoes is on the right side",
      "fact_ids": [
        "f7"
      ],
      "description": "The pair of shoes on the right side of the bench."
    }
  ],
  "entity_alignment": [
    {
      "original_entity_ids": [
        "o1"
      ],
      "steer_entity_ids": [
        "s2"
      ],
      "status": "matched",
      "reason": "Both refer to the bench, described as wooden in both captions.",
      "global_entity": "g1"
    },
    {
      "original_entity_ids": [
        "o2"
      ],
      "steer_entity_ids": [
        "s1"
      ],
      "status": "matched",
      "reason": "Both refer to the two pairs of shoes as a group, placed on the bench.",
      "global_entity": "g2"
    },
    {
      "original_entity_ids": [
        "o3"
      ],
      "steer_entity_ids": [
        "s3"
      ],
      "status": "matched",
      "reason": "Both refer to the pair of shoes on the left side of the bench.",
      "global_entity": "g3"
    },
    {
      "original_entity_ids": [
        "o4"
      ],
      "steer_entity_ids": [
        "s4"
      ],
      "status": "matched",
      "reason": "Both refer to the pair of shoes on the right side of the bench.",
      "global_entity": "g4"
    },
    {
      "original_entity_ids": [
        "o5"
      ],
      "steer_entity_ids": [],
      "status": "original_only",
      "reason": "The grassy area is mentioned only in the original caption; the steer caption does not mention any location.",
      "global_entity": "g5"
    }
  ],
  "global_mapping": {
    "original": {
      "o1": "g1",
      "o2": "g2",
      "o3": "g3",
      "o4": "g4",
      "o5": "g5"
    },
    "steer": {
      "s2": "g1",
      "s1": "g2",
      "s3": "g3",
      "s4": "g4"
    }
  }
}
```

### 299573

```json
{
  "pair_id": "299573",
  "status": "ready",
  "original_entities": [
    {
      "id": "o1",
      "mention": "two giraffes",
      "fact_ids": [
        "f1",
        "f3",
        "f5",
        "f6",
        "f7",
        "f8",
        "f9",
        "f10",
        "f11"
      ],
      "description": "Two giraffes standing in a grassy field, one slightly behind the other, facing the same direction, close together."
    },
    {
      "id": "o2",
      "mention": "a grassy field",
      "fact_ids": [
        "f2",
        "f4",
        "f6",
        "f12",
        "f13"
      ],
      "description": "A grassy field filled with tall grass, providing habitat for the giraffes."
    }
  ],
  "steer_entities": [
    {
      "id": "s1",
      "mention": "Two giraffes",
      "fact_ids": [
        "f1",
        "f2",
        "f5",
        "f6",
        "f7"
      ],
      "description": "Two giraffes standing side by side in a grassy field."
    },
    {
      "id": "s2",
      "mention": "a grassy field",
      "fact_ids": [
        "f3",
        "f4",
        "f7"
      ],
      "description": "A grassy field where the giraffes stand."
    }
  ],
  "entity_alignment": [
    {
      "original_entity_ids": [
        "o1"
      ],
      "steer_entity_ids": [
        "s1"
      ],
      "status": "matched",
      "reason": "Both refer to the same two giraffes, described as standing in a grassy field; original adds relative positioning and facing direction, steer adds side-by-side arrangement.",
      "global_entity": "g1"
    },
    {
      "original_entity_ids": [
        "o2"
      ],
      "steer_entity_ids": [
        "s2"
      ],
      "status": "matched",
      "reason": "Both refer to the same grassy field where the giraffes are located; original adds tall grass and habitat role.",
      "global_entity": "g2"
    }
  ],
  "global_mapping": {
    "original": {
      "o1": "g1",
      "o2": "g2"
    },
    "steer": {
      "s1": "g1",
      "s2": "g2"
    }
  }
}
```

### 415015

```json
{
  "pair_id": "415015",
  "status": "ready",
  "original_entities": [
    {
      "id": "o1",
      "mention": "a vase",
      "fact_ids": [
        "f1",
        "f7",
        "f9",
        "f10"
      ],
      "description": "The vase that is filled with dried flowers, placed on a table, and positioned near a window."
    },
    {
      "id": "o2",
      "mention": "a variety of dried flowers",
      "fact_ids": [
        "f2",
        "f7",
        "f8"
      ],
      "description": "The dried flowers that fill the vase and include daisies and sunflowers."
    },
    {
      "id": "o3",
      "mention": "daisies",
      "fact_ids": [
        "f3",
        "f8"
      ],
      "description": "Daisies that are part of the dried flowers in the vase."
    },
    {
      "id": "o4",
      "mention": "sunflowers",
      "fact_ids": [
        "f4",
        "f8"
      ],
      "description": "Sunflowers that are part of the dried flowers in the vase."
    },
    {
      "id": "o5",
      "mention": "a table",
      "fact_ids": [
        "f5",
        "f9"
      ],
      "description": "The table on which the vase is placed."
    },
    {
      "id": "o6",
      "mention": "a window",
      "fact_ids": [
        "f6",
        "f10"
      ],
      "description": "The window near which the vase is positioned."
    }
  ],
  "steer_entities": [
    {
      "id": "s1",
      "mention": "a glass vase",
      "fact_ids": [
        "f1",
        "f6",
        "f7",
        "f8"
      ],
      "description": "The glass vase that is filled with flowers and grasses and placed on a table."
    },
    {
      "id": "s2",
      "mention": "various types of flowers",
      "fact_ids": [
        "f2",
        "f7",
        "f10"
      ],
      "description": "The flowers that fill the vase along with grasses."
    },
    {
      "id": "s3",
      "mention": "grasses",
      "fact_ids": [
        "f3",
        "f7",
        "f10"
      ],
      "description": "The grasses that fill the vase along with flowers."
    },
    {
      "id": "s4",
      "mention": "a table",
      "fact_ids": [
        "f4",
        "f8",
        "f9"
      ],
      "description": "The table on which the vase is placed and which is next to the window."
    },
    {
      "id": "s5",
      "mention": "a window",
      "fact_ids": [
        "f5",
        "f9"
      ],
      "description": "The window next to the table."
    }
  ],
  "entity_alignment": [
    {
      "original_entity_ids": [
        "o1"
      ],
      "steer_entity_ids": [
        "s1"
      ],
      "status": "matched",
      "reason": "Both refer to the vase that is filled with flowers and placed on a table; the steer adds the material 'glass' but the core referent is the same.",
      "global_entity": "g1"
    },
    {
      "original_entity_ids": [
        "o2"
      ],
      "steer_entity_ids": [
        "s2"
      ],
      "status": "matched",
      "reason": "Both refer to the flowers inside the vase; original specifies 'dried' and includes daisies and sunflowers, while steer says 'various types' but the referent is the same flower arrangement.",
      "global_entity": "g2"
    },
    {
      "original_entity_ids": [
        "o3",
        "o4"
      ],
      "steer_entity_ids": [
        "s3"
      ],
      "status": "ambiguous",
      "reason": "Original mentions daisies and sunflowers as specific flowers, while steer mentions grasses; these are different types of plant material, so no direct match is certain.",
      "global_entity": null
    },
    {
      "original_entity_ids": [
        "o5"
      ],
      "steer_entity_ids": [
        "s4"
      ],
      "status": "matched",
      "reason": "Both refer to the table on which the vase is placed.",
      "global_entity": "g4"
    },
    {
      "original_entity_ids": [
        "o6"
      ],
      "steer_entity_ids": [
        "s5"
      ],
      "status": "matched",
      "reason": "Both refer to the window near the table/vase.",
      "global_entity": "g5"
    }
  ],
  "global_mapping": {
    "original": {
      "o1": "g1",
      "o2": "g2",
      "o3": null,
      "o4": null,
      "o5": "g4",
      "o6": "g5"
    },
    "steer": {
      "s1": "g1",
      "s2": "g2",
      "s3": null,
      "s4": "g4",
      "s5": "g5"
    }
  }
}
```

### 581451

```json
{
  "pair_id": "581451",
  "status": "failed",
  "error": "original-only shape"
}
```

## Fact Alignment（完整状态；非人工准确率）

### 415015 — needs_review

| status / reason | Vanilla | Steer |
| --- | --- | --- |
| modified / value_changed | f1: There is a vase. | f1: There is a glass vase. |
| modified / value_changed | f2: There are dried flowers. | f2: There are flowers. |
| ambiguous / entity_uncertain | f3: There are daisies. ; f4: There are sunflowers. | f3: There are grasses. |
| retained / same_fact | f5: There is a table. | f4: There is a table. |
| retained / same_fact | f6: There is a window. | f5: There is a window. |
| retained / same_fact | f9: The vase is placed on the table. | f8: The vase is placed on the table. |
| removed / not_expressed | f12: The combination of the vase, flowers, and the window creates a pleasant and inviting atmosphere. |  |
| added / not_expressed |  | f6: The vase is made of glass. |
| ambiguous / alignment_validation_error | f7: The vase is filled with dried flowers. |  |
| ambiguous / alignment_validation_error | f8: The dried flowers include daisies and sunflowers. |  |
| ambiguous / alignment_validation_error | f10: The vase is positioned near the window. |  |
| ambiguous / alignment_validation_error | f11: The flowers are arranged in a visually appealing manner. |  |
| ambiguous / alignment_validation_error |  | f7: The vase is filled with flowers and grasses. |
| ambiguous / alignment_validation_error |  | f9: The table is next to the window. |
| ambiguous / alignment_validation_error |  | f10: The flowers and grasses are arranged in such a way that they create a visually appealing bouquet. |
拒绝的对应（保留原始响应，回退 ambiguous）：
```json
[
  {
    "index": 5,
    "raw": {
      "original_fact_ids": [
        "f7"
      ],
      "steer_fact_ids": [
        "f7"
      ],
      "status": "modified",
      "reason": "value_changed",
      "evidence": [
        {
          "side": "original",
          "quote": "a vase filled with a variety of dried flowers"
        },
        {
          "side": "steer",
          "quote": "a glass vase filled with various types of flowers and grasses"
        }
      ]
    },
    "error": "uncertain entity cannot support a confident status"
  },
  {
    "index": 6,
    "raw": {
      "original_fact_ids": [
        "f8"
      ],
      "steer_fact_ids": [],
      "status": "removed",
      "reason": "not_expressed",
      "evidence": [
        {
          "side": "original",
          "quote": "a variety of dried flowers, including daisies and sunflowers"
        }
      ]
    },
    "error": "uncertain entity cannot support a confident status"
  },
  {
    "index": 8,
    "raw": {
      "original_fact_ids": [
        "f10"
      ],
      "steer_fact_ids": [
        "f9"
      ],
      "status": "modified",
      "reason": "value_changed",
      "evidence": [
        {
          "side": "original",
          "quote": "The vase is positioned near a window"
        },
        {
          "side": "steer",
          "quote": "a table next to a window"
        }
      ]
    },
    "error": "retained/modified require same ordered global participants"
  },
  {
    "index": 9,
    "raw": {
      "original_fact_ids": [
        "f11"
      ],
      "steer_fact_ids": [
        "f10"
      ],
      "status": "modified",
      "reason": "value_changed",
      "evidence": [
        {
          "side": "original",
          "quote": "the flowers are arranged in a visually appealing manner"
        },
        {
          "side": "steer",
          "quote": "The flowers and grasses are arranged in such a way that they create a visually appealing bouquet"
        }
      ]
    },
    "error": "uncertain entity cannot support a confident status"
  }
]
```

### 299573 — ready

| status / reason | Vanilla | Steer |
| --- | --- | --- |
| retained / same_fact | f1: There are two giraffes. | f1: There are giraffes. |
| retained / same_fact | f2: There is a grassy field. | f3: There is a grassy field. |
| retained / same_fact | f3: There are two giraffes. | f2: There are two giraffes. |
| retained / same_fact | f4: The field is grassy. | f4: The field is grassy. |
| retained / same_fact | f5: The giraffes are standing. | f5: The giraffes are standing. |
| retained / same_fact | f6: The giraffes are in the grassy field. | f7: The giraffes are in the grassy field. |
| modified / value_changed | f7: One giraffe is positioned slightly behind the other. | f6: The giraffes are side by side. |
| removed / not_expressed | f8: Both giraffes are facing the same direction. |  |
| removed / not_expressed | f9: The giraffes are possibly looking at something in the distance. |  |
| removed / not_expressed | f10: The giraffes are standing close to each other. |  |
| removed / not_expressed | f11: The giraffes create a sense of companionship. |  |
| removed / not_expressed | f12: The field is filled with tall grass. |  |
| removed / not_expressed | f13: The field provides a natural habitat for the giraffes. |  |
| removed / not_expressed | cov_f1: The grass is tall. |  |

### 581451 — failed

| status / reason | Vanilla | Steer |
| --- | --- | --- |
| ambiguous / stage_failed | f1: There is a hot dog. |  |
| ambiguous / stage_failed | f2: There is a bun. |  |
| ambiguous / stage_failed | f3: There is ketchup. |  |
| ambiguous / stage_failed | f4: There are green peppers. |  |
| ambiguous / stage_failed | f5: There is a piece of paper. |  |
| ambiguous / stage_failed | f6: There is a napkin. |  |
| ambiguous / stage_failed | f7: The hot dog has a bun. |  |
| ambiguous / stage_failed | f8: The hot dog is topped with ketchup. |  |
| ambiguous / stage_failed | f9: The hot dog is topped with green peppers. |  |
| ambiguous / stage_failed | f10: The peppers are green. |  |
| ambiguous / stage_failed | f11: The hot dog is placed on the piece of paper. |  |
| ambiguous / stage_failed | f12: The piece of paper is likely a napkin. |  |
| ambiguous / stage_failed | f13: The hot dog is positioned in the center of the image. |  |
| ambiguous / stage_failed | f14: The peppers are scattered around the hot dog. |  |
| ambiguous / stage_failed | f15: The peppers add a colorful and appetizing touch to the dish. |  |
| ambiguous / stage_failed |  | f1: There is a person. |
| ambiguous / stage_failed |  | f2: There is a hot dog. |
| ambiguous / stage_failed |  | f3: There is ketchup. |
| ambiguous / stage_failed |  | f4: There are peppers. |
| ambiguous / stage_failed |  | f5: The person is holding the hot dog. |
| ambiguous / stage_failed |  | f6: The hot dog has ketchup on it. |
| ambiguous / stage_failed |  | f7: The hot dog has peppers on it. |
失败：entity alignment failed

### 417586 — needs_review

| status / reason | Vanilla | Steer |
| --- | --- | --- |
| retained / same_fact | f1: There is a bench. | f2: There is a bench. |
| retained / same_fact | f2: There are shoes. | f1: There are shoes. |
| retained / same_fact | f3: The bench is wooden. | f4: The bench is wooden. |
| retained / same_fact | f4: There are two pairs of the described shoes. | f3: There are two pairs of the described shoes. |
| retained / same_fact | f5: The shoes are on the bench. | f5: The shoes are on the bench. |
| retained / same_fact | f7: One pair of shoes is located towards the left side of the bench. | f6: One pair of shoes is on the left side of the bench. |
| retained / same_fact | f8: The other pair of shoes is on the right side of the bench. | f7: The other pair of shoes is on the right side of the bench. |
| removed / not_expressed | f6: The shoes are positioned close to each other. |  |
| removed / not_expressed | f9: The bench appears to be made of wood. |  |
| removed / not_expressed | f10: The bench is situated in a grassy area. |  |
| removed / not_expressed | f11: The grassy area is possibly a park or a garden. |  |
| removed / not_expressed | f12: The shoes seem to be old. |  |
| removed / not_expressed | f14: The shoes suggest that they have been used for a long time. |  |
| added / not_expressed |  | f8: Both pairs of shoes are black. |
| ambiguous / alignment_validation_error | f13: The shoes seem to be worn. |  |
拒绝的对应（保留原始响应，回退 ambiguous）：
```json
[
  {
    "index": 12,
    "raw": {
      "original_fact_ids": [
        "f13"
      ],
      "steer_fact_ids": [],
      "status": "removed",
      "reason": "not_expressed",
      "evidence": [
        {
          "side": "original",
          "quote": "The shoes seem to be worn"
        }
      ]
    },
    "error": "evidence must be from that caption"
  }
]
```
