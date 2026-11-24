# 辅助脚本

| 脚本 | 用途 |
| --- | --- |
| `make_synthetic_data.py` | 生成 CelebA 目录结构的合成数据（不含真人照片），配合 `configs/smoke.json` 跑通全流程 |
| `download_celeba_mirror.sh` | 从 hf-mirror 的 `flwrlabs/celeba` 并行下载 25 个 parquet 分片，并按 LFS 哈希校验 |
| `convert_celeba_parquet.py` | 把 parquet 分片转成 `data/celeba/img_align_celeba/` 与 `identity_CelebA.txt`（需另装 pyarrow） |
| `make_calib_configs.py` | 由 `configs/calib.json` 生成阶段 1 校准用的学习率与 ArcFace 参数变体 |
| `exp03_diagnostics.py` | 实验 3 只读诊断：删除前主模型对各遗忘组的识别率、L4 重新学习曲线（原权重对参照），见 docs/exp03_analysis.md |
| `check_stage1_convergence.py` | 报告公开基础模型在公开池训练照片上的准确率，用于检查收敛；不看 exp00 阳性对照 |

CelebA 准备与校准的完整过程见 [docs/exp00_analysis.md](../docs/exp00_analysis.md)。

训练、划分与实验统一通过命令行运行，见根目录 README「开始使用」：

```bash
python -m mini_ever check-config --config <配置>
python -m mini_ever make-split   --config <配置>
python -m mini_ever train main   --config <配置>
python -m mini_ever run exp01    --config <配置> [--groups 0 1] [--seeds 1 2]
```

删除实验只在划分清单定义的训练集合上操作，从不修改源数据文件。
