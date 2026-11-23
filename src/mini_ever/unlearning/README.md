# 遗忘方法

统一签名：`method(ctx, model, removed, identities, seed) -> UnlearningOutput`，注册在 `METHODS` 中。

| 名称 | 文件 | 类型 |
| --- | --- | --- |
| `output_filter` | `approximate.py` | 只屏蔽输出，参数不变 |
| `finetune` | `approximate.py` | 在保留集上继续训练 |
| `neggrad_plus` | `approximate.py` | 保留集下降 + 遗忘集上升 |
| `scrub` | `approximate.py` | 教师–学生 max/min 交替（Kurmanji et al., 2023） |
| `full_retrain` | `exact.py` | 从公开基础模型重训第二阶段（精确） |
| `sisa` | `sisa.py` | 只重训受影响分片（精确）；独立训练设计，不从单体权重转换 |

所有方法返回更新耗时；精确方法标记 `exact=True`。
