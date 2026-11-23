# 评估模块

- `scores.py`：逐人分数（原型相似度、gallery 分数、检索 top-1、分类准确率、暗号触发率、TAR@FAR、逐样本分数）。
- `stats.py`：AUC、区分优势、按身份 bootstrap、四状态判定（通过/失败/不确定/不适用）。
- `leakage.py`：节点泄露与端到端最大值聚合（附平均值对照）。
- `mia.py`：U-LiRA（留一影子模型，每类至少 3 个）。
- `relearn.py`：少样本重新学习曲线（L4）。
- `levels.py`：L1–L5 判定。
- `utility.py`：闭集检索与 LFW 10 折验证。

统计协议见 `docs/protocol.md`。
