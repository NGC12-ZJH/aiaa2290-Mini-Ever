# 配置

| 文件 | 用途 |
| --- | --- |
| `base.json` | 正式实验模板。`null` 与空列表表示运行前必须确定的研究决定 |
| `smoke.json` | 合成数据冒烟配置，参数已全部填写，可直接运行 |

```bash
python -m mini_ever check-config --config configs/base.json   # 列出仍未确定的字段
```

字段含义见 `src/mini_ever/config.py` 中的数据类。未知字段会报错，避免拼写错误被静默忽略。模型初始化只允许 `imagenet_pretrained` 或 `random`，禁止人脸预训练权重（实验 0）。

正式运行时复制 `base.json` 另存，填写后不再修改；配置哈希会写入每条结果记录和模型缓存键。建议：遗忘组 3–5 组，训练总计 30–40 epoch，影子模型 16–32 个（U-LiRA 每类至少 3 个），均需先用首轮计时校准预算。
