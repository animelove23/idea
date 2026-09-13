# M1 粗粒度记录：真实数据完整性

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "captions": 1000,
  "tokens": 72655,
  "source_slice_correct": 72655,
  "source_slice_accuracy": 1.0,
  "repeat_captions": 20,
  "repeat_identical": 20,
  "empty": 1,
  "repetition": 0,
  "pos_human_accuracy": null,
  "lemma_human_accuracy": null
}
```

- 复用既有SpacyParser模型加载和重复退化检测，未增加LLM。
- 逐词偏移/统计通过不证明POS正确；尚无独立人工词性/lemma金标，准确率明确N/A。
- 词数排除标点，不能与历史len(words)未经重算直接比较；模型token长度未知。
