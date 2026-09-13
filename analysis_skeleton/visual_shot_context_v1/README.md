# X5a：视觉few-shot输入字段一致性

保持现有6个示例的图片、命题、答案、顺序、类型与数量不变，仅为它们原本为空的`entity_context`补齐与query一致的字段：name、source_mentions、source_window、target_mention、context_role。

source_window使用示例原命题，不新增原caption或图像定位框。这个实验只检验格式一致性，不声称提供了新的视觉定位证据。原模型、system prompt与query原图完全保留，不叠加局部视图实验。

```powershell
.venv\Scripts\python.exe -m unittest tests.test_visual_shot_context_v1 -v
.venv\Scripts\python.exe -m analysis_skeleton.visual_shot_context_v1.experiment prepare --output outputs/visual_shot_context_v1
.venv\Scripts\python.exe -m analysis_skeleton.visual_shot_context_v1.experiment run --output outputs/visual_shot_context_v1
.venv\Scripts\python.exe -m analysis_skeleton.visual_shot_context_v1.experiment report --output outputs/visual_shot_context_v1
```

输出目录需全新；`run --resume`恢复同一冻结条件，不能更改输入或代码。一次固定60条旧开发命题，两条件交错各60次；41实体为主要指标，19属性为回归检查。参考单独保存且不进入请求。

预设通过条件：实体至少37/41、优于当轮control，错误确定判断不增加，属性正确数量不下降，工程检查通过。旧候选参考得分仍不等于人工准确率；通过也需新图确认。主框架默认示例未修改。
