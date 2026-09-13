# 下游 eight-shot 示例

助手编写的合成演示，不是人工 gold。每阶段 8 个演示，覆盖 8 个场景、16 条新 caption。测试集的 8 条原文不在演示中。例子针对已知开发集问题设计，不能据此声称独立泛化。

## helmet_color

Original: A white helmet rests on a crate.

Steer: A blue helmet rests on a crate.

Coverage 追加：{"added_elements": [{"category": "color", "fact": "The helmet is white.", "source": "white helmet", "assertion": "asserted", "polarity": "positive"}]}

Alignment 演示：
```json
[
  {
    "original_fact_ids": [
      "f1"
    ],
    "steer_fact_ids": [
      "f1"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f2"
    ],
    "steer_fact_ids": [
      "f2"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f3"
    ],
    "steer_fact_ids": [
      "f3"
    ],
    "status": "modified",
    "reason": "value_changed",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f4"
    ],
    "steer_fact_ids": [
      "f4"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  }
]
```

## roles_and_order

Original: A nurse holds a folder. A pilot holds a radio.

Steer: A pilot carries a radio, while a nurse carries a folder.

Coverage 追加：{"added_elements": []}

Alignment 演示：
```json
[
  {
    "original_fact_ids": [
      "f1"
    ],
    "steer_fact_ids": [
      "f2"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f2"
    ],
    "steer_fact_ids": [
      "f1"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f3"
    ],
    "steer_fact_ids": [
      "f4"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f4"
    ],
    "steer_fact_ids": [
      "f3"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f5"
    ],
    "steer_fact_ids": [
      "f6"
    ],
    "status": "ambiguous",
    "reason": "partial_overlap",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f6"
    ],
    "steer_fact_ids": [
      "f5"
    ],
    "status": "ambiguous",
    "reason": "partial_overlap",
    "evidence": []
  }
]
```

## uncertain_child

Original: A child holds a kite. Another child holds a balloon.

Steer: A child is smiling.

Coverage 追加：{"added_elements": [{"category": "object", "fact": "There is a kite.", "source": "a kite", "assertion": "asserted", "polarity": "positive"}]}

Alignment 演示：
```json
[
  {
    "original_fact_ids": [
      "f1",
      "f2"
    ],
    "steer_fact_ids": [
      "f1"
    ],
    "status": "ambiguous",
    "reason": "entity_uncertain",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f3"
    ],
    "steer_fact_ids": [],
    "status": "removed",
    "reason": "not_expressed",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f4"
    ],
    "steer_fact_ids": [],
    "status": "removed",
    "reason": "not_expressed",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f5",
      "f6"
    ],
    "steer_fact_ids": [
      "f2"
    ],
    "status": "ambiguous",
    "reason": "entity_uncertain",
    "evidence": []
  }
]
```

## embedded_material

Original: A metal lantern is on a cabinet.

Steer: A lantern is on a cabinet.

Coverage 追加：{"added_elements": [{"category": "material", "fact": "The lantern is metal.", "source": "metal lantern", "assertion": "asserted", "polarity": "positive"}]}

Alignment 演示：
```json
[
  {
    "original_fact_ids": [
      "f1"
    ],
    "steer_fact_ids": [
      "f1"
    ],
    "status": "ambiguous",
    "reason": "granularity",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f2"
    ],
    "steer_fact_ids": [
      "f2"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f3"
    ],
    "steer_fact_ids": [],
    "status": "removed",
    "reason": "not_expressed",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f4"
    ],
    "steer_fact_ids": [
      "f3"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  }
]
```

## missing_color_in_other_extraction

Original: A violet curtain hangs beside a door.

Steer: A purple curtain hangs next to a door.

Coverage 追加：{"added_elements": []}

Alignment 演示：
```json
[
  {
    "original_fact_ids": [
      "f1"
    ],
    "steer_fact_ids": [
      "f1"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f2"
    ],
    "steer_fact_ids": [
      "f2"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f3"
    ],
    "steer_fact_ids": [],
    "status": "ambiguous",
    "reason": "extraction_gap",
    "evidence": [
      {
        "side": "steer",
        "quote": "purple curtain"
      }
    ]
  },
  {
    "original_fact_ids": [
      "f4"
    ],
    "steer_fact_ids": [
      "f3"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  }
]
```

## many_to_one_partial_information

Original: Two cyclists ride next to each other on a path.

Steer: Two cyclists ride side by side on a path.

Coverage 追加：{"added_elements": [{"category": "spatial", "fact": "The cyclists are next to each other.", "source": "next to each other", "assertion": "asserted", "polarity": "positive"}]}

Alignment 演示：
```json
[
  {
    "original_fact_ids": [
      "f1"
    ],
    "steer_fact_ids": [
      "f1"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f2"
    ],
    "steer_fact_ids": [
      "f2"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f3"
    ],
    "steer_fact_ids": [
      "f3"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f4",
      "f5"
    ],
    "steer_fact_ids": [
      "f4"
    ],
    "status": "ambiguous",
    "reason": "granularity",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f6"
    ],
    "steer_fact_ids": [
      "f5"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  }
]
```

## one_sided_and_conjoined_speculation

Original: A parcel rests on a mat. The mat may be a towel. The parcel seems to be dented and torn.

Steer: A courier carries a parcel.

Coverage 追加：{"added_elements": [{"category": "state", "fact": "The parcel seems torn.", "source": "The parcel seems to be dented and torn", "assertion": "speculative", "polarity": "positive"}]}

Alignment 演示：
```json
[
  {
    "original_fact_ids": [
      "f1"
    ],
    "steer_fact_ids": [
      "f2"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f2"
    ],
    "steer_fact_ids": [],
    "status": "removed",
    "reason": "not_expressed",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f3"
    ],
    "steer_fact_ids": [],
    "status": "removed",
    "reason": "not_expressed",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f4"
    ],
    "steer_fact_ids": [],
    "status": "removed",
    "reason": "not_expressed",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f5"
    ],
    "steer_fact_ids": [],
    "status": "removed",
    "reason": "not_expressed",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f6"
    ],
    "steer_fact_ids": [],
    "status": "removed",
    "reason": "not_expressed",
    "evidence": [
      {
        "side": "original",
        "quote": "The parcel seems to be dented and torn"
      }
    ]
  },
  {
    "original_fact_ids": [
      "f7"
    ],
    "steer_fact_ids": [],
    "status": "removed",
    "reason": "not_expressed",
    "evidence": [
      {
        "side": "original",
        "quote": "The parcel seems to be dented and torn"
      }
    ]
  },
  {
    "original_fact_ids": [],
    "steer_fact_ids": [
      "f1"
    ],
    "status": "added",
    "reason": "not_expressed",
    "evidence": []
  },
  {
    "original_fact_ids": [],
    "steer_fact_ids": [
      "f3"
    ],
    "status": "added",
    "reason": "not_expressed",
    "evidence": []
  }
]
```

## count_with_unit

Original: Three pairs of gloves lie on a shelf.

Steer: Two pairs of gloves lie on a shelf.

Coverage 追加：{"added_elements": [{"category": "counting", "fact": "There are 3 pairs of gloves.", "source": "Three pairs of gloves", "assertion": "asserted", "polarity": "positive"}]}

Alignment 演示：
```json
[
  {
    "original_fact_ids": [
      "f1"
    ],
    "steer_fact_ids": [
      "f1"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f2"
    ],
    "steer_fact_ids": [
      "f2"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f3"
    ],
    "steer_fact_ids": [
      "f3"
    ],
    "status": "modified",
    "reason": "value_changed",
    "evidence": []
  },
  {
    "original_fact_ids": [
      "f4"
    ],
    "steer_fact_ids": [
      "f4"
    ],
    "status": "retained",
    "reason": "same_fact",
    "evidence": []
  }
]
```

完整模型消息中的输入/输出见 coverage.jsonl、entities.jsonl、alignment.jsonl。零示例使用完全相同的系统规则和校验器，仅省略这8组演示消息。
