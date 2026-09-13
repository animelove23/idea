# 示例覆盖与边界材料

当前运行仍为原8/8/6-shot，未替换任何例子。对应表为shot_coverage_matrix.csv，完整候选输入/输出为boundary_cases.jsonl。

24组候选包括：20组M2正反对照（六种合法state、三种shape、material/color/size、存在推测、否定、局部属性推测、重复提及、两件衬衫的颜色绑定）；4组M3固定事实控制（retained、modified、removed、extraction_gap）。每组保留完整候选输出和规则说明。

所有候选输出均经过相同JSON/引文/类型校验，未调用LLM测试。它们是作者构造的边界材料，不是自然样本，更不是人工gold。M3复杂身份歧义及视觉真实困难例仍需独立补充，不能把这24组叫全类别验收。

已知原示例缺口：M2的state主要示范open/wet，其余四个state缺少示例；M5三个属性例全是color，缺size/material/shape/state边界，且entity_context全为空。不得同时补定位字段和替换例子内容后宣称某一因素有效。

下一步先审核材料及对应相邻反例，再用fresh重复基线决定一个干预；人工标签、模型、提示词、示例数量/顺序和query窗口不能同时改变。
