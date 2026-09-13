# 串联入口本地检查

命令：`.venv\Scripts\python.exe -m unittest tests.test_skeleton_pipeline -v`

2026-09-12 实际执行4项，4项通过，耗时5.942秒。

| 测试 | 检查的行为 |
|---|---|
| real_m0_schema_and_shared_visual_backfill | 使用真实M0字段格式，2次分解＋1次对齐＋2次视觉模拟调用；共享实体回填两侧，3条事实只请求2个claim |
| missing_image_keeps_facts_and_makes_no_visual_calls | 缺图时保留3条事实并标pending，视觉调用0次 |
| failed_decompose_blocks_normal_alignment | 分解失败时对齐调用0次；剩余事实保持unresolved，完整pair名册记录失败 |
| missing_caption_preserved_in_roster_without_calls | 缺侧caption时三个模型均0次调用，pair_status保留异常 |

这是程序集成检查。使用明确的离线模拟响应，图片只在本地读取与校验；不产生真实模型准确率或真假现象结论。
