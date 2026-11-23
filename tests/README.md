# 测试

```bash
python -m pytest
```

全部测试使用合成数据与 CPU，约半分钟。覆盖：

| 文件 | 检查内容 |
| --- | --- |
| `test_config.py` | 未定参数检出、未知键拒绝、禁止人脸预训练权重 |
| `test_data.py` | 身份池与角色不重叠、账户比例、账户删除 ⊂ 人物删除、遗漏集合嵌套、暗号只在遗忘训练照片上且翻转不变 |
| `test_stats_and_mia.py` | AUC、区分优势、四状态判定、按身份 bootstrap、最弱节点聚合、U-LiRA |
| `test_models.py` | ArcFace 边际、输出过滤、gallery 删除、量化网格与副本隔离、产物血缘、分片均衡 |
| `test_pipeline.py` | 模型缓存与标签空间对齐、六种遗忘方法、exp00/01/03/04 端到端，结果文件不含身份编号 |

仓库中不放置真人图片或权重。
