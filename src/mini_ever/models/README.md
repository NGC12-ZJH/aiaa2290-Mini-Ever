# 模型与产物

- `backbones.py`：ResNet-18/50（ImageNet 或随机初始化）+ 线性颈部，输出人脸 embedding；`tiny_cnn` 仅用于测试。没有加载人脸预训练权重的代码路径。
- `arcface.py`：ArcFace 头。
- `face_model.py`：嵌入网络 + 头 + 标签空间；`block()` 实现输出过滤。
- `gallery.py`：注册 embedding 库，可按身份删除、1:N 检索。
- `quantize.py`：逐通道对称权重量化（INT8/INT4）。
- `artifacts.py`：产物版本清单，记录每个产物包含的身份与账户并继承父产物血缘；`affected_by()` 列出删除请求涉及的所有版本。

权重、特征及逐人信息只保存在本地 `runs/`。
