# 数据模块

- `celeba.py`：读取 `identity_CelebA.txt`，按最少图片数筛选身份。
- `splits.py`：划分清单。公开池/用户池、train/gallery/test 角色、上传账户（本人与虚拟其他上传者）、互不重叠的遗忘组；可保存、加载与哈希。
- `deletion.py`：账户删除与人物删除、追踪遗漏（嵌套抽样）、两阶段训练集合。
- `canary.py`：Athena 式暗号（每个遗忘组一个图案与目标身份，左右对称，翻转不变）。
- `datasets.py`：PyTorch 数据集与变换；暗号在空间变换之后、归一化之前加上。
- `lfw.py`：LFW pairs 读取与排除名单。
- `synthetic.py`：合成“人脸”，仅用于测试与冒烟运行。
