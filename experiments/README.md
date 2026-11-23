# 实验入口

实验代码在 `src/mini_ever/experiments/`，统一通过 `python -m mini_ever run <key> --config <配置>` 运行。每个模块开头的说明列出比较对象与参照。

| key | 模块 | 实验 | 主要产物 |
| --- | --- | --- | --- |
| exp00 | `exp00_prior_familiarity` | 起点模型是否事先认识遗忘组；含阳性对照 | 每个起点模型的组间差值与判定 |
| exp01 | `exp01_traceability` | 只删照片后的逐节点残留；1b 账户删除 vs 人物删除；受影响产物清单 | 节点泄露、端到端泄露、账户缺口与噪声底 |
| exp02 | `exp02_deletability` | 单体与 SISA 的顺序删除成本 | 逐请求局部与全链路耗时、前后效用 |
| exp03 | `exp03_measurable_forgetting` | 六种方法 × L1–L5 | 各级判定、更新耗时、效用 |
| exp04 | `exp04_weakest_link` | A/B/C/D 配置；4b 追踪遗漏率扫描 | 节点泄露、端到端（最大值）与平均值对照 |

结果写入 `results/<实验名>/<时间戳>.json`，包含 commit、配置哈希、划分哈希等运行记录，不包含身份编号。
