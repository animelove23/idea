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
    "ready": 4
  },
  "alignment_status": {
    "ready": 2,
    "needs_review": 2
  },
  "alignment_rows_all": {
    "added": 5,
    "ambiguous": 10,
    "modified": 0,
    "removed": 26,
    "retained": 21
  },
  "alignment_rows_main": {
    "added": 5,
    "ambiguous": 9,
    "modified": 0,
    "removed": 20,
    "retained": 21
  },
  "main_fact_status_counts": {
    "original": {
      "added": 0,
      "ambiguous": 7,
      "modified": 0,
      "removed": 20,
      "retained": 21
    },
    "steer": {
      "added": 5,
      "ambiguous": 5,
      "modified": 0,
      "removed": 0,
      "retained": 21
    }
  },
  "extraction_gap_rows": 0,
  "contextual_references": 1,
  "equivalent_fact_groups": 0,
  "api_calls": 16,
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
        "f5",
        "f7",
        "f8",
        "f9",
        "f10"
      ],
      "description": "bench supporting shoes"
    },
    {
      "id": "o2",
      "mention": "two pairs of shoes",
      "fact_ids": [
        "f2",
        "f4",
        "f5",
        "f6",
        "f7",
        "f8",
        "f12",
        "f13",
        "f14"
      ],
      "description": "shoe group on bench"
    },
    {
      "id": "o3",
      "mention": "one pair",
      "fact_ids": [
        "f7"
      ],
      "description": "left pair of shoes"
    },
    {
      "id": "o4",
      "mention": "the other pair",
      "fact_ids": [
        "f8"
      ],
      "description": "right pair of shoes"
    }
  ],
  "steer_entities": [
    {
      "id": "s1",
      "mention": "a wooden bench",
      "fact_ids": [
        "f2",
        "f4",
        "f5",
        "f6",
        "f7"
      ],
      "description": "bench supporting shoes"
    },
    {
      "id": "s2",
      "mention": "two pairs of shoes",
      "fact_ids": [
        "f1",
        "f3",
        "f5",
        "f6",
        "f7",
        "f8"
      ],
      "description": "shoe group on bench"
    },
    {
      "id": "s3",
      "mention": "One pair of shoes",
      "fact_ids": [
        "f6"
      ],
      "description": "left pair of shoes"
    },
    {
      "id": "s4",
      "mention": "the other pair of shoes",
      "fact_ids": [
        "f7"
      ],
      "description": "right pair of shoes"
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
      "reason": "Same wooden bench.",
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
      "reason": "Same shoe group on bench.",
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
      "reason": "Left pair of shoes.",
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
      "reason": "Right pair of shoes.",
      "global_entity": "g4"
    }
  ],
  "global_mapping": {
    "original": {
      "o1": "g1",
      "o2": "g2",
      "o3": "g3",
      "o4": "g4"
    },
    "steer": {
      "s1": "g1",
      "s2": "g2",
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
        "f11",
        "f13"
      ],
      "description": "pair of giraffes in field"
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
      "description": "field containing giraffes"
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
      "description": "pair of giraffes in field"
    },
    {
      "id": "s2",
      "mention": "a grassy field",
      "fact_ids": [
        "f3",
        "f4",
        "f7"
      ],
      "description": "field containing giraffes"
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
      "reason": "Same pair of giraffes in the same field.",
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
      "reason": "Same grassy field.",
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
      "description": "vase filled with dried flowers, on table near window"
    },
    {
      "id": "o2",
      "mention": "a variety of dried flowers",
      "fact_ids": [
        "f2",
        "f7",
        "f8"
      ],
      "description": "dried flowers in vase, including daisies and sunflowers"
    },
    {
      "id": "o3",
      "mention": "daisies",
      "fact_ids": [
        "f3",
        "f8"
      ],
      "description": "daisies among dried flowers"
    },
    {
      "id": "o4",
      "mention": "sunflowers",
      "fact_ids": [
        "f4",
        "f8"
      ],
      "description": "sunflowers among dried flowers"
    },
    {
      "id": "o5",
      "mention": "a table",
      "fact_ids": [
        "f5",
        "f9"
      ],
      "description": "table supporting vase"
    },
    {
      "id": "o6",
      "mention": "a window",
      "fact_ids": [
        "f6",
        "f10"
      ],
      "description": "window near vase"
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
      "description": "glass vase filled with flowers and grasses, on table"
    },
    {
      "id": "s2",
      "mention": "various types of flowers",
      "fact_ids": [
        "f2",
        "f7"
      ],
      "description": "flowers in vase"
    },
    {
      "id": "s3",
      "mention": "grasses",
      "fact_ids": [
        "f3",
        "f7"
      ],
      "description": "grasses in vase"
    },
    {
      "id": "s4",
      "mention": "a table",
      "fact_ids": [
        "f4",
        "f8",
        "f9"
      ],
      "description": "table supporting vase, next to window"
    },
    {
      "id": "s5",
      "mention": "a window",
      "fact_ids": [
        "f5",
        "f9"
      ],
      "description": "window next to table"
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
      "reason": "Same vase, both filled with flowers and placed on table near window.",
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
      "reason": "Both refer to the flowers filling the vase.",
      "global_entity": "g2"
    },
    {
      "original_entity_ids": [
        "o3"
      ],
      "steer_entity_ids": [],
      "status": "original_only",
      "reason": "Daisies not mentioned in steer.",
      "global_entity": "g3"
    },
    {
      "original_entity_ids": [
        "o4"
      ],
      "steer_entity_ids": [],
      "status": "original_only",
      "reason": "Sunflowers not mentioned in steer.",
      "global_entity": "g4"
    },
    {
      "original_entity_ids": [
        "o5"
      ],
      "steer_entity_ids": [
        "s4"
      ],
      "status": "matched",
      "reason": "Same table supporting the vase.",
      "global_entity": "g5"
    },
    {
      "original_entity_ids": [
        "o6"
      ],
      "steer_entity_ids": [
        "s5"
      ],
      "status": "matched",
      "reason": "Same window near the vase/table.",
      "global_entity": "g6"
    },
    {
      "original_entity_ids": [],
      "steer_entity_ids": [
        "s3"
      ],
      "status": "steer_only",
      "reason": "Grasses not mentioned in original.",
      "global_entity": "g7"
    }
  ],
  "global_mapping": {
    "original": {
      "o1": "g1",
      "o2": "g2",
      "o3": "g3",
      "o4": "g4",
      "o5": "g5",
      "o6": "g6"
    },
    "steer": {
      "s1": "g1",
      "s2": "g2",
      "s4": "g5",
      "s5": "g6",
      "s3": "g7"
    }
  }
}
```

### 581451

```json
{
  "pair_id": "581451",
  "status": "ready",
  "original_entities": [
    {
      "id": "o1",
      "mention": "a hot dog",
      "fact_ids": [
        "f1",
        "f7",
        "f8",
        "f9",
        "f11",
        "f13",
        "f14"
      ],
      "description": "hot dog with bun and toppings"
    },
    {
      "id": "o2",
      "mention": "a bun",
      "fact_ids": [
        "f2",
        "f7"
      ],
      "description": "bun of hot dog"
    },
    {
      "id": "o3",
      "mention": "ketchup",
      "fact_ids": [
        "f3",
        "f8"
      ],
      "description": "ketchup topping"
    },
    {
      "id": "o4",
      "mention": "green peppers",
      "fact_ids": [
        "f4",
        "f9",
        "f10",
        "f14",
        "f15"
      ],
      "description": "green pepper topping"
    },
    {
      "id": "o5",
      "mention": "a piece of paper",
      "fact_ids": [
        "f5",
        "f11",
        "f12"
      ],
      "description": "paper under hot dog"
    },
    {
      "id": "o6",
      "mention": "a napkin",
      "fact_ids": [
        "f6",
        "f12"
      ],
      "description": "speculative napkin identity"
    }
  ],
  "steer_entities": [
    {
      "id": "s1",
      "mention": "A person",
      "fact_ids": [
        "f1",
        "f5"
      ],
      "description": "person holding hot dog"
    },
    {
      "id": "s2",
      "mention": "a hot dog",
      "fact_ids": [
        "f2",
        "f5",
        "f6",
        "f7"
      ],
      "description": "held hot dog"
    },
    {
      "id": "s3",
      "mention": "ketchup",
      "fact_ids": [
        "f3",
        "f6"
      ],
      "description": "ketchup on hot dog"
    },
    {
      "id": "s4",
      "mention": "peppers",
      "fact_ids": [
        "f4",
        "f7"
      ],
      "description": "peppers on hot dog"
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
      "reason": "Same hot dog with ketchup and peppers.",
      "global_entity": "g1"
    },
    {
      "original_entity_ids": [
        "o3"
      ],
      "steer_entity_ids": [
        "s3"
      ],
      "status": "matched",
      "reason": "Same ketchup topping.",
      "global_entity": "g2"
    },
    {
      "original_entity_ids": [
        "o4"
      ],
      "steer_entity_ids": [
        "s4"
      ],
      "status": "matched",
      "reason": "Same peppers topping.",
      "global_entity": "g3"
    },
    {
      "original_entity_ids": [
        "o2"
      ],
      "steer_entity_ids": [],
      "status": "original_only",
      "reason": "Bun not mentioned in steer.",
      "global_entity": "g4"
    },
    {
      "original_entity_ids": [
        "o5"
      ],
      "steer_entity_ids": [],
      "status": "original_only",
      "reason": "Paper not mentioned in steer.",
      "global_entity": "g5"
    },
    {
      "original_entity_ids": [
        "o6"
      ],
      "steer_entity_ids": [],
      "status": "original_only",
      "reason": "Napkin not mentioned in steer.",
      "global_entity": "g6"
    },
    {
      "original_entity_ids": [],
      "steer_entity_ids": [
        "s1"
      ],
      "status": "steer_only",
      "reason": "Person not mentioned in original.",
      "global_entity": "g7"
    }
  ],
  "global_mapping": {
    "original": {
      "o1": "g1",
      "o3": "g2",
      "o4": "g3",
      "o2": "g4",
      "o5": "g5",
      "o6": "g6"
    },
    "steer": {
      "s2": "g1",
      "s3": "g2",
      "s4": "g3",
      "s1": "g7"
    }
  }
}
```

## Fact Alignment（完整状态；非人工准确率）

### 415015 — needs_review

| status / reason | Vanilla | Steer |
| --- | --- | --- |
| retained / same_fact | f1: There is a vase. | f1: There is a glass vase. |
| retained / same_fact | f2: There are dried flowers. | f2: There are flowers. |
| removed / not_expressed | f3: There are daisies. |  |
| removed / not_expressed | f4: There are sunflowers. |  |
| retained / same_fact | f5: There is a table. | f4: There is a table. |
| retained / same_fact | f6: There is a window. | f5: There is a window. |
| removed / not_expressed | f8: The dried flowers include daisies and sunflowers. |  |
| retained / same_fact | f9: The vase is placed on the table. | f8: The vase is placed on the table. |
| removed / not_expressed | f12: The combination of the vase, flowers, and the window creates a pleasant and inviting atmosphere. |  |
| added / not_expressed |  | f3: There are grasses. |
| added / not_expressed |  | f6: The vase is made of glass. |
| ambiguous / partial_overlap | f10: The vase is positioned near the window. | f9: The table is next to the window. |
| ambiguous / partial_overlap | f11: The flowers are arranged in a visually appealing manner. | f10: The flowers and grasses are arranged in such a way that they create a visually appealing bouquet. |
| ambiguous / alignment_validation_error | f7: The vase is filled with dried flowers. |  |
| ambiguous / alignment_validation_error |  | f7: The vase is filled with flowers and grasses. |
拒绝的对应（保留原始响应，回退 ambiguous）：
```json
[
  {
    "index": 6,
    "raw": {
      "original_fact_ids": [
        "f7"
      ],
      "steer_fact_ids": [
        "f7"
      ],
      "status": "modified",
      "reason": "value_changed",
      "evidence": []
    },
    "error": "retained/modified require same ordered global participants"
  }
]
```

### 299573 — needs_review

| status / reason | Vanilla | Steer |
| --- | --- | --- |
| retained / same_fact | f2: There is a grassy field. | f3: There is a grassy field. |
| retained / same_fact | f4: The field is grassy. | f4: The field is grassy. |
| retained / same_fact | f5: The giraffes are standing. | f5: The giraffes are standing. |
| retained / same_fact | f6: The giraffes are in the grassy field. | f7: The giraffes are in the grassy field. |
| removed / not_expressed | f8: Both giraffes are facing the same direction. |  |
| removed / not_expressed | f9: The giraffes are possibly looking at something in the distance. |  |
| removed / not_expressed | f11: The giraffes create a sense of companionship. |  |
| removed / not_expressed | f12: The field is filled with tall grass. |  |
| removed / not_expressed | f13: The field provides a natural habitat for the giraffes. |  |
| removed / not_expressed | cov_f1: The grass is tall. |  |
| ambiguous / partial_overlap | f7: One giraffe is positioned slightly behind the other. ; f10: The giraffes are standing close to each other. | f6: The giraffes are side by side. |
| ambiguous / alignment_validation_error | f1: There are two giraffes. |  |
| ambiguous / alignment_validation_error | f3: There are two giraffes. |  |
| ambiguous / alignment_validation_error |  | f1: There are giraffes. |
| ambiguous / alignment_validation_error |  | f2: There are two giraffes. |
拒绝的对应（保留原始响应，回退 ambiguous）：
```json
[
  {
    "index": 0,
    "raw": {
      "original_fact_ids": [
        "f1",
        "f3"
      ],
      "steer_fact_ids": [
        "f1",
        "f2"
      ],
      "status": "retained",
      "reason": "same_fact",
      "evidence": []
    },
    "error": "different main types require ambiguous correspondence"
  }
]
```

### 581451 — ready

| status / reason | Vanilla | Steer |
| --- | --- | --- |
| retained / same_fact | f1: There is a hot dog. | f2: There is a hot dog. |
| removed / not_expressed | f2: There is a bun. |  |
| retained / same_fact | f3: There is ketchup. | f3: There is ketchup. |
| retained / same_fact | f4: There are green peppers. | f4: There are peppers. |
| removed / not_expressed | f5: There is a piece of paper. |  |
| removed / not_expressed | f6: There is a napkin. |  |
| removed / not_expressed | f7: The hot dog has a bun. |  |
| retained / same_fact | f8: The hot dog is topped with ketchup. | f6: The hot dog has ketchup on it. |
| retained / same_fact | f9: The hot dog is topped with green peppers. | f7: The hot dog has peppers on it. |
| removed / not_expressed | f10: The peppers are green. |  |
| removed / not_expressed | f11: The hot dog is placed on the piece of paper. |  |
| removed / not_expressed | f12: The piece of paper is likely a napkin. |  |
| removed / not_expressed | f13: The hot dog is positioned in the center of the image. |  |
| removed / not_expressed | f14: The peppers are scattered around the hot dog. |  |
| removed / not_expressed | f15: The peppers add a colorful and appetizing touch to the dish. |  |
| added / not_expressed |  | f1: There is a person. |
| added / not_expressed |  | f5: The person is holding the hot dog. |

### 417586 — ready

| status / reason | Vanilla | Steer |
| --- | --- | --- |
| retained / same_fact | f1: There is a bench. | f2: There is a bench. |
| retained / same_fact | f2: There are shoes. | f1: There are shoes. |
| retained / same_fact | f3: The bench is wooden. | f4: The bench is wooden. |
| retained / same_fact | f4: There are two pairs of the described shoes. | f3: There are two pairs of the described shoes. |
| retained / same_fact | f5: The shoes are on the bench. | f5: The shoes are on the bench. |
| removed / not_expressed | f6: The shoes are positioned close to each other. |  |
| retained / same_fact | f7: One pair of shoes is located towards the left side of the bench. | f6: One pair of shoes is on the left side of the bench. |
| retained / same_fact | f8: The other pair of shoes is on the right side of the bench. | f7: The other pair of shoes is on the right side of the bench. |
| removed / not_expressed | f10: The bench is situated in a grassy area. |  |
| removed / not_expressed | f11: The grassy area is possibly a park or a garden. |  |
| removed / not_expressed | f12: The shoes seem to be old. |  |
| removed / not_expressed | f13: The shoes seem to be worn. |  |
| removed / not_expressed | f14: The shoes suggest that they have been used for a long time. |  |
| added / not_expressed |  | f8: Both pairs of shoes are black. |
| ambiguous / qualifier_difference | f9: The bench appears to be made of wood. |  |

关联引用（不重复计作主对齐；语气等限定保留）：
```json
[
  {
    "original_fact_ids": [
      "f9"
    ],
    "steer_fact_ids": [
      "f4"
    ],
    "status": "ambiguous",
    "reason": "qualifier_difference",
    "evidence": [],
    "type": "attribute",
    "types": [
      "attribute"
    ],
    "in_main": true,
    "global_entity_ids": [
      "g1"
    ],
    "role": "contextual_reference",
    "counted_as_primary_alignment": false,
    "shared_fact_ids": [
      {
        "side": "steer",
        "fact_id": "f4"
      }
    ],
    "qualifiers": {
      "original": [
        {
          "fact_id": "f9",
          "assertion": "speculative",
          "polarity": "positive"
        }
      ],
      "steer": [
        {
          "fact_id": "f4",
          "assertion": "asserted",
          "polarity": "positive"
        }
      ]
    }
  }
]
```

本轮真实 pair 未观察到 modified；不编造实际例子，见本地 contract tests 中的受控案例。
