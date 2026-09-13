# v6 测试参考（调用前冻结；助手编写，未经用户审核）

主线 entity/relation/attribute，other 单独计；逐条语义匹配不按措辞完全相同计。

## a0

> A girl wearing a green wool coat is standing beside a bicycle.

| id | type | 参考语义 |
| --- | --- | --- |
| g1 | entity | A girl exists. |
| g2 | entity | A coat exists. |
| g3 | entity | A bicycle exists. |
| g4 | attribute | The coat is green. |
| g5 | attribute | The coat is wool. |
| g6 | relation | The girl wears the coat. |
| g7 | relation | The girl is standing. |
| g8 | relation | The girl is beside the bicycle. |

## a1

> A girl wearing a wool coat is standing beside a bicycle.

| id | type | 参考语义 |
| --- | --- | --- |
| g1 | entity | A girl exists. |
| g2 | entity | A coat exists. |
| g3 | entity | A bicycle exists. |
| g4 | attribute | The coat is wool. |
| g5 | relation | The girl wears the coat. |
| g6 | relation | The girl is standing. |
| g7 | relation | The girl is beside the bicycle. |

## b0

> Four ceramic plates are on the right side of a counter.

| id | type | 参考语义 |
| --- | --- | --- |
| g1 | entity | Plates exist. |
| g2 | entity | A counter exists. |
| g3 | attribute | There are four plates in the described set. |
| g4 | attribute | The plates are ceramic. |
| g5 | relation | The plates are on the right side of the counter. |

## b1

> Two ceramic plates are on the left side of a counter.

| id | type | 参考语义 |
| --- | --- | --- |
| g1 | entity | Plates exist. |
| g2 | entity | A counter exists. |
| g3 | attribute | There are two plates in the described set. |
| g4 | attribute | The plates are ceramic. |
| g5 | relation | The plates are on the left side of the counter. |

## c0

> A dog may be sleeping under a round table.

| id | type | 参考语义 |
| --- | --- | --- |
| g1 | entity | A dog exists. |
| g2 | entity | A table exists. |
| g3 | attribute | The table is round. |
| g4 | relation | The dog may be sleeping. |
| g5 | relation | The dog may be under the table. |

## c1

> A dog is sleeping under a round table.

| id | type | 参考语义 |
| --- | --- | --- |
| g1 | entity | A dog exists. |
| g2 | entity | A table exists. |
| g3 | attribute | The table is round. |
| g4 | relation | The dog is sleeping. |
| g5 | relation | The dog is under the table. |

## d0

> A nurse carries a small metal box. The scene feels peaceful.

| id | type | 参考语义 |
| --- | --- | --- |
| g1 | entity | A nurse exists. |
| g2 | entity | A box exists. |
| g3 | attribute | The box is small. |
| g4 | attribute | The box is metal. |
| g5 | relation | The nurse carries the box. |
| g6 | other | The scene feels peaceful. |

## d1

> A nurse carries a small metal box, which is not red. The scene feels peaceful.

| id | type | 参考语义 |
| --- | --- | --- |
| g1 | entity | A nurse exists. |
| g2 | entity | A box exists. |
| g3 | attribute | The box is small. |
| g4 | attribute | The box is metal. |
| g5 | relation | The nurse carries the box. |
| g6 | attribute | The box is not red. |
| g7 | other | The scene feels peaceful. |
