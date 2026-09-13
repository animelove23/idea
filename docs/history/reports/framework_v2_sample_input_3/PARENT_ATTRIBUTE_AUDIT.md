# 旧样本复用与主体—属性一致性核查

本次为本地核查，新增API调用0。

## 复用范围

- 上次fresh样本测试使用原expansion20的3张图和6条caption；模型重新推断36次，没有回放旧答案。
- M2沿用旧分解候选参考，按固定口径计算F1。
- M5由本次M2/M3生成27个命题；未整套重跑原60条固定视觉标记样本。25个新命题与历史请求身份及输入完全一致，用于标签变化诊断，不是准确率参考。
- 原标记文件仍声明为助手候选参考，未经独立人工裁决。317188旧视觉参考仅覆盖glasses、pink sweater、purple cell phone，不包括beach或sand，无法用这三条标签判定本次主体—属性组合谁错。

## 频率

| 范围 | 属性事实行 | 去重属性命题 | 主体U且属性S | 属性S命题中的占比 |
|---|---:|---:|---:|---:|
| 此前repair_v1的20图全链结果 | 39 | 32 | 0/32 | 0/23 |
| 本轮fresh 3图 | 6 | 5 | 1/5 | 1/5 |

两组图片重叠，不合并为独立样本估计总体发生率。重复回填的属性事实不是新的视觉判断。

## 具体案例317188

- 实体命题：An entity or group described as "beach" is present in the image.
- 实体U理由：The background shows sand, but no water or shoreline is visible to confirm a beach.
- 属性命题：The referenced beach is made of sand.
- 属性S理由：The ground beneath the woman is visibly sandy.

查看原图可见沙地，画面没有明确水面或海岸线。因此本例不能仅凭主体U认定实体分错。模型把主体命题解释成地貌类别确认，把属性命题解释成可见沙质判断。若属性S代表完整命题成立，则其中beach的存在及指代也应有支持，目前两个独立调用没有保证这一点。实体请求复用original语境，属性请求来自steer语境，也不是完全相同的定位条件。

新账本已记录binding_unconfirmed=True和strict_parent_supported_eligible=False；原始视觉标签保留，不应强行把实体升为S来消除表面不一致。后续可在保持模型/示例不变时，单独检验统一主体定位与属性完整命题判断。

## 实体与属性谁更容易

旧60条固定视觉样本，在repair_v1 context条件下，实体与候选参考一致33/41（80.5%），属性14/19（73.7%）。此结果支持该批实体总体更准，但类别构成和难度不同，不是严格的难度对照，亦非人工准确率。具体对象类别如woman、glasses，与场景类别beach、群体/个体及微小物体不宜混为一类讨论。

数据见parent_attribute_audit.json；本轮原始命题、理由和定位语境见fresh/verification_queue.jsonl与fresh/verification.jsonl。
