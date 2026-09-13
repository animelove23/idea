# framework_v2：首轮工程与测评改进

本版本完成改进计划E0/E1，并准备第5节的候选参考审核材料。原repair_v1、原提示、8/8/6-shot和原参考均保留。默认视觉窗口及retained共享行为未改变；新增逐侧定位审计不进入视觉query。

已验证结果：[首轮报告](../../outputs/framework_v2_stage1_release/RESULTS.md)。84项离线测试通过；原20图259个保存响应重放后，264条事实、199个视觉命题及M6统计完全一致。再次恢复没有重发完成请求。新增API调用为0。

## 运行入口

从项目根目录执行。新runner可接收任意符合M0格式的明确pairs清单，支持真实M2分解，不再依赖旧bundles。

```powershell
# 重放本轮已保存的响应，严格禁止cache miss后访问网络；输出须使用新目录
.venv\Scripts\python.exe -m analysis_skeleton.framework_v2.pipeline --pairs analysis_skeleton/fixtures/expansion20/pairs.jsonl --output outputs/framework_v2_my_replay --cache outputs/framework_v2_stage1_release/response_cache.jsonl --cache-mode replay

# 恢复上面的同一配置、同一输入、同一代码运行
.venv\Scripts\python.exe -m analysis_skeleton.framework_v2.pipeline --pairs analysis_skeleton/fixtures/expansion20/pairs.jsonl --output outputs/framework_v2_my_replay --cache outputs/framework_v2_stage1_release/response_cache.jsonl --cache-mode replay --resume

# 离线测试：网络访问由测试runner阻止，结果写到指定目录
.venv\Scripts\python.exe -m tests.run_framework_v2_checks --output outputs/framework_v2_local_checks
```

需要实际模型推断时使用同一pipeline入口的--cache-mode fresh，并指定--condition-id和--replicate-id；该模式调用已有官方DeepSeek配置。--pair-id可重复传入。fresh忽略旧响应缓存；reuse只在精确匹配时复用，未命中则请求；replay只读选择好的响应，未命中记技术失败。线上新数据与调用范围遵循用户既有授权及实验范围，本首轮没有执行在线模式。

## 数据与异常处理

- contracts.py：非字符串ID、status、reason等坏结构局部隔离；坏行涉及的冲突ID不能因此被另一个合法行抢占。仍执行原语义合同，未确定主体不会被强行匹配。
- runtime.py：输入构造、图像读取、传输、解析和校验分别留痕；unexpected_failure保留异常类型与栈位置，不记录响应头、异常正文或密钥。checkpoint有身份和checksum。
- pipeline.py：每claim和pair保留状态；缺图不删除文本事实。已经完成的请求恢复时不重发。只有started没有响应的记录标outcome_unknown，不自动重发；服务端是否已执行/计费不可由此确定。
- queue.py：保留实际query，增加每个ref的原文定位窗口、共享来源和文本语境是否完全相同。文本语境相同不证明视觉上是同一主体。
- ledger.py：生产有效事实、隔离项和参考全集分开记录。未匹配参考保留extraction_missing，预测额外项另列，不能把漏抽当removed。
- scoring.py：固定repair_v1词形规则，只暴露对应关系用于账本，不增加临时同义词。参考仍是助手候选。
- stability.py：定义三对重复的平均不一致率、任一次变化比例、S↔H翻转及完整覆盖；拒绝缓存冒充重复、重复response_id、不同输入或模型混为同一repeat。计算可决错误率时，参考U被判S/H也计错误确定判断。

后续repeat记录需含case_id、image_id、condition_id、replicate_id、query_hash、status、规范化signature、audit.identity、audit.response_id。每个condition独立评价；同图重复不当新增独立图片。尚未生成三次fresh重复，因此此版本不宣称跨模型调用稳定。

## 阶段状态

E0/E1已完成。24组边界候选仅经过结构和证据区间校验；它们不是新模型测试通过率。人工审核、D1/T1新图参考、fresh重复与X2/X3/X4/X5单变量干预均未执行，状态见[任务状态](../../outputs/framework_v2_stage1_release/TASK_STATUS.md)。
