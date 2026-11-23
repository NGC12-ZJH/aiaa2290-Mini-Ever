# 交接文档（HANDOFF）

> 写给没有任何上文的新会话。写于 2026-11-23，2026-11-24 补充了 GPU 环境与 GPU 冒烟结果；对应 commit `904f629`（`main`，已推送到 GitHub）。
> 先读本文，再按需读文中链接的文档。所有人称统一用 they/them。

---

## 1. 我们在做什么

**课程**：AIAA 2290（EPS in AI · AI Ethics, Security & Privacy）期末 presentation，两人组：

- Jinghan ZHAO：讲稿中的 B，负责第 4–7 页（三环模型与 T/D/M）；
- Qingyang LI：讲稿中的 A，负责第 1–3 页和第 8–11 页。

**Pre 主题**：*Forgettability* —— 公司什么时候才能诚实地说“已删除”？

- **案例**：Ever 相册 App（Everalbum / Paravision）。2021 年 FTC 不仅要求删除照片，还要求删除用照片训练出来的人脸模型。
- **概念框架**：可信删除 = `min(T, D, M)`
  - T：Traceability，知道数据去了哪里；
  - D：Deletability，能把影响拿出来；
  - M：Measurable forgetting，能证明影响已经消失。
- **评分**：10 分钟演讲，不许看稿，之后有 Q&A。共 12 项、每项 7 分制，见 [docs/presentation_rubric.md](docs/presentation_rubric.md)。
- **pre 日期**：**未知**。去问用户，倒排日程时要用到。

**Mini-Ever**（本仓库）：用一个缩小版 Ever 的人脸识别实验，给 pre 的 T/D/M 各页提供**自己的实测数字**，替换目前引用的文献证据（Carlini、Harry Potter 13%→89% 等）。
- 数据：CelebA 名人照片。
- 模型：ResNet-50 + ArcFace。
- 实验：exp00 起点检查、exp01 T、exp02 D、exp03 M、exp04 最弱一环。

---

## 2. 已经完成了什么

### Pre 材料（都在仓库里）

| 文件 | 内容 |
|---|---|
| [report/Forgettability_EPS_Presentation.pptx](report/Forgettability_EPS_Presentation.pptx) | 当前 PPT，12 页（含 References） |
| [docs/script_v1.md](docs/script_v1.md) | 逐字讲稿 v1，从 Windows 上的 docx 转换而来 |
| [docs/presentation_rubric.md](docs/presentation_rubric.md) | 课程评分标准 |
| [docs/everalbum_paravision.md](docs/everalbum_paravision.md) | Ever 案例事实，**已逐段核对 FTC 起诉书原文**，附来源链接 |

原始文件在 Windows 桌面：`/mnt/c/Users/30528/Desktop/EPS in AI/`（讲稿 docx、PPT、rubric PDF 等）。

### 实验设计文档

| 文件 | 内容 |
|---|---|
| [README.md](README.md) | 完整方案：设计依据、实验 0–4、仓库结构、使用方法、实现约定 |
| [docs/overview.md](docs/overview.md) | 通俗版说明，含**预期结果**（是假设，不是数据） |
| [docs/code_walkthrough.md](docs/code_walkthrough.md) | 代码结构讲解与冒烟测试结果 |
| [docs/protocol.md](docs/protocol.md) | 统计与对照规范（四状态判定、按身份 bootstrap 等） |
| [docs/roadmap.md](docs/roadmap.md) | 5 天排期、最小可行版、pre 页面映射 |

### 代码（`src/mini_ever/`，已合并到 `main`）

- 实现了全部 5 个实验和 6 种遗忘方法：输出过滤、FT、NegGrad+、SCRUB、全量重训、SISA。
- 有命令行入口 `python -m mini_ever ...`。
- 47 个测试全部通过（CPU，约 30 秒）。
- 用合成数据（`configs/smoke.json`）把 exp00–exp04 从头到尾跑通了，结论见 code_walkthrough 第三节。

### GPU 机器（点动 ddycloud，环境已装好）

- **平台与规格**：点动云实例 `12C32G4090`（区域“港科大”，按需计费 **1.0 点豆/小时**），镜像 `ubuntu-2204-nv570-cu124`。2026-11-23 23:27 创建。创建前账户余额 84 点豆。
- **连接**：`ssh ddy-4090`。IP 和端口只记在本机 `~/.ssh/config` 的 `ddy-4090` 条目里（仓库是公开的，不写进文档）；用户 `user`，密钥 `~/.ssh/id_ed25519_diandong`（公钥已由用户装到服务器）。
  - 控制台“访问 IP”里另有两个业务端口，分别映射服务器内部的 10000 和 10001 端口，可用于 TensorBoard 或 Jupyter。外部端口号在控制台查看。
  - **实例重建后 IP、端口和主机指纹都可能变**：先在控制台“访问 IP → 查看”核对，再更新 ssh config 并重新装公钥。
- **硬件**：RTX 4090 24 GB，驱动 570.211.01（最高支持 CUDA 12.8），12 核，31 GB 内存，系统盘 194 GB（已用约 13 GB）。有 git、tmux、免密 sudo。
- **2026-11-23 已装好的环境**：
  - 代码在 `~/aiaa2290-Mini-Ever`，commit `904f629`，用 HTTPS 克隆（服务器能直连 GitHub 和 download.pytorch.org）。
  - 镜像缺 `python3.10-venv` 和 pip，已用 `sudo apt-get install python3.10-venv python3-pip` 补上。
  - 虚拟环境在 `~/aiaa2290-Mini-Ever/.venv`：torch `2.11.0+cu128`，torchvision `0.26.0+cu128`，`torch.cuda.is_available()` 为 True；项目用 `pip install -e ".[dev]"` 安装。PyTorch 与 CUDA 库下载约 4 GB，用时 10 分钟以上。
  - **`data/` 下还没有 CelebA 或 LFW**，只有冒烟用的 `data/synthetic/`。
- **计费**：实例开着就按小时扣点豆，空闲时到控制台“停止计费”。**释放实例前**，先把 `results/`、`runs/`、`logs/` 下载回本地。关机后是否还收磁盘费没有核实过，用之前先查平台的计费说明。

### GPU 上的冒烟测试结果（2026-11-23，合成数据）

在 4090 上用 `configs/smoke.json` 跑了一遍，**只证明代码在 GPU 上链路通，不是研究结果**（见第 5 节第 15 条）。

- `pytest`：47 个测试全部通过，用时 46 秒。
- 五个实验在 tmux 里依次运行，全部正常退出（exit 0），日志里没有 warning 或 traceback：

| 实验 | GPU 用时 | CPU 用时（code_walkthrough） |
|---|---|---|
| exp00 起点检查 | 6 秒 | 3 秒 |
| exp01 T | 24 秒 | 15 秒 |
| exp02 D | 21 秒 | 14 秒 |
| exp03 M | 201 秒 | 约 2 分钟 |
| exp04 最弱一环 | 32 秒 | 23 秒 |

  GPU 反而更慢是正常的：冒烟用的是两层小 CNN、32×32 输入，主要耗时在 CUDA 初始化和数据搬运上。**不能用这些耗时估算正式实验的 GPU 预算**，正式预算要用 ResNet-50 实测 1 个 epoch 来定。
- 结果文件的 `meta` 记录了 `device: cuda`、`torch 2.11.0+cu128`、git commit `904f629`、配置哈希 `3baf1dd8…`、划分哈希 `ab41797f…`。
- 结论与 CPU 冒烟一致：
  - exp00 公开基础模型：遗忘组 vs 其他用户为“通过”。
  - exp00 **阳性对照（公开池 vs 用户池）仍是“测不出差异”**：验证 TAR 差 0.004（90% 区间 −0.009 至 0.021），检索 top-1 差 0。这再次说明合成数据没有记忆信号；正式实验必须先看到 CelebA 上的阳性对照为 detected。
  - exp01 第 0 组：照片库 61 张删到 0 张；gallery 节点泄露为 1.0（失败，符合预期：注册特征没删），主模型 0.0（通过），学生模型 0.25（失败）。人数只有 4，属于噪声级别。
- 文件位置（只在服务器上，不提交）：`results/smoke/<实验名>/<时间戳>.json`，日志在 `logs/smoke_exp0*.log`，汇总在 `logs/smoke_summary.txt`，模型缓存在 `runs/smoke/`。

### 其他算力选项（备用）

- **学校 HPC（Model Develop，网页门户）**：教学账号额度 RMB 50。2026-11-23 晚查看时，**整卡（A800 1/2/4/8 卡、A40 1/2/4/8 卡）可分配节点全部为 0**，只有 A800 的 MIG 切片（10G、20G、40G，均为 4 核）可选。没有 A30。MIG 按申请的显存计费；20G 切片的算力只有整卡的 1/7 或 2/7（要用 `nvidia-smi -L` 确认是 1g 还是 2g），比 4090 慢很多，所以只适合作备用。
  - 价格（低优先级，元/卡/小时）：A800 1.60，A30/A40/Ascend 0.50。VSCode 开发环境一律按低优先级价格计费。
  - 指南原件：`/mnt/c/Users/30528/Desktop/Intro 2 Data Mining/Project/Rubric and Instrution/API_and_HPC_User_Guide.pdf`。
  - 本机 `~/.ssh/config` 里的 `hpc2`、`hpc3`、`hpc4` 用的是**另一门课的账号**，不是这次的教学账号。
- **点动的其他规格**：A6000 48 GB 单卡 1.8 点豆/小时（2/4/8 卡依次翻倍）；4090 的 2/4/8 卡分别为 2、4、8 点豆/小时。代码是单卡训练，不需要多卡。
- **正式实验统一在 4090 单卡上跑**：实验 2 要比较 GPU 耗时，所以所有计时必须来自同一种硬件。

---

## 3. 当前卡在哪里

**没有被技术问题卡住，只是正式实验还没开始。** 正式实验需要依次做完这几件事：

1. **GPU 环境**：已完成（2026-11-23）。torch 已装好，测试和冒烟实验都在 4090 上跑通了。
2. **数据**：CelebA 还没下载到 GPU 机器上。下载前需要确认授权条款，仅限非商业研究。
3. **研究参数**：`configs/base.json` 里还有 24 个 `null` 字段没填，包括种子、训练轮数、学习率、batch size、等效界值、置信水平、影子模型数量等。没填完时，`run` 和 `train` 会拒绝启动；可以用 `python -m mini_ever check-config --config ...` 列出还缺哪些。部分数值（轮数、影子模型数）要先实测耗时才能定。
4. **pre 日期未知**，无法倒排日程。按经验，GPU 至少需要 pre 前 10 天开始用。

**目前没有任何真实实验数字。PPT 和讲稿都还没有更新。**

---

## 4. 下一步计划

### A. GPU 上的环境与校准（第 1 天）

环境已经装好，也验证过了（见第 2 节）。每次登录后先激活虚拟环境：

```bash
ssh ddy-4090
```
```bash
cd ~/aiaa2290-Mini-Ever && git pull && source .venv/bin/activate
```

长任务放在 tmux 里跑，避免 SSH 断开后任务中断，例如：

```bash
tmux new -s run
```

接下来：
1. 把 CelebA 放到 `data/celeba/`（`img_align_celeba/` 和 `identity_CelebA.txt`），LFW 可选放到 `data/lfw/`。
2. 复制 `configs/base.json` 为 `configs/my_run.json`（名字自定）。先填一个临时配置，实测 ResNet-50 跑 1 个 epoch 的耗时和显存，再填完所有 `null` 字段。**填完就不要再改**：配置哈希会进入缓存键和结果记录。
3. 依次运行：

```bash
python3 -m mini_ever make-split --config configs/my_run.json
```
```bash
python3 -m mini_ever run exp00 --config configs/my_run.json
```

**实验 0 的阳性对照必须先显示“detected”**（能区分公开池和用户池），否则先改进测量方法，再继续后面的实验。

### B. 正式实验（按 [roadmap](docs/roadmap.md)）

- 顺序：exp00 → 主模型与参照模型 → exp01（含 1b）→ exp03 → exp02 → exp04（含 4b）。
- 时间不够时只做“最小可行版”：实验 0、主模型与参照模型、1b、实验 3 的 L1/L3/L4、实验 4 的 B 配置，以及 4b 中漏删 0% 和 20% 两组。
- 最耗时的是 U-LiRA 影子模型：每类至少 3 个，规划是 16–32 个。用首轮实测的耗时决定数量。

### C. 更新 pre（拿到结果之后）

- 按 roadmap 的“展示映射”替换证据：
  - 第 5 页：用 1b 的账户残留比例替换 Carlini；
  - 第 6 页：用实测的成本—准确率曲线；
  - 第 7 页：用人脸模型量化前后或重新学习前后的数字替换 Harry Potter 的 13%→89%；
  - 第 9 页：用 4b 的遗漏率曲线。
- 新建 `docs/script_v2.md`，不要直接改 v1。
- **之前审查中发现的问题还没改**，pre 改版时一并处理：
  1. 第 5 页 Carlini：信息是“从 GPT-2 本身提取出来的”，不是“从训练数据中”；
  2. 第 6 页 SISA 的取舍应写成“准确率 ⇄ 删除成本”，不是“训练便宜 ⇄ 删除便宜”；
  3. 第 7 页 13%→89% 需要核对原文（论文摘要给的平均值是 21%→83%）；第 7 页讲稿还缺 “IF M BREAKS…” 那一句；
  4. 第 4 页和第 9 页的动词要统一（Know/Do/Prove 与 Trace/Isolate/Prove 二选一）；
  5. 第 11 页 “Jinhan” 是拼写错误，应为 Jinghan；
  6. 第 8 页 “And through our framework” 应改为 “But”；
  7. 第 2 页 “In 2017, Ever made a promise” 在 FTC 原文里找不到依据；引号里的承诺也不是原话；
  8. Ever 构建训练集时会**排除已停用账户**的照片，所以第 5 页“删了照片影响也已经进模型”的说法需要补充这个细节，详见 everalbum_paravision.md 第 4 节。
- 时间控制：v1 讲稿约 1,080 词，大约 9–9.5 分钟，余量很小。可删的段落见 rubric 审查（本次会话中给出过）：第 5 页标了 [可删] 的一句、第 3 页 “Put these rules together” 那一段等。

---

## 5. 踩过的坑：绝对不要再踩

### Git 与推送
1. **本机（WSL）用 HTTPS 无法 push**：没有存凭据。推送时改用 SSH 地址，本地 remote 配置不要动：

```bash
git push git@github.com:NGC12-ZJH/aiaa2290-Mini-Ever.git main
```

   因为不经过 `origin`，本地的 `origin/main` 记录会显示“落后”，这是正常现象。核对远程真实状态用 `git ls-remote git@github.com:NGC12-ZJH/aiaa2290-Mini-Ever.git main`。
2. **只有用户明确要求时才 commit 和 push**。用户没要求时去推送，会被权限检查拦下。
3. **绝不提交数据**：`data/`、`runs/`、`results/`、划分清单、权重、身份映射都被 `.gitignore` 忽略了。提交前务必检查 `git diff --cached --name-only`。注意：`src/mini_ever/data/` 是代码，会被提交，这是正常的；`.gitignore` 里的 `data/*` 只匹配仓库根目录下的 `data/`。`*.docx` 也被忽略了，Word 文档要先转成 md 再提交。

### 本机环境（WSL）
4. **系统自带的 Python 3.13 没有 torch。** 本机跑测试要用 conda 环境 `dsaa_ml`（torch 2.12 CPU 版）：

```bash
PYTHONPATH=src ~/miniconda3/envs/dsaa_ml/bin/python -m pytest
```

   不要往这个环境里装包。
5. **本机没有 pdftotext 和 pdftoppm**，Read 工具也打不开 PDF。读 PDF 的办法：`pip install --target <scratchpad>/pylib pypdf`，然后用 `python3 -I` 加上这个路径来读取。读 docx 用 `pandoc`（本机已安装）。

### 实验设计与代码（不要“修回去”）
6. **禁止使用人脸预训练权重**（MS-Celeb-1M、VGGFace2、Glint360K、InsightFace 权重等）。它们见过 CelebA 里的名人，会让所有残留测量失效。代码里刻意没有加载这类权重的路径，配置也会拒绝。
7. **参照模型使用派生种子**（`Context.reference_seed`），这是故意的。如果改成和被评估模型用同一个种子，全量重训得到的模型会和参照一模一样，“通过”就失去了意义。
8. **SISA 的参照必须沿用同样的分片方案**（`assignment_seed` 等于被评估模型的种子），只改变训练种子。
9. **U-LiRA 每类至少 3 个影子模型。** 只有 2 个时，留一法剩下 1 个模型，标准差是 NaN，而且不会报错。代码已经加了这道限制。
10. **L4 重新学习时必须关闭输出过滤**（攻击者拿到的是权重，不是过滤后的输出）。L1 和量化副本则保留过滤。之前的 bug 让输出过滤在 L4 永远“通过”。
11. **暗号必须在缩放之后重新镜像，并且严格居中。** 否则随机水平翻转会让暗号变形。
12. **两个进程不要共用同一个 `runs_dir`**：`artifacts.json` 会被互相覆盖。并行跑实验时，给每个进程准备一个改了 `paths.runs_dir` 的配置。
13. **`make-split --force` 会改变所有缓存键**，所有模型都要重新训练。划分生成之后就不要再动。
14. 用合成数据跑冒烟测试时，必须加 `--no-crop` 参数（合成图片不需要做 CelebA 的人脸裁剪）。

### GPU 平台与登录（2026-11-23 踩过）

- **Claude 不会替用户输入任何平台的密码**（学校 HPC 门户、点动控制台、服务器密码都一样），用户本人同意也不行。需要登录时，让用户自己操作。Claude 要直接操作服务器的话，就用 SSH 密钥：用户自己运行 `ssh-copy-id` 并输入一次密码。密码一律不写进文件或对话。
- **Chrome 插件（Claude in Chrome）装不上**：用户的网络打不开 Chrome 应用商店（`ERR_CONNECTION_CLOSED`），开全局代理、换节点都不行。所以学校 HPC 门户只能让用户自己登录、截图发过来，或者走 SSH。
- **点动的“一键登录”网页终端报过 HTTP 502**（`asset.ddycloud.com` 网关）。直接 SSH 最稳。用户开着全局代理，访问国内服务（点动、学校门户）时可能出问题，需要切到规则模式。
- **学校 HPC 门户要用校园网或 VPN**，和全局代理会冲突。
- **点动镜像自带的 Python 缺 `venv` 和 pip**，要先用 apt 装（实例有免密 sudo）。实例重建后要重新装。
- **服务器用 HTTPS 克隆公开仓库**；服务器上没有 GitHub 推送凭据，不要在服务器上 commit 或 push。

### 结果与诚信
15. **合成数据的冒烟结果不是研究结果，绝不能上 pre。** 合成图案太简单，模型深层面的残留信号接近 0；实验 0 的阳性对照已经报了“测不出差异”。冒烟只证明代码链路是通的。
16. **预期结果（docs/overview.md）是假设，不是数据。** 不能把预期值当成结果写进 PPT 或讲稿。结果和预期相反时也要如实报告。
17. **视觉实验和语言模型的结论不能互相套用。** Mini-Ever 的数字也不代表 Ever 或 Paravision 的真实表现。
18. **只有 4 个人时统计全是噪声**：冒烟里 D 配置为 0.38、4b 曲线不单调，都是噪声。正式实验每组 20 人、多个种子是必需的。

### 事实核查
19. 讲 Ever 案例的事实，以 [docs/everalbum_paravision.md](docs/everalbum_paravision.md) 为准，它已经对照 FTC 原文核对过。几个已知的坑：
    - “2017 年做出删除承诺”没有原文依据；
    - NBC 报道的 “99.85% 准确率” 在 NIST 数据中查不到；
    - Cambridge Analytica、WW/Kurbo、Rite Aid 这几个“删除算法”的后续案例**还没核对原文**。
20. **隐私**：不要把用户的姓名、邮箱等个人信息放进任何发往外部服务的请求里。

---

## 6. 常用命令速查

| 目的 | 命令 |
|---|---|
| 列出还没定的参数 | `python3 -m mini_ever check-config --config <配置>` |
| 生成划分 | `python3 -m mini_ever make-split --config <配置>` |
| 训练或加载模型 | `python3 -m mini_ever train main --config <配置>` |
| 跑实验 | `python3 -m mini_ever run exp01 --config <配置> [--groups 0 1] [--seeds 1 2] [--methods ...]` |
| 生成合成数据 | `python3 scripts/make_synthetic_data.py --out data/synthetic` |
| 测试 | `python3 -m pytest` |

结果写在 `results/<实验名>/<时间戳>.json`，模型缓存在 `runs/models/`，产物清单在 `runs/artifacts.json`。这些都只在本地，不提交。
