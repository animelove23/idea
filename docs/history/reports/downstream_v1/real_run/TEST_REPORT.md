# 首轮请求格式失败记录（没有语义模型结果）

12 次流水线请求全部 HTTPError；一次原请求复现确认为 HTTP 400：JSON 模式要求提示包含 JSON 字样。另一次合成连通性诊断成功。合计 14 次请求。下列 ambiguous/stage_failed 均为失败回退，不是模型判断。原始失败结果未覆盖。

# Coverage / Alignment 首轮测试

Decomposer、v6 few-shot 和既有事实均未修改；使用先前独立拆分的真实 caption。所有视觉验证保持 pending。

## 状态计数

```json
{
  "pairs_planned": 4,
  "pairs_completed": 4,
  "coverage_captions": 8,
  "coverage_added": 0,
  "coverage_status": {
    "failed": 8
  },
  "entity_status": {
    "failed": 4
  },
  "alignment_status": {
    "failed": 4
  },
  "alignment_rows_all": {
    "added": 0,
    "ambiguous": 86,
    "modified": 0,
    "removed": 0,
    "retained": 0
  },
  "alignment_rows_main": {
    "added": 0,
    "ambiguous": 78,
    "modified": 0,
    "removed": 0,
    "retained": 0
  },
  "main_fact_status_counts": {
    "original": {
      "added": 0,
      "ambiguous": 47,
      "modified": 0,
      "removed": 0,
      "retained": 0
    },
    "steer": {
      "added": 0,
      "ambiguous": 31,
      "modified": 0,
      "removed": 0,
      "retained": 0
    }
  },
  "extraction_gap_rows": 0,
  "api_calls": 12,
  "pending_claims": 86,
  "note": "Alignment outputs are not human gold; ambiguous/extraction_gap are never counted as removed/added. All verifier labels pending."
}
```

注意：alignment 行数与事实数不同，ambiguous 可以多对多；主线不统计 other。未完成/失败另列，不用它们制造信息删除。

## Coverage 追加事实

### 581451_vanilla — failed

无已接收新增事实。
失败：HTTPError

### 299573_vista — failed

无已接收新增事实。
失败：HTTPError

### 417586_vanilla — failed

无已接收新增事实。
失败：HTTPError

### 581451_vista — failed

无已接收新增事实。
失败：HTTPError

### 417586_vista — failed

无已接收新增事实。
失败：HTTPError

### 299573_vanilla — failed

无已接收新增事实。
失败：HTTPError

### 415015_vanilla — failed

无已接收新增事实。
失败：HTTPError

### 415015_vista — failed

无已接收新增事实。
失败：HTTPError

## Entity Alignment

### 417586

```json
{
  "pair_id": "417586",
  "status": "failed",
  "error": "HTTPError"
}
```

### 299573

```json
{
  "pair_id": "299573",
  "status": "failed",
  "error": "HTTPError"
}
```

### 415015

```json
{
  "pair_id": "415015",
  "status": "failed",
  "error": "HTTPError"
}
```

### 581451

```json
{
  "pair_id": "581451",
  "status": "failed",
  "error": "HTTPError"
}
```

## Fact Alignment（完整状态；非人工准确率）

### 415015 — failed

| status / reason | Vanilla | Steer |
| --- | --- | --- |
| ambiguous / stage_failed | f1: There is a vase. |  |
| ambiguous / stage_failed | f2: There are dried flowers. |  |
| ambiguous / stage_failed | f3: There are daisies. |  |
| ambiguous / stage_failed | f4: There are sunflowers. |  |
| ambiguous / stage_failed | f5: There is a table. |  |
| ambiguous / stage_failed | f6: There is a window. |  |
| ambiguous / stage_failed | f7: The vase is filled with dried flowers. |  |
| ambiguous / stage_failed | f8: The dried flowers include daisies and sunflowers. |  |
| ambiguous / stage_failed | f9: The vase is placed on the table. |  |
| ambiguous / stage_failed | f10: The vase is positioned near the window. |  |
| ambiguous / stage_failed | f11: The flowers are arranged in a visually appealing manner. |  |
| ambiguous / stage_failed | f12: The combination of the vase, flowers, and the window creates a pleasant and inviting atmosphere. |  |
| ambiguous / stage_failed |  | f1: There is a glass vase. |
| ambiguous / stage_failed |  | f2: There are flowers. |
| ambiguous / stage_failed |  | f3: There are grasses. |
| ambiguous / stage_failed |  | f4: There is a table. |
| ambiguous / stage_failed |  | f5: There is a window. |
| ambiguous / stage_failed |  | f6: The vase is made of glass. |
| ambiguous / stage_failed |  | f7: The vase is filled with flowers and grasses. |
| ambiguous / stage_failed |  | f8: The vase is placed on the table. |
| ambiguous / stage_failed |  | f9: The table is next to the window. |
| ambiguous / stage_failed |  | f10: The flowers and grasses are arranged in such a way that they create a visually appealing bouquet. |
失败：entity alignment failed

### 299573 — failed

| status / reason | Vanilla | Steer |
| --- | --- | --- |
| ambiguous / stage_failed | f1: There are two giraffes. |  |
| ambiguous / stage_failed | f2: There is a grassy field. |  |
| ambiguous / stage_failed | f3: There are two giraffes. |  |
| ambiguous / stage_failed | f4: The field is grassy. |  |
| ambiguous / stage_failed | f5: The giraffes are standing. |  |
| ambiguous / stage_failed | f6: The giraffes are in the grassy field. |  |
| ambiguous / stage_failed | f7: One giraffe is positioned slightly behind the other. |  |
| ambiguous / stage_failed | f8: Both giraffes are facing the same direction. |  |
| ambiguous / stage_failed | f9: The giraffes are possibly looking at something in the distance. |  |
| ambiguous / stage_failed | f10: The giraffes are standing close to each other. |  |
| ambiguous / stage_failed | f11: The giraffes create a sense of companionship. |  |
| ambiguous / stage_failed | f12: The field is filled with tall grass. |  |
| ambiguous / stage_failed | f13: The field provides a natural habitat for the giraffes. |  |
| ambiguous / stage_failed |  | f1: There are giraffes. |
| ambiguous / stage_failed |  | f2: There are two giraffes. |
| ambiguous / stage_failed |  | f3: There is a grassy field. |
| ambiguous / stage_failed |  | f4: The field is grassy. |
| ambiguous / stage_failed |  | f5: The giraffes are standing. |
| ambiguous / stage_failed |  | f6: The giraffes are side by side. |
| ambiguous / stage_failed |  | f7: The giraffes are in the grassy field. |
失败：entity alignment failed

### 581451 — failed

| status / reason | Vanilla | Steer |
| --- | --- | --- |
| ambiguous / stage_failed | f1: There is a hot dog. |  |
| ambiguous / stage_failed | f2: There is a bun. |  |
| ambiguous / stage_failed | f3: There is ketchup. |  |
| ambiguous / stage_failed | f4: There are green peppers. |  |
| ambiguous / stage_failed | f5: There is a piece of paper. |  |
| ambiguous / stage_failed | f6: There is a napkin. |  |
| ambiguous / stage_failed | f7: The hot dog has a bun. |  |
| ambiguous / stage_failed | f8: The hot dog is topped with ketchup. |  |
| ambiguous / stage_failed | f9: The hot dog is topped with green peppers. |  |
| ambiguous / stage_failed | f10: The peppers are green. |  |
| ambiguous / stage_failed | f11: The hot dog is placed on the piece of paper. |  |
| ambiguous / stage_failed | f12: The piece of paper is likely a napkin. |  |
| ambiguous / stage_failed | f13: The hot dog is positioned in the center of the image. |  |
| ambiguous / stage_failed | f14: The peppers are scattered around the hot dog. |  |
| ambiguous / stage_failed | f15: The peppers add a colorful and appetizing touch to the dish. |  |
| ambiguous / stage_failed |  | f1: There is a person. |
| ambiguous / stage_failed |  | f2: There is a hot dog. |
| ambiguous / stage_failed |  | f3: There is ketchup. |
| ambiguous / stage_failed |  | f4: There are peppers. |
| ambiguous / stage_failed |  | f5: The person is holding the hot dog. |
| ambiguous / stage_failed |  | f6: The hot dog has ketchup on it. |
| ambiguous / stage_failed |  | f7: The hot dog has peppers on it. |
失败：entity alignment failed

### 417586 — failed

| status / reason | Vanilla | Steer |
| --- | --- | --- |
| ambiguous / stage_failed | f1: There is a bench. |  |
| ambiguous / stage_failed | f2: There are shoes. |  |
| ambiguous / stage_failed | f3: The bench is wooden. |  |
| ambiguous / stage_failed | f4: There are two pairs of the described shoes. |  |
| ambiguous / stage_failed | f5: The shoes are on the bench. |  |
| ambiguous / stage_failed | f6: The shoes are positioned close to each other. |  |
| ambiguous / stage_failed | f7: One pair of shoes is located towards the left side of the bench. |  |
| ambiguous / stage_failed | f8: The other pair of shoes is on the right side of the bench. |  |
| ambiguous / stage_failed | f9: The bench appears to be made of wood. |  |
| ambiguous / stage_failed | f10: The bench is situated in a grassy area. |  |
| ambiguous / stage_failed | f11: The grassy area is possibly a park or a garden. |  |
| ambiguous / stage_failed | f12: The shoes seem to be old. |  |
| ambiguous / stage_failed | f13: The shoes seem to be worn. |  |
| ambiguous / stage_failed | f14: The shoes suggest that they have been used for a long time. |  |
| ambiguous / stage_failed |  | f1: There are shoes. |
| ambiguous / stage_failed |  | f2: There is a bench. |
| ambiguous / stage_failed |  | f3: There are two pairs of the described shoes. |
| ambiguous / stage_failed |  | f4: The bench is wooden. |
| ambiguous / stage_failed |  | f5: The shoes are on the bench. |
| ambiguous / stage_failed |  | f6: One pair of shoes is on the left side of the bench. |
| ambiguous / stage_failed |  | f7: The other pair of shoes is on the right side of the bench. |
| ambiguous / stage_failed |  | f8: Both pairs of shoes are black. |
失败：entity alignment failed

本轮真实 pair 未观察到 added；不编造实际例子，见本地 contract tests 中的受控案例。
本轮真实 pair 未观察到 modified；不编造实际例子，见本地 contract tests 中的受控案例。
本轮真实 pair 未观察到 removed；不编造实际例子，见本地 contract tests 中的受控案例。
本轮真实 pair 未观察到 retained；不编造实际例子，见本地 contract tests 中的受控案例。
