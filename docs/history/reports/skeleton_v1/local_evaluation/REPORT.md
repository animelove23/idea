# 逐模块本地测评总览

本报告区分工程完整性、候选参考符合度和真实语义准确率。

```json
{
  "modules": [
    {
      "module": "M0",
      "tests": 2,
      "failures": 0,
      "errors": 0,
      "passed": true,
      "semantic_model_accuracy": null
    },
    {
      "module": "M1",
      "tests": 3,
      "failures": 0,
      "errors": 0,
      "passed": true,
      "semantic_model_accuracy": null
    },
    {
      "module": "M2",
      "tests": 6,
      "failures": 0,
      "errors": 0,
      "passed": true,
      "semantic_model_accuracy": null
    },
    {
      "module": "M3",
      "tests": 6,
      "failures": 0,
      "errors": 0,
      "passed": true,
      "semantic_model_accuracy": null
    },
    {
      "module": "M4",
      "tests": 4,
      "failures": 0,
      "errors": 0,
      "passed": true,
      "semantic_model_accuracy": null
    },
    {
      "module": "M5",
      "tests": 3,
      "failures": 0,
      "errors": 0,
      "passed": true,
      "semantic_model_accuracy": null
    },
    {
      "module": "M6",
      "tests": 6,
      "failures": 0,
      "errors": 0,
      "passed": true,
      "semantic_model_accuracy": null
    }
  ],
  "tests": 30,
  "external_calls": 0
}
```

- M4/M6控制用例导出齐备；视觉标签是明示的合成输入，不是DeepSeek图像判定。
- 真实在线模型结果分别见同级m2_online、m3_online、m5_online。
