# Few-shot与候选参考审核入口

当前全部为助手起草候选，**没有冒充人工gold**。每例完整输入、输出均保存在下方；不在此文件修改运行过的JSONL。

审核结论请另存：example_id/case_id、accept或reject、理由、修订版本；未审核条目保持pending。

## decompose：固定示例

### d1 — 只声明实体存在，不补属性

人工审核：pending。

```json
{
  "example_id": "d1",
  "reference_status": "assistant_authored_candidate",
  "input": {
    "text": "A car."
  },
  "output": {
    "entities": [
      {
        "id": "e1",
        "name": "car",
        "mentions": [
          {
            "quote": "car",
            "occurrence": 0
          }
        ]
      }
    ],
    "attributes": [],
    "excluded": []
  }
}
```

### d2 — small和red分别计size/color

人工审核：pending。

```json
{
  "example_id": "d2",
  "reference_status": "assistant_authored_candidate",
  "input": {
    "text": "A small red car."
  },
  "output": {
    "entities": [
      {
        "id": "e1",
        "name": "car",
        "mentions": [
          {
            "quote": "car",
            "occurrence": 0
          }
        ]
      }
    ],
    "attributes": [
      {
        "id": "a1",
        "entity_id": "e1",
        "slot": "size",
        "value": "small",
        "evidence": [
          {
            "quote": "small red car",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "small",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "a2",
        "entity_id": "e1",
        "slot": "color",
        "value": "red",
        "evidence": [
          {
            "quote": "red car",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "red",
            "occurrence": 0
          }
        ]
      }
    ],
    "excluded": []
  }
}
```

### d3 — wooden计material，不另造wood实体

人工审核：pending。

```json
{
  "example_id": "d3",
  "reference_status": "assistant_authored_candidate",
  "input": {
    "text": "A wooden table."
  },
  "output": {
    "entities": [
      {
        "id": "e1",
        "name": "table",
        "mentions": [
          {
            "quote": "table",
            "occurrence": 0
          }
        ]
      }
    ],
    "attributes": [
      {
        "id": "a1",
        "entity_id": "e1",
        "slot": "material",
        "value": "wood",
        "evidence": [
          {
            "quote": "wooden table",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "wooden",
            "occurrence": 0
          }
        ]
      }
    ],
    "excluded": []
  }
}
```

### d4 — round与made of wood分slot；词性不决定类别

人工审核：pending。

```json
{
  "example_id": "d4",
  "reference_status": "assistant_authored_candidate",
  "input": {
    "text": "A round table made of wood."
  },
  "output": {
    "entities": [
      {
        "id": "e1",
        "name": "table",
        "mentions": [
          {
            "quote": "table",
            "occurrence": 0
          }
        ]
      }
    ],
    "attributes": [
      {
        "id": "a1",
        "entity_id": "e1",
        "slot": "shape",
        "value": "round",
        "evidence": [
          {
            "quote": "round table",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "round",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "a2",
        "entity_id": "e1",
        "slot": "material",
        "value": "wood",
        "evidence": [
          {
            "quote": "table made of wood",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "wood",
            "occurrence": 0
          }
        ]
      }
    ],
    "excluded": []
  }
}
```

### d5 — open计state；beside排除

人工审核：pending。

```json
{
  "example_id": "d5",
  "reference_status": "assistant_authored_candidate",
  "input": {
    "text": "An open door beside a chair."
  },
  "output": {
    "entities": [
      {
        "id": "e1",
        "name": "door",
        "mentions": [
          {
            "quote": "door",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e2",
        "name": "chair",
        "mentions": [
          {
            "quote": "chair",
            "occurrence": 0
          }
        ]
      }
    ],
    "attributes": [
      {
        "id": "a1",
        "entity_id": "e1",
        "slot": "state",
        "value": "open",
        "evidence": [
          {
            "quote": "open door",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "open",
            "occurrence": 0
          }
        ]
      }
    ],
    "excluded": [
      {
        "source": {
          "quote": "beside a chair",
          "occurrence": 0
        },
        "reason": "relation"
      }
    ]
  }
}
```

### d6 — wet计state；running不计state

人工审核：pending。

```json
{
  "example_id": "d6",
  "reference_status": "assistant_authored_candidate",
  "input": {
    "text": "A dog is running beside a wet bench."
  },
  "output": {
    "entities": [
      {
        "id": "e1",
        "name": "dog",
        "mentions": [
          {
            "quote": "dog",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e2",
        "name": "bench",
        "mentions": [
          {
            "quote": "bench",
            "occurrence": 0
          }
        ]
      }
    ],
    "attributes": [
      {
        "id": "a1",
        "entity_id": "e2",
        "slot": "state",
        "value": "wet",
        "evidence": [
          {
            "quote": "wet bench",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "wet",
            "occurrence": 0
          }
        ]
      }
    ],
    "excluded": [
      {
        "source": {
          "quote": "running",
          "occurrence": 0
        },
        "reason": "action"
      },
      {
        "source": {
          "quote": "beside a wet bench",
          "occurrence": 0
        },
        "reason": "relation"
      }
    ]
  }
}
```

### d7 — 数量、评价、动作排除；群体不虚构多个个体

人工审核：pending。

```json
{
  "example_id": "d7",
  "reference_status": "assistant_authored_candidate",
  "input": {
    "text": "Two dogs stand beside a beautiful car."
  },
  "output": {
    "entities": [
      {
        "id": "e1",
        "name": "dog",
        "mentions": [
          {
            "quote": "dogs",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e2",
        "name": "car",
        "mentions": [
          {
            "quote": "car",
            "occurrence": 0
          }
        ]
      }
    ],
    "attributes": [],
    "excluded": [
      {
        "source": {
          "quote": "Two",
          "occurrence": 0
        },
        "reason": "count"
      },
      {
        "source": {
          "quote": "stand",
          "occurrence": 0
        },
        "reason": "action"
      },
      {
        "source": {
          "quote": "beside a beautiful car",
          "occurrence": 0
        },
        "reason": "relation"
      },
      {
        "source": {
          "quote": "beautiful",
          "occurrence": 0
        },
        "reason": "subjective"
      }
    ]
  }
}
```

### d8 — 重复红色只计一次；推测和否定不当肯定颜色

人工审核：pending。

```json
{
  "example_id": "d8",
  "reference_status": "assistant_authored_candidate",
  "input": {
    "text": "A red car is parked. The car is red. It may be blue. It is not green."
  },
  "output": {
    "entities": [
      {
        "id": "e1",
        "name": "car",
        "mentions": [
          {
            "quote": "car",
            "occurrence": 0
          },
          {
            "quote": "car",
            "occurrence": 1
          }
        ]
      }
    ],
    "attributes": [
      {
        "id": "a1",
        "entity_id": "e1",
        "slot": "color",
        "value": "red",
        "evidence": [
          {
            "quote": "red car",
            "occurrence": 0
          },
          {
            "quote": "The car is red",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "red",
            "occurrence": 0
          },
          {
            "quote": "red",
            "occurrence": 1
          }
        ]
      }
    ],
    "excluded": [
      {
        "source": {
          "quote": "parked",
          "occurrence": 0
        },
        "reason": "action"
      },
      {
        "source": {
          "quote": "It may be blue",
          "occurrence": 0
        },
        "reason": "nonasserted"
      },
      {
        "source": {
          "quote": "It is not green",
          "occurrence": 0
        },
        "reason": "nonasserted"
      }
    ]
  }
}
```

## align：固定示例

### a1 — 完整等义材质保留

人工审核：pending。

```json
{
  "example_id": "a1",
  "reference_status": "assistant_candidate",
  "input": {
    "original": {
      "text": "A wooden table.",
      "entities": [
        {
          "id": "e1",
          "name": "table",
          "mentions": [
            {
              "quote": "table",
              "occurrence": 0,
              "start": 9,
              "end": 14
            }
          ]
        }
      ],
      "facts": [
        {
          "id": "entity_e1",
          "type": "entity",
          "entity_id": "e1",
          "slot": "existence",
          "value": "table",
          "source_spans": [
            {
              "quote": "table",
              "occurrence": 0,
              "start": 9,
              "end": 14
            }
          ],
          "value_spans": [
            {
              "quote": "table",
              "occurrence": 0,
              "start": 9,
              "end": 14
            }
          ]
        },
        {
          "id": "a1",
          "type": "attribute",
          "entity_id": "e1",
          "slot": "material",
          "value": "wood",
          "source_spans": [
            {
              "quote": "A wooden table.",
              "occurrence": 0,
              "start": 0,
              "end": 15
            }
          ],
          "value_spans": [
            {
              "quote": "wooden",
              "occurrence": 0,
              "start": 2,
              "end": 8
            }
          ]
        }
      ],
      "issues": []
    },
    "steer": {
      "text": "A table made of wood.",
      "entities": [
        {
          "id": "e1",
          "name": "table",
          "mentions": [
            {
              "quote": "table",
              "occurrence": 0,
              "start": 2,
              "end": 7
            }
          ]
        }
      ],
      "facts": [
        {
          "id": "entity_e1",
          "type": "entity",
          "entity_id": "e1",
          "slot": "existence",
          "value": "table",
          "source_spans": [
            {
              "quote": "table",
              "occurrence": 0,
              "start": 2,
              "end": 7
            }
          ],
          "value_spans": [
            {
              "quote": "table",
              "occurrence": 0,
              "start": 2,
              "end": 7
            }
          ]
        },
        {
          "id": "a1",
          "type": "attribute",
          "entity_id": "e1",
          "slot": "material",
          "value": "wood",
          "source_spans": [
            {
              "quote": "A table made of wood.",
              "occurrence": 0,
              "start": 0,
              "end": 21
            }
          ],
          "value_spans": [
            {
              "quote": "wood",
              "occurrence": 0,
              "start": 16,
              "end": 20
            }
          ]
        }
      ],
      "issues": []
    }
  },
  "output": {
    "entities": [
      {
        "original": [
          "e1"
        ],
        "steer": [
          "e1"
        ],
        "status": "matched",
        "reason": "same subject and slot"
      }
    ],
    "alignments": [
      {
        "original": [
          "entity_e1"
        ],
        "steer": [
          "entity_e1"
        ],
        "status": "retained",
        "reason": "same subject and slot"
      },
      {
        "original": [
          "a1"
        ],
        "steer": [
          "a1"
        ],
        "status": "retained",
        "reason": "same subject and slot"
      }
    ]
  }
}
```

### a2 — 属性缺失removed

人工审核：pending。

```json
{
  "example_id": "a2",
  "reference_status": "assistant_candidate",
  "input": {
    "original": {
      "text": "A red car.",
      "entities": [
        {
          "id": "e1",
          "name": "car",
          "mentions": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 6,
              "end": 9
            }
          ]
        }
      ],
      "facts": [
        {
          "id": "entity_e1",
          "type": "entity",
          "entity_id": "e1",
          "slot": "existence",
          "value": "car",
          "source_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 6,
              "end": 9
            }
          ],
          "value_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 6,
              "end": 9
            }
          ]
        },
        {
          "id": "a1",
          "type": "attribute",
          "entity_id": "e1",
          "slot": "color",
          "value": "red",
          "source_spans": [
            {
              "quote": "A red car.",
              "occurrence": 0,
              "start": 0,
              "end": 10
            }
          ],
          "value_spans": [
            {
              "quote": "red",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ]
        }
      ],
      "issues": []
    },
    "steer": {
      "text": "A car.",
      "entities": [
        {
          "id": "e1",
          "name": "car",
          "mentions": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ]
        }
      ],
      "facts": [
        {
          "id": "entity_e1",
          "type": "entity",
          "entity_id": "e1",
          "slot": "existence",
          "value": "car",
          "source_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ],
          "value_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ]
        }
      ],
      "issues": []
    }
  },
  "output": {
    "entities": [
      {
        "original": [
          "e1"
        ],
        "steer": [
          "e1"
        ],
        "status": "matched",
        "reason": "same subject and slot"
      }
    ],
    "alignments": [
      {
        "original": [
          "entity_e1"
        ],
        "steer": [
          "entity_e1"
        ],
        "status": "retained",
        "reason": "same subject and slot"
      },
      {
        "original": [
          "a1"
        ],
        "steer": [],
        "status": "removed",
        "reason": "same subject and slot"
      }
    ]
  }
}
```

### a3 — 属性新出现added

人工审核：pending。

```json
{
  "example_id": "a3",
  "reference_status": "assistant_candidate",
  "input": {
    "original": {
      "text": "A car.",
      "entities": [
        {
          "id": "e1",
          "name": "car",
          "mentions": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ]
        }
      ],
      "facts": [
        {
          "id": "entity_e1",
          "type": "entity",
          "entity_id": "e1",
          "slot": "existence",
          "value": "car",
          "source_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ],
          "value_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ]
        }
      ],
      "issues": []
    },
    "steer": {
      "text": "A red car.",
      "entities": [
        {
          "id": "e1",
          "name": "car",
          "mentions": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 6,
              "end": 9
            }
          ]
        }
      ],
      "facts": [
        {
          "id": "entity_e1",
          "type": "entity",
          "entity_id": "e1",
          "slot": "existence",
          "value": "car",
          "source_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 6,
              "end": 9
            }
          ],
          "value_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 6,
              "end": 9
            }
          ]
        },
        {
          "id": "a1",
          "type": "attribute",
          "entity_id": "e1",
          "slot": "color",
          "value": "red",
          "source_spans": [
            {
              "quote": "A red car.",
              "occurrence": 0,
              "start": 0,
              "end": 10
            }
          ],
          "value_spans": [
            {
              "quote": "red",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ]
        }
      ],
      "issues": []
    }
  },
  "output": {
    "entities": [
      {
        "original": [
          "e1"
        ],
        "steer": [
          "e1"
        ],
        "status": "matched",
        "reason": "same subject and slot"
      }
    ],
    "alignments": [
      {
        "original": [
          "entity_e1"
        ],
        "steer": [
          "entity_e1"
        ],
        "status": "retained",
        "reason": "same subject and slot"
      },
      {
        "original": [],
        "steer": [
          "a1"
        ],
        "status": "added",
        "reason": "same subject and slot"
      }
    ]
  }
}
```

### a4 — 同主体同槽变值modified

人工审核：pending。

```json
{
  "example_id": "a4",
  "reference_status": "assistant_candidate",
  "input": {
    "original": {
      "text": "A red car.",
      "entities": [
        {
          "id": "e1",
          "name": "car",
          "mentions": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 6,
              "end": 9
            }
          ]
        }
      ],
      "facts": [
        {
          "id": "entity_e1",
          "type": "entity",
          "entity_id": "e1",
          "slot": "existence",
          "value": "car",
          "source_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 6,
              "end": 9
            }
          ],
          "value_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 6,
              "end": 9
            }
          ]
        },
        {
          "id": "a1",
          "type": "attribute",
          "entity_id": "e1",
          "slot": "color",
          "value": "red",
          "source_spans": [
            {
              "quote": "A red car.",
              "occurrence": 0,
              "start": 0,
              "end": 10
            }
          ],
          "value_spans": [
            {
              "quote": "red",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ]
        }
      ],
      "issues": []
    },
    "steer": {
      "text": "A blue car.",
      "entities": [
        {
          "id": "e1",
          "name": "car",
          "mentions": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 7,
              "end": 10
            }
          ]
        }
      ],
      "facts": [
        {
          "id": "entity_e1",
          "type": "entity",
          "entity_id": "e1",
          "slot": "existence",
          "value": "car",
          "source_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 7,
              "end": 10
            }
          ],
          "value_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 7,
              "end": 10
            }
          ]
        },
        {
          "id": "a1",
          "type": "attribute",
          "entity_id": "e1",
          "slot": "color",
          "value": "blue",
          "source_spans": [
            {
              "quote": "A blue car.",
              "occurrence": 0,
              "start": 0,
              "end": 11
            }
          ],
          "value_spans": [
            {
              "quote": "blue",
              "occurrence": 0,
              "start": 2,
              "end": 6
            }
          ]
        }
      ],
      "issues": []
    }
  },
  "output": {
    "entities": [
      {
        "original": [
          "e1"
        ],
        "steer": [
          "e1"
        ],
        "status": "matched",
        "reason": "same subject and slot"
      }
    ],
    "alignments": [
      {
        "original": [
          "entity_e1"
        ],
        "steer": [
          "entity_e1"
        ],
        "status": "retained",
        "reason": "same subject and slot"
      },
      {
        "original": [
          "a1"
        ],
        "steer": [
          "a1"
        ],
        "status": "modified",
        "reason": "same subject and slot"
      }
    ]
  }
}
```

### a5 — 跨槽remove+add

人工审核：pending。

```json
{
  "example_id": "a5",
  "reference_status": "assistant_candidate",
  "input": {
    "original": {
      "text": "A wooden table.",
      "entities": [
        {
          "id": "e1",
          "name": "table",
          "mentions": [
            {
              "quote": "table",
              "occurrence": 0,
              "start": 9,
              "end": 14
            }
          ]
        }
      ],
      "facts": [
        {
          "id": "entity_e1",
          "type": "entity",
          "entity_id": "e1",
          "slot": "existence",
          "value": "table",
          "source_spans": [
            {
              "quote": "table",
              "occurrence": 0,
              "start": 9,
              "end": 14
            }
          ],
          "value_spans": [
            {
              "quote": "table",
              "occurrence": 0,
              "start": 9,
              "end": 14
            }
          ]
        },
        {
          "id": "a1",
          "type": "attribute",
          "entity_id": "e1",
          "slot": "material",
          "value": "wood",
          "source_spans": [
            {
              "quote": "A wooden table.",
              "occurrence": 0,
              "start": 0,
              "end": 15
            }
          ],
          "value_spans": [
            {
              "quote": "wooden",
              "occurrence": 0,
              "start": 2,
              "end": 8
            }
          ]
        }
      ],
      "issues": []
    },
    "steer": {
      "text": "A red table.",
      "entities": [
        {
          "id": "e1",
          "name": "table",
          "mentions": [
            {
              "quote": "table",
              "occurrence": 0,
              "start": 6,
              "end": 11
            }
          ]
        }
      ],
      "facts": [
        {
          "id": "entity_e1",
          "type": "entity",
          "entity_id": "e1",
          "slot": "existence",
          "value": "table",
          "source_spans": [
            {
              "quote": "table",
              "occurrence": 0,
              "start": 6,
              "end": 11
            }
          ],
          "value_spans": [
            {
              "quote": "table",
              "occurrence": 0,
              "start": 6,
              "end": 11
            }
          ]
        },
        {
          "id": "a1",
          "type": "attribute",
          "entity_id": "e1",
          "slot": "color",
          "value": "red",
          "source_spans": [
            {
              "quote": "A red table.",
              "occurrence": 0,
              "start": 0,
              "end": 12
            }
          ],
          "value_spans": [
            {
              "quote": "red",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ]
        }
      ],
      "issues": []
    }
  },
  "output": {
    "entities": [
      {
        "original": [
          "e1"
        ],
        "steer": [
          "e1"
        ],
        "status": "matched",
        "reason": "same subject and slot"
      }
    ],
    "alignments": [
      {
        "original": [
          "entity_e1"
        ],
        "steer": [
          "entity_e1"
        ],
        "status": "retained",
        "reason": "same subject and slot"
      },
      {
        "original": [
          "a1"
        ],
        "steer": [],
        "status": "removed",
        "reason": "same subject and slot"
      },
      {
        "original": [],
        "steer": [
          "a1"
        ],
        "status": "added",
        "reason": "same subject and slot"
      }
    ]
  }
}
```

### a6 — 主体退出与属性省略区分

人工审核：pending。

```json
{
  "example_id": "a6",
  "reference_status": "assistant_candidate",
  "input": {
    "original": {
      "text": "A car and a bench.",
      "entities": [
        {
          "id": "e1",
          "name": "car",
          "mentions": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ]
        },
        {
          "id": "e2",
          "name": "bench",
          "mentions": [
            {
              "quote": "bench",
              "occurrence": 0,
              "start": 12,
              "end": 17
            }
          ]
        }
      ],
      "facts": [
        {
          "id": "entity_e1",
          "type": "entity",
          "entity_id": "e1",
          "slot": "existence",
          "value": "car",
          "source_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ],
          "value_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ]
        },
        {
          "id": "entity_e2",
          "type": "entity",
          "entity_id": "e2",
          "slot": "existence",
          "value": "bench",
          "source_spans": [
            {
              "quote": "bench",
              "occurrence": 0,
              "start": 12,
              "end": 17
            }
          ],
          "value_spans": [
            {
              "quote": "bench",
              "occurrence": 0,
              "start": 12,
              "end": 17
            }
          ]
        }
      ],
      "issues": []
    },
    "steer": {
      "text": "A car.",
      "entities": [
        {
          "id": "e1",
          "name": "car",
          "mentions": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ]
        }
      ],
      "facts": [
        {
          "id": "entity_e1",
          "type": "entity",
          "entity_id": "e1",
          "slot": "existence",
          "value": "car",
          "source_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ],
          "value_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ]
        }
      ],
      "issues": []
    }
  },
  "output": {
    "entities": [
      {
        "original": [
          "e1"
        ],
        "steer": [
          "e1"
        ],
        "status": "matched",
        "reason": "same subject and slot"
      },
      {
        "original": [
          "e2"
        ],
        "steer": [],
        "status": "original_only",
        "reason": "same subject and slot"
      }
    ],
    "alignments": [
      {
        "original": [
          "entity_e1"
        ],
        "steer": [
          "entity_e1"
        ],
        "status": "retained",
        "reason": "same subject and slot"
      },
      {
        "original": [
          "entity_e2"
        ],
        "steer": [],
        "status": "removed",
        "reason": "same subject and slot"
      }
    ]
  }
}
```

### a7 — 身份不能确定时unresolved

人工审核：pending。

```json
{
  "example_id": "a7",
  "reference_status": "assistant_candidate",
  "input": {
    "original": {
      "text": "A person and another person.",
      "entities": [
        {
          "id": "e1",
          "name": "person",
          "mentions": [
            {
              "quote": "person",
              "occurrence": 0,
              "start": 2,
              "end": 8
            }
          ]
        },
        {
          "id": "e2",
          "name": "person",
          "mentions": [
            {
              "quote": "person",
              "occurrence": 1,
              "start": 21,
              "end": 27
            }
          ]
        }
      ],
      "facts": [
        {
          "id": "entity_e1",
          "type": "entity",
          "entity_id": "e1",
          "slot": "existence",
          "value": "person",
          "source_spans": [
            {
              "quote": "person",
              "occurrence": 0,
              "start": 2,
              "end": 8
            }
          ],
          "value_spans": [
            {
              "quote": "person",
              "occurrence": 0,
              "start": 2,
              "end": 8
            }
          ]
        },
        {
          "id": "entity_e2",
          "type": "entity",
          "entity_id": "e2",
          "slot": "existence",
          "value": "person",
          "source_spans": [
            {
              "quote": "person",
              "occurrence": 1,
              "start": 21,
              "end": 27
            }
          ],
          "value_spans": [
            {
              "quote": "person",
              "occurrence": 1,
              "start": 21,
              "end": 27
            }
          ]
        }
      ],
      "issues": []
    },
    "steer": {
      "text": "A person.",
      "entities": [
        {
          "id": "e1",
          "name": "person",
          "mentions": [
            {
              "quote": "person",
              "occurrence": 0,
              "start": 2,
              "end": 8
            }
          ]
        }
      ],
      "facts": [
        {
          "id": "entity_e1",
          "type": "entity",
          "entity_id": "e1",
          "slot": "existence",
          "value": "person",
          "source_spans": [
            {
              "quote": "person",
              "occurrence": 0,
              "start": 2,
              "end": 8
            }
          ],
          "value_spans": [
            {
              "quote": "person",
              "occurrence": 0,
              "start": 2,
              "end": 8
            }
          ]
        }
      ],
      "issues": []
    }
  },
  "output": {
    "entities": [
      {
        "original": [
          "e1",
          "e2"
        ],
        "steer": [
          "e1"
        ],
        "status": "unresolved",
        "reason": "identity_unclear"
      }
    ],
    "alignments": [
      {
        "original": [
          "entity_e1",
          "entity_e2"
        ],
        "steer": [
          "entity_e1"
        ],
        "status": "unresolved",
        "reason": "identity_unclear"
      }
    ]
  }
}
```

### a8 — 对侧原文已表达但输入事实缺失时extraction_gap

人工审核：pending。

```json
{
  "example_id": "a8",
  "reference_status": "assistant_candidate",
  "input": {
    "original": {
      "text": "A red car.",
      "entities": [
        {
          "id": "e1",
          "name": "car",
          "mentions": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 6,
              "end": 9
            }
          ]
        }
      ],
      "facts": [
        {
          "id": "entity_e1",
          "type": "entity",
          "entity_id": "e1",
          "slot": "existence",
          "value": "car",
          "source_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 6,
              "end": 9
            }
          ],
          "value_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 6,
              "end": 9
            }
          ]
        },
        {
          "id": "a1",
          "type": "attribute",
          "entity_id": "e1",
          "slot": "color",
          "value": "red",
          "source_spans": [
            {
              "quote": "A red car.",
              "occurrence": 0,
              "start": 0,
              "end": 10
            }
          ],
          "value_spans": [
            {
              "quote": "red",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ]
        }
      ],
      "issues": []
    },
    "steer": {
      "text": "A car is red.",
      "entities": [
        {
          "id": "e1",
          "name": "car",
          "mentions": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ]
        }
      ],
      "facts": [
        {
          "id": "entity_e1",
          "type": "entity",
          "entity_id": "e1",
          "slot": "existence",
          "value": "car",
          "source_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ],
          "value_spans": [
            {
              "quote": "car",
              "occurrence": 0,
              "start": 2,
              "end": 5
            }
          ]
        }
      ],
      "issues": []
    }
  },
  "output": {
    "entities": [
      {
        "original": [
          "e1"
        ],
        "steer": [
          "e1"
        ],
        "status": "matched",
        "reason": "same subject and slot"
      }
    ],
    "alignments": [
      {
        "original": [
          "entity_e1"
        ],
        "steer": [
          "entity_e1"
        ],
        "status": "retained",
        "reason": "same subject and slot"
      },
      {
        "original": [
          "a1"
        ],
        "steer": [],
        "status": "unresolved",
        "reason": "extraction_gap",
        "opposite_evidence": {
          "quote": "red",
          "occurrence": 0
        }
      }
    ]
  }
}
```

## verify：固定示例

### v1 — 实体supported

人工审核：pending。

![原图](./实验结果/exp_results/images/COCO_val2014_000000054627.jpg)

```json
{
  "example_id": "v1",
  "image_id": "54627",
  "semantic_type": "entity",
  "reference_status": "assistant_visual_candidate",
  "input": {
    "image_path": ".\\实验结果\\exp_results\\images\\COCO_val2014_000000054627.jpg",
    "image_sha256": "7c51d023d63c4ec851d413bcaf7218d5ef8c9e8567e0a599c36f5c4eae5fd984",
    "statement": "There is a horse in the image.",
    "entity_context": {}
  },
  "output": {
    "label": "supported",
    "reason": "Several horses are visible in the field."
  }
}
```

### v2 — 实体hallucinated

人工审核：pending。

![原图](./实验结果/exp_results/images/COCO_val2014_000000212603.jpg)

```json
{
  "example_id": "v2",
  "image_id": "212603",
  "semantic_type": "entity",
  "reference_status": "assistant_visual_candidate",
  "input": {
    "image_path": ".\\实验结果\\exp_results\\images\\COCO_val2014_000000212603.jpg",
    "image_sha256": "27c5145e371b05f1cfc13ff425d98d1fc4b98eb7538dd5ea10a97a800d9acd0a",
    "statement": "There is a dog in the image.",
    "entity_context": {}
  },
  "output": {
    "label": "hallucinated",
    "reason": "The visible animal is a cat, not a dog."
  }
}
```

### v3 — 实体uncertain

人工审核：pending。

![原图](./实验结果/exp_results/images/COCO_val2014_000000003501.jpg)

```json
{
  "example_id": "v3",
  "image_id": "3501",
  "semantic_type": "entity",
  "reference_status": "assistant_visual_candidate",
  "input": {
    "image_path": ".\\实验结果\\exp_results\\images\\COCO_val2014_000000003501.jpg",
    "image_sha256": "872beddd8e45dd2fbceb10ff6463a73b7be3c1b2dcefaa827386ffedd30eebdf",
    "statement": "There is a carrot in the stew.",
    "entity_context": {}
  },
  "output": {
    "label": "uncertain",
    "reason": "The small orange pieces cannot be confidently identified as carrot from this image."
  }
}
```

### v4 — 属性supported

人工审核：pending。

![原图](./实验结果/exp_results/images/COCO_val2014_000000008775.jpg)

```json
{
  "example_id": "v4",
  "image_id": "8775",
  "semantic_type": "attribute",
  "reference_status": "assistant_visual_candidate",
  "input": {
    "image_path": ".\\实验结果\\exp_results\\images\\COCO_val2014_000000008775.jpg",
    "image_sha256": "5f43ea915a5cb101f615d84a8201cccab1fdfe74234953548ee22092bda89426",
    "statement": "The pillow near the left side of the bed has blue fabric.",
    "entity_context": {}
  },
  "output": {
    "label": "supported",
    "reason": "Blue fabric is visible on the pillow."
  }
}
```

### v5 — 属性hallucinated

人工审核：pending。

![原图](./实验结果/exp_results/images/COCO_val2014_000000003501.jpg)

```json
{
  "example_id": "v5",
  "image_id": "3501",
  "semantic_type": "attribute",
  "reference_status": "assistant_visual_candidate",
  "input": {
    "image_path": ".\\实验结果\\exp_results\\images\\COCO_val2014_000000003501.jpg",
    "image_sha256": "872beddd8e45dd2fbceb10ff6463a73b7be3c1b2dcefaa827386ffedd30eebdf",
    "statement": "The bowl is black.",
    "entity_context": {}
  },
  "output": {
    "label": "hallucinated",
    "reason": "The bowl is light-colored, not black."
  }
}
```

### v6 — 属性uncertain

人工审核：pending。

![原图](./outputs/visual40_v1/images/275717.jpg)

```json
{
  "example_id": "v6",
  "image_id": "275717",
  "semantic_type": "attribute",
  "reference_status": "assistant_visual_candidate",
  "input": {
    "image_path": ".\\outputs\\visual40_v1\\images\\275717.jpg",
    "image_sha256": "1267d252d460bb36365428777c969d7a7c9f16b86f20d29ce8af7f8e58403453",
    "statement": "The tie has red fabric.",
    "entity_context": {}
  },
  "output": {
    "label": "uncertain",
    "reason": "This grayscale image does not establish the actual hue of the tie."
  }
}
```

## 固定测评候选参考

示例与下面测评输入分开。M3只称开发最小对照，不称改写族隔离的held-out测试。

### decompose_pilot / boundary_01

人工审核：pending。

```json
{
  "case_id": "boundary_01",
  "text": "A blue ceramic bowl is broken.",
  "reference": {
    "entities": [
      {
        "id": "e1",
        "name": "bowl",
        "mentions": [
          {
            "quote": "bowl",
            "occurrence": 0
          }
        ]
      }
    ],
    "attributes": [
      {
        "id": "a1",
        "entity_id": "e1",
        "slot": "color",
        "value": "blue",
        "evidence": [
          {
            "quote": "blue ceramic bowl",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "blue",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "a2",
        "entity_id": "e1",
        "slot": "material",
        "value": "ceramic",
        "evidence": [
          {
            "quote": "ceramic bowl",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "ceramic",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "a3",
        "entity_id": "e1",
        "slot": "state",
        "value": "broken",
        "evidence": [
          {
            "quote": "bowl is broken",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "broken",
            "occurrence": 0
          }
        ]
      }
    ],
    "excluded": []
  },
  "reference_status": "assistant_candidate",
  "split": "synthetic_boundary_development",
  "family": "not_generalization_evidence"
}
```

### decompose_pilot / boundary_02

人工审核：pending。

```json
{
  "case_id": "boundary_02",
  "text": "Three cats are sleeping near a square box.",
  "reference": {
    "entities": [
      {
        "id": "e1",
        "name": "cat",
        "mentions": [
          {
            "quote": "cats",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e2",
        "name": "box",
        "mentions": [
          {
            "quote": "box",
            "occurrence": 0
          }
        ]
      }
    ],
    "attributes": [
      {
        "id": "a1",
        "entity_id": "e2",
        "slot": "shape",
        "value": "square",
        "evidence": [
          {
            "quote": "square box",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "square",
            "occurrence": 0
          }
        ]
      }
    ],
    "excluded": [
      {
        "source": {
          "quote": "Three",
          "occurrence": 0
        },
        "reason": "count"
      },
      {
        "source": {
          "quote": "sleeping",
          "occurrence": 0
        },
        "reason": "action"
      },
      {
        "source": {
          "quote": "near a square box",
          "occurrence": 0
        },
        "reason": "relation"
      }
    ]
  },
  "reference_status": "assistant_candidate",
  "split": "synthetic_boundary_development",
  "family": "not_generalization_evidence"
}
```

### decompose_pilot / boundary_03

人工审核：pending。

```json
{
  "case_id": "boundary_03",
  "text": "The bag is not black. It might be green.",
  "reference": {
    "entities": [
      {
        "id": "e1",
        "name": "bag",
        "mentions": [
          {
            "quote": "bag",
            "occurrence": 0
          }
        ]
      }
    ],
    "attributes": [],
    "excluded": [
      {
        "source": {
          "quote": "The bag is not black",
          "occurrence": 0
        },
        "reason": "nonasserted"
      },
      {
        "source": {
          "quote": "It might be green",
          "occurrence": 0
        },
        "reason": "nonasserted"
      }
    ]
  },
  "reference_status": "assistant_candidate",
  "split": "synthetic_boundary_development",
  "family": "not_generalization_evidence"
}
```

### decompose_pilot / boundary_04

人工审核：pending。

```json
{
  "case_id": "boundary_04",
  "text": "An intact glass bottle is near a large basket.",
  "reference": {
    "entities": [
      {
        "id": "e1",
        "name": "bottle",
        "mentions": [
          {
            "quote": "bottle",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e2",
        "name": "basket",
        "mentions": [
          {
            "quote": "basket",
            "occurrence": 0
          }
        ]
      }
    ],
    "attributes": [
      {
        "id": "a1",
        "entity_id": "e1",
        "slot": "state",
        "value": "intact",
        "evidence": [
          {
            "quote": "intact glass bottle",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "intact",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "a2",
        "entity_id": "e1",
        "slot": "material",
        "value": "glass",
        "evidence": [
          {
            "quote": "glass bottle",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "glass",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "a3",
        "entity_id": "e2",
        "slot": "size",
        "value": "large",
        "evidence": [
          {
            "quote": "large basket",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "large",
            "occurrence": 0
          }
        ]
      }
    ],
    "excluded": [
      {
        "source": {
          "quote": "near a large basket",
          "occurrence": 0
        },
        "reason": "relation"
      }
    ]
  },
  "reference_status": "assistant_candidate",
  "split": "synthetic_boundary_development",
  "family": "not_generalization_evidence"
}
```

### decompose_pilot / 150639_steer

人工审核：pending。

```json
{
  "case_id": "150639_steer",
  "text": "The man is wearing glasses and talking on a red phone. He is in a car with other people around him.",
  "reference": {
    "entities": [
      {
        "id": "e1",
        "name": "man",
        "mentions": [
          {
            "quote": "man",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e2",
        "name": "glasses",
        "mentions": [
          {
            "quote": "glasses",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e3",
        "name": "phone",
        "mentions": [
          {
            "quote": "phone",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e4",
        "name": "car",
        "mentions": [
          {
            "quote": "car",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e5",
        "name": "people",
        "mentions": [
          {
            "quote": "people",
            "occurrence": 0
          }
        ]
      }
    ],
    "attributes": [
      {
        "id": "a1",
        "entity_id": "e3",
        "slot": "color",
        "value": "red",
        "evidence": [
          {
            "quote": "red phone",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "red",
            "occurrence": 0
          }
        ]
      }
    ],
    "excluded": []
  },
  "reference_status": "assistant_candidate",
  "split": "real_development",
  "family": "150639"
}
```

### decompose_pilot / 337055_steer

人工审核：pending。

```json
{
  "case_id": "337055_steer",
  "text": "A woman with tattoos and glasses is sitting on a suitcase.",
  "reference": {
    "entities": [
      {
        "id": "e1",
        "name": "woman",
        "mentions": [
          {
            "quote": "woman",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e2",
        "name": "tattoo",
        "mentions": [
          {
            "quote": "tattoos",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e3",
        "name": "glasses",
        "mentions": [
          {
            "quote": "glasses",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e4",
        "name": "suitcase",
        "mentions": [
          {
            "quote": "suitcase",
            "occurrence": 0
          }
        ]
      }
    ],
    "attributes": [],
    "excluded": []
  },
  "reference_status": "assistant_candidate",
  "split": "real_development",
  "family": "337055"
}
```

### decompose_pilot / 397351_steer

人工审核：pending。

```json
{
  "case_id": "397351_steer",
  "text": "The image depicts a man standing in front of a table full of vegetables, including carrots and radishes. He is wearing a green apron and appears to be selling these vegetables at a market.",
  "reference": {
    "entities": [
      {
        "id": "e1",
        "name": "man",
        "mentions": [
          {
            "quote": "man",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e2",
        "name": "table",
        "mentions": [
          {
            "quote": "table",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e3",
        "name": "vegetable",
        "mentions": [
          {
            "quote": "vegetables",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e4",
        "name": "carrot",
        "mentions": [
          {
            "quote": "carrots",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e5",
        "name": "radish",
        "mentions": [
          {
            "quote": "radishes",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e6",
        "name": "apron",
        "mentions": [
          {
            "quote": "apron",
            "occurrence": 0
          }
        ]
      }
    ],
    "attributes": [
      {
        "id": "a1",
        "entity_id": "e6",
        "slot": "color",
        "value": "green",
        "evidence": [
          {
            "quote": "green apron",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "green",
            "occurrence": 0
          }
        ]
      }
    ],
    "excluded": []
  },
  "reference_status": "assistant_candidate",
  "split": "real_development",
  "family": "397351"
}
```

### decompose_pilot / 360487_original

人工审核：pending。

```json
{
  "case_id": "360487_original",
  "text": "The image features a green glass vase filled with a bouquet of white flowers. The vase is placed on a wooden table, which serves as a beautiful backdrop for the arrangement. The flowers in the vase are arranged in a way that showcases their beauty, creating a visually appealing display. The combination of the green vase and the white flowers creates a harmonious and elegant atmosphere.",
  "reference": {
    "entities": [
      {
        "id": "e1",
        "name": "vase",
        "mentions": [
          {
            "quote": "vase",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e2",
        "name": "flower",
        "mentions": [
          {
            "quote": "flowers",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "e3",
        "name": "table",
        "mentions": [
          {
            "quote": "table",
            "occurrence": 0
          }
        ]
      }
    ],
    "attributes": [
      {
        "id": "a1",
        "entity_id": "e1",
        "slot": "color",
        "value": "green",
        "evidence": [
          {
            "quote": "green glass vase",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "green",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "a2",
        "entity_id": "e1",
        "slot": "material",
        "value": "glass",
        "evidence": [
          {
            "quote": "glass vase",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "glass",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "a3",
        "entity_id": "e2",
        "slot": "color",
        "value": "white",
        "evidence": [
          {
            "quote": "white flowers",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "white",
            "occurrence": 0
          }
        ]
      },
      {
        "id": "a4",
        "entity_id": "e3",
        "slot": "material",
        "value": "wood",
        "evidence": [
          {
            "quote": "wooden table",
            "occurrence": 0
          }
        ],
        "value_quotes": [
          {
            "quote": "wooden",
            "occurrence": 0
          }
        ]
      }
    ],
    "excluded": []
  },
  "reference_status": "assistant_candidate",
  "split": "real_development",
  "family": "360487"
}
```

### align_cases / align_01

人工审核：pending。

```json
{
  "case_id": "align_01",
  "original": {
    "caption_id": "caption",
    "text": "A green bottle.",
    "entities": [
      {
        "id": "e1",
        "name": "bottle",
        "mentions": [
          {
            "quote": "bottle",
            "occurrence": 0,
            "start": 8,
            "end": 14
          }
        ]
      }
    ],
    "facts": [
      {
        "id": "entity_e1",
        "type": "entity",
        "entity_id": "e1",
        "slot": "existence",
        "value": "bottle",
        "source_spans": [
          {
            "quote": "bottle",
            "occurrence": 0,
            "start": 8,
            "end": 14
          }
        ],
        "value_spans": [
          {
            "quote": "bottle",
            "occurrence": 0,
            "start": 8,
            "end": 14
          }
        ]
      },
      {
        "id": "a1",
        "type": "attribute",
        "entity_id": "e1",
        "slot": "color",
        "value": "green",
        "source_spans": [
          {
            "quote": "A green bottle.",
            "occurrence": 0,
            "start": 0,
            "end": 15
          }
        ],
        "value_spans": [
          {
            "quote": "green",
            "occurrence": 0,
            "start": 2,
            "end": 7
          }
        ]
      }
    ],
    "excluded": [],
    "issues": [],
    "status": "ready"
  },
  "steer": {
    "caption_id": "caption",
    "text": "A blue bottle.",
    "entities": [
      {
        "id": "e1",
        "name": "bottle",
        "mentions": [
          {
            "quote": "bottle",
            "occurrence": 0,
            "start": 7,
            "end": 13
          }
        ]
      }
    ],
    "facts": [
      {
        "id": "entity_e1",
        "type": "entity",
        "entity_id": "e1",
        "slot": "existence",
        "value": "bottle",
        "source_spans": [
          {
            "quote": "bottle",
            "occurrence": 0,
            "start": 7,
            "end": 13
          }
        ],
        "value_spans": [
          {
            "quote": "bottle",
            "occurrence": 0,
            "start": 7,
            "end": 13
          }
        ]
      },
      {
        "id": "a1",
        "type": "attribute",
        "entity_id": "e1",
        "slot": "color",
        "value": "blue",
        "source_spans": [
          {
            "quote": "A blue bottle.",
            "occurrence": 0,
            "start": 0,
            "end": 14
          }
        ],
        "value_spans": [
          {
            "quote": "blue",
            "occurrence": 0,
            "start": 2,
            "end": 6
          }
        ]
      }
    ],
    "excluded": [],
    "issues": [],
    "status": "ready"
  },
  "reference": {
    "entities": [
      {
        "original": [
          "e1"
        ],
        "steer": [
          "e1"
        ],
        "status": "matched",
        "reason": "same subject and slot"
      }
    ],
    "alignments": [
      {
        "original": [
          "entity_e1"
        ],
        "steer": [
          "entity_e1"
        ],
        "status": "retained",
        "reason": "same subject and slot"
      },
      {
        "original": [
          "a1"
        ],
        "steer": [
          "a1"
        ],
        "status": "modified",
        "reason": "same subject and slot"
      }
    ]
  },
  "split": "controlled_development",
  "reference_status": "assistant_candidate"
}
```

### align_cases / align_02

人工审核：pending。

```json
{
  "case_id": "align_02",
  "original": {
    "caption_id": "caption",
    "text": "A ceramic bowl.",
    "entities": [
      {
        "id": "e1",
        "name": "bowl",
        "mentions": [
          {
            "quote": "bowl",
            "occurrence": 0,
            "start": 10,
            "end": 14
          }
        ]
      }
    ],
    "facts": [
      {
        "id": "entity_e1",
        "type": "entity",
        "entity_id": "e1",
        "slot": "existence",
        "value": "bowl",
        "source_spans": [
          {
            "quote": "bowl",
            "occurrence": 0,
            "start": 10,
            "end": 14
          }
        ],
        "value_spans": [
          {
            "quote": "bowl",
            "occurrence": 0,
            "start": 10,
            "end": 14
          }
        ]
      },
      {
        "id": "a1",
        "type": "attribute",
        "entity_id": "e1",
        "slot": "material",
        "value": "ceramic",
        "source_spans": [
          {
            "quote": "A ceramic bowl.",
            "occurrence": 0,
            "start": 0,
            "end": 15
          }
        ],
        "value_spans": [
          {
            "quote": "ceramic",
            "occurrence": 0,
            "start": 2,
            "end": 9
          }
        ]
      }
    ],
    "excluded": [],
    "issues": [],
    "status": "ready"
  },
  "steer": {
    "caption_id": "caption",
    "text": "A small bowl.",
    "entities": [
      {
        "id": "e1",
        "name": "bowl",
        "mentions": [
          {
            "quote": "bowl",
            "occurrence": 0,
            "start": 8,
            "end": 12
          }
        ]
      }
    ],
    "facts": [
      {
        "id": "entity_e1",
        "type": "entity",
        "entity_id": "e1",
        "slot": "existence",
        "value": "bowl",
        "source_spans": [
          {
            "quote": "bowl",
            "occurrence": 0,
            "start": 8,
            "end": 12
          }
        ],
        "value_spans": [
          {
            "quote": "bowl",
            "occurrence": 0,
            "start": 8,
            "end": 12
          }
        ]
      },
      {
        "id": "a1",
        "type": "attribute",
        "entity_id": "e1",
        "slot": "size",
        "value": "small",
        "source_spans": [
          {
            "quote": "A small bowl.",
            "occurrence": 0,
            "start": 0,
            "end": 13
          }
        ],
        "value_spans": [
          {
            "quote": "small",
            "occurrence": 0,
            "start": 2,
            "end": 7
          }
        ]
      }
    ],
    "excluded": [],
    "issues": [],
    "status": "ready"
  },
  "reference": {
    "entities": [
      {
        "original": [
          "e1"
        ],
        "steer": [
          "e1"
        ],
        "status": "matched",
        "reason": "same subject and slot"
      }
    ],
    "alignments": [
      {
        "original": [
          "entity_e1"
        ],
        "steer": [
          "entity_e1"
        ],
        "status": "retained",
        "reason": "same subject and slot"
      },
      {
        "original": [
          "a1"
        ],
        "steer": [],
        "status": "removed",
        "reason": "same subject and slot"
      },
      {
        "original": [],
        "steer": [
          "a1"
        ],
        "status": "added",
        "reason": "same subject and slot"
      }
    ]
  },
  "split": "controlled_development",
  "reference_status": "assistant_candidate"
}
```

### align_cases / align_03

人工审核：pending。

```json
{
  "case_id": "align_03",
  "original": {
    "caption_id": "caption",
    "text": "A wet towel.",
    "entities": [
      {
        "id": "e1",
        "name": "towel",
        "mentions": [
          {
            "quote": "towel",
            "occurrence": 0,
            "start": 6,
            "end": 11
          }
        ]
      }
    ],
    "facts": [
      {
        "id": "entity_e1",
        "type": "entity",
        "entity_id": "e1",
        "slot": "existence",
        "value": "towel",
        "source_spans": [
          {
            "quote": "towel",
            "occurrence": 0,
            "start": 6,
            "end": 11
          }
        ],
        "value_spans": [
          {
            "quote": "towel",
            "occurrence": 0,
            "start": 6,
            "end": 11
          }
        ]
      },
      {
        "id": "a1",
        "type": "attribute",
        "entity_id": "e1",
        "slot": "state",
        "value": "wet",
        "source_spans": [
          {
            "quote": "A wet towel.",
            "occurrence": 0,
            "start": 0,
            "end": 12
          }
        ],
        "value_spans": [
          {
            "quote": "wet",
            "occurrence": 0,
            "start": 2,
            "end": 5
          }
        ]
      }
    ],
    "excluded": [],
    "issues": [],
    "status": "ready"
  },
  "steer": {
    "caption_id": "caption",
    "text": "A towel is wet.",
    "entities": [
      {
        "id": "e1",
        "name": "towel",
        "mentions": [
          {
            "quote": "towel",
            "occurrence": 0,
            "start": 2,
            "end": 7
          }
        ]
      }
    ],
    "facts": [
      {
        "id": "entity_e1",
        "type": "entity",
        "entity_id": "e1",
        "slot": "existence",
        "value": "towel",
        "source_spans": [
          {
            "quote": "towel",
            "occurrence": 0,
            "start": 2,
            "end": 7
          }
        ],
        "value_spans": [
          {
            "quote": "towel",
            "occurrence": 0,
            "start": 2,
            "end": 7
          }
        ]
      }
    ],
    "excluded": [],
    "issues": [],
    "status": "ready"
  },
  "reference": {
    "entities": [
      {
        "original": [
          "e1"
        ],
        "steer": [
          "e1"
        ],
        "status": "matched",
        "reason": "same subject and slot"
      }
    ],
    "alignments": [
      {
        "original": [
          "entity_e1"
        ],
        "steer": [
          "entity_e1"
        ],
        "status": "retained",
        "reason": "same subject and slot"
      },
      {
        "original": [
          "a1"
        ],
        "steer": [],
        "status": "unresolved",
        "reason": "extraction_gap",
        "opposite_evidence": {
          "quote": "wet",
          "occurrence": 0
        }
      }
    ]
  },
  "split": "controlled_development",
  "reference_status": "assistant_candidate"
}
```

### align_cases / align_04

人工审核：pending。

```json
{
  "case_id": "align_04",
  "original": {
    "caption_id": "caption",
    "text": "A mug made of glass.",
    "entities": [
      {
        "id": "e1",
        "name": "mug",
        "mentions": [
          {
            "quote": "mug",
            "occurrence": 0,
            "start": 2,
            "end": 5
          }
        ]
      }
    ],
    "facts": [
      {
        "id": "entity_e1",
        "type": "entity",
        "entity_id": "e1",
        "slot": "existence",
        "value": "mug",
        "source_spans": [
          {
            "quote": "mug",
            "occurrence": 0,
            "start": 2,
            "end": 5
          }
        ],
        "value_spans": [
          {
            "quote": "mug",
            "occurrence": 0,
            "start": 2,
            "end": 5
          }
        ]
      },
      {
        "id": "a1",
        "type": "attribute",
        "entity_id": "e1",
        "slot": "material",
        "value": "glass",
        "source_spans": [
          {
            "quote": "A mug made of glass.",
            "occurrence": 0,
            "start": 0,
            "end": 20
          }
        ],
        "value_spans": [
          {
            "quote": "glass",
            "occurrence": 0,
            "start": 14,
            "end": 19
          }
        ]
      }
    ],
    "excluded": [],
    "issues": [],
    "status": "ready"
  },
  "steer": {
    "caption_id": "caption",
    "text": "A glass mug.",
    "entities": [
      {
        "id": "e1",
        "name": "mug",
        "mentions": [
          {
            "quote": "mug",
            "occurrence": 0,
            "start": 8,
            "end": 11
          }
        ]
      }
    ],
    "facts": [
      {
        "id": "entity_e1",
        "type": "entity",
        "entity_id": "e1",
        "slot": "existence",
        "value": "mug",
        "source_spans": [
          {
            "quote": "mug",
            "occurrence": 0,
            "start": 8,
            "end": 11
          }
        ],
        "value_spans": [
          {
            "quote": "mug",
            "occurrence": 0,
            "start": 8,
            "end": 11
          }
        ]
      },
      {
        "id": "a1",
        "type": "attribute",
        "entity_id": "e1",
        "slot": "material",
        "value": "glass",
        "source_spans": [
          {
            "quote": "A glass mug.",
            "occurrence": 0,
            "start": 0,
            "end": 12
          }
        ],
        "value_spans": [
          {
            "quote": "glass",
            "occurrence": 0,
            "start": 2,
            "end": 7
          }
        ]
      }
    ],
    "excluded": [],
    "issues": [],
    "status": "ready"
  },
  "reference": {
    "entities": [
      {
        "original": [
          "e1"
        ],
        "steer": [
          "e1"
        ],
        "status": "matched",
        "reason": "same subject and slot"
      }
    ],
    "alignments": [
      {
        "original": [
          "entity_e1"
        ],
        "steer": [
          "entity_e1"
        ],
        "status": "retained",
        "reason": "same subject and slot"
      },
      {
        "original": [
          "a1"
        ],
        "steer": [
          "a1"
        ],
        "status": "retained",
        "reason": "same subject and slot"
      }
    ]
  },
  "split": "controlled_development",
  "reference_status": "assistant_candidate"
}
```

### verify_cases / visual_1

人工审核：pending。

![原图](./outputs/visual40_v1/images/337055.jpg)

```json
{
  "case_id": "visual_1",
  "image_id": "337055",
  "semantic_type": "entity",
  "input": {
    "image_path": ".\\outputs\\visual40_v1\\images\\337055.jpg",
    "image_sha256": "a6182f269c232a632a3ddba5ac6e0f730bd4f61c8ab31fc236b988c422768237",
    "statement": "There is a suitcase in the image.",
    "entity_context": {}
  },
  "reference_label": "supported",
  "reference_status": "assistant_visual_candidate",
  "split": "visual_development"
}
```

### verify_cases / visual_2

人工审核：pending。

![原图](./outputs/visual40_v1/images/337055.jpg)

```json
{
  "case_id": "visual_2",
  "image_id": "337055",
  "semantic_type": "entity",
  "input": {
    "image_path": ".\\outputs\\visual40_v1\\images\\337055.jpg",
    "image_sha256": "a6182f269c232a632a3ddba5ac6e0f730bd4f61c8ab31fc236b988c422768237",
    "statement": "There is a dog in the image.",
    "entity_context": {}
  },
  "reference_label": "hallucinated",
  "reference_status": "assistant_visual_candidate",
  "split": "visual_development"
}
```

### verify_cases / visual_3

人工审核：pending。

![原图](./实验结果/exp_results/caption_review_20/images/COCO_val2014_000000150639.jpg)

```json
{
  "case_id": "visual_3",
  "image_id": "150639",
  "semantic_type": "entity",
  "input": {
    "image_path": ".\\实验结果\\exp_results\\caption_review_20\\images\\COCO_val2014_000000150639.jpg",
    "image_sha256": "790cf7dac4ffb0299a6f9da799bf00122cbfa4d094ab3cba19b490573c8889e2",
    "statement": "There is a passenger inside the car visible through the rear window.",
    "entity_context": {}
  },
  "reference_label": "uncertain",
  "reference_status": "assistant_visual_candidate",
  "split": "visual_development"
}
```

### verify_cases / visual_4

人工审核：pending。

![原图](./实验结果/exp_results/caption_review_20/images/COCO_val2014_000000360487.jpg)

```json
{
  "case_id": "visual_4",
  "image_id": "360487",
  "semantic_type": "attribute",
  "input": {
    "image_path": ".\\实验结果\\exp_results\\caption_review_20\\images\\COCO_val2014_000000360487.jpg",
    "image_sha256": "9065d717d952ab1636dfe12ded99d40a37c559742ee6bf3b76c7d8e32ee891ba",
    "statement": "The vase is green.",
    "entity_context": {}
  },
  "reference_label": "supported",
  "reference_status": "assistant_visual_candidate",
  "split": "visual_development"
}
```

### verify_cases / visual_5

人工审核：pending。

![原图](./实验结果/exp_results/caption_review_20/images/COCO_val2014_000000360487.jpg)

```json
{
  "case_id": "visual_5",
  "image_id": "360487",
  "semantic_type": "attribute",
  "input": {
    "image_path": ".\\实验结果\\exp_results\\caption_review_20\\images\\COCO_val2014_000000360487.jpg",
    "image_sha256": "9065d717d952ab1636dfe12ded99d40a37c559742ee6bf3b76c7d8e32ee891ba",
    "statement": "The flowers are blue.",
    "entity_context": {}
  },
  "reference_label": "hallucinated",
  "reference_status": "assistant_visual_candidate",
  "split": "visual_development"
}
```

### verify_cases / visual_6

人工审核：pending。

![原图](./实验结果/exp_results/caption_review_20/images/COCO_val2014_000000150639.jpg)

```json
{
  "case_id": "visual_6",
  "image_id": "150639",
  "semantic_type": "attribute",
  "input": {
    "image_path": ".\\实验结果\\exp_results\\caption_review_20\\images\\COCO_val2014_000000150639.jpg",
    "image_sha256": "790cf7dac4ffb0299a6f9da799bf00122cbfa4d094ab3cba19b490573c8889e2",
    "statement": "The eyeglass frame is made of titanium.",
    "entity_context": {}
  },
  "reference_label": "uncertain",
  "reference_status": "assistant_visual_candidate",
  "split": "visual_development"
}
```
