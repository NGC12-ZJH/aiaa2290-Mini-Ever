# mini_ever 包

| 模块 | 职责 |
| --- | --- |
| `config.py` | 类型化 JSON 配置与一致性检查 |
| `context.py` | 实验上下文：划分清单、数据集、模型磁盘缓存、产物清单、结果写入 |
| `data/` | CelebA 读取、划分清单、删除请求、暗号、数据集、LFW、合成数据 |
| `models/` | 嵌入网络、ArcFace、gallery、权重量化、产物版本清单 |
| `training/` | 训练循环、特征提取、蒸馏 |
| `unlearning/` | 六种遗忘方法（统一签名） |
| `evaluation/` | 逐人分数、统计、泄露聚合、U-LiRA、重新学习、L1–L5、效用 |
| `experiments/` | exp00–exp04 运行器 |
| `cli.py` | 命令行入口 |

依赖方向：`data`/`models`/`training` → `context` → `unlearning`/`evaluation` → `experiments` → `cli`。
