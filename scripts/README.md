# 辅助脚本

| 脚本 | 用途 |
| --- | --- |
| `make_synthetic_data.py` | 生成 CelebA 目录结构的合成数据（不含真人照片），配合 `configs/smoke.json` 跑通全流程 |

训练、划分与实验统一通过命令行运行，见根目录 README「开始使用」：

```bash
python -m mini_ever check-config --config <配置>
python -m mini_ever make-split   --config <配置>
python -m mini_ever train main   --config <配置>
python -m mini_ever run exp01    --config <配置> [--groups 0 1] [--seeds 1 2]
```

删除实验只在划分清单定义的训练集合上操作，从不修改源数据文件。
