# 固定局部视图实验模块

这是M5的独立实验适配器；主框架默认视觉输入未改变。

`views.py`将原图解码为RGB，按固定2×2网格取四个宽高各为原图60%的重叠区域，保存为无损PNG。所有局部像素须与解码后的原图对应区域完全一致。没有生成图像、超分辨率、插值、按答案挑框或增加定位LLM。

`MultiViewStage`保留原system prompt、6组图文示例、原query文本和完整原图，只在query后附加四个局部视图及原图坐标。上下文来自原文本，标签不进入请求。一次命题仍只调用一次模型；图像输入量增加，需要同时报告token与延迟。

运行示例（输出目录必须新建，线上调用遵循原数据授权）：

```powershell
.venv\Scripts\python.exe -m unittest tests.test_visual_localization_v1 -v
.venv\Scripts\python.exe -m analysis_skeleton.visual_localization_v1.experiment prepare --output outputs/visual_localization_v1
.venv\Scripts\python.exe -m analysis_skeleton.visual_localization_v1.experiment run --output outputs/visual_localization_v1
.venv\Scripts\python.exe -m analysis_skeleton.visual_localization_v1.experiment report --output outputs/visual_localization_v1
```

`--resume`用于run恢复，身份及文件哈希需与首次一致。冻结检查点保留每次响应，已完成请求不重复发送。首次输入实验固定41实体，原图和局部视图条件交错，各41次，无缓存。

通过线：候选至少37/41正确，优于当轮原图control，错误确定判断不增加，工程检查全部通过；参考仍为旧助手候选。即使开发集过线，也需重复、属性回归及新图确认，不能直接宣称研究准确率达标。

这一步测的是固定多视图，不是已经解决了主体实例定位；目标可能横跨区域或本来就无足够像素，且多张局部图也可能使模型把局部细节误当独立对象。
