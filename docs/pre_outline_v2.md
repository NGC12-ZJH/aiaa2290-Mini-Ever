# Pre 全貌（定稿版）：结构、每页内容、台词、时间、Q&A

> 对应幻灯片：`report/Forgettability_EPS_Presentation_v2.pptx`（27 页：正文 13 页 + 谢谢 + 参考文献 + 附录 12 页）。
> 生成脚本：`scripts/build_slides_v2.py`。实验细节见 `docs/pre_walkthrough.md` 和 `docs/exp00_analysis.md` 到 `docs/exp04_analysis.md`。
> **B 负责的第 4–10 页，以逐字稿 `docs/script_v2_B.md` 为准**（按点击顺序写，台词和屏幕上的字一一对应）；下面第三部分这几页的台词骨架只作概要。
> 讲者：**A** = Qingyang LI，**B** = Jinghan ZHAO。硬性要求：**10 分钟**，第 8 分钟会被提醒；不能看稿。

---

## 零、一句话主线

**公司什么时候能诚实地说“删了”？**

我们的回答：可信的删除要三环都做到。**T** 知道数据去了哪（追踪），**D** 能把影响拿出来（删除），**M** 能证明真的没了（证明）。整体只和最弱的一环一样强：**min(T, D, M)**。

我们搭了一个缩小版的 Ever，把每一环都测了一遍：Ever **找不全**（T），**删不起**（D），**证明不了**（M）。而现实里，监管最后接受的“证明”只是一份宣誓声明。

---

## 一、整体结构

```
开场（A）  1 封面 → 2 承诺 → 3 法律                         问题：删了就够了吗？法律要的是“文件变成了什么”
框架（B）  4 三环 min(T,D,M) → 5 小 Ever 和指标（泄露）             怎么回答：三环 + 一个能测的测试台
证据（B）  6 T → 7 D 概念 → 8 D 实测 → 9 M 标准 → 10 M 实测   每一环先讲道理，再给自己测的数字
收束（A）  11 判决与结局 → 12 最弱一环 → 13 最后一句 → 14 谢谢
备用       15 参考文献 · 16–27 附录 A1–A11（Q&A 用）
```

### 每一页和证据的对应

| 页 | 主张 | 证据 | 来源 |
|---|---|---|---|
| 2 | Ever 承诺删照片，一张没删 | FTC 起诉书 ¶20、¶22 | 真实案例 |
| 3 | 法律问的是“文件变成了什么” | GDPR、EDPB 2024、PIPL | 法律 |
| 5 | 指标：泄露 = 2·AUC − 1，和“从没见过”的模型比 | 指标本身可靠：阳性对照里见过的人好认 16–20 个百分点 | 实验 0（附录 A2、A3） |
| 6 | T：删了照片，人还在 | 特征库 1.0；模型 0.46；删账户还剩 0.16 | 实验 1、1b |
| 8 | D：分片的价格 | 便宜 8 倍，但准确率 43% → 25%，整条链几乎不省 | 实验 2 |
| 10 | M：一关通过不是证明 | 屏蔽名字 0% 但权重 74%；NegGrad+ 暗号 0% 但仍叫出 62% | 实验 3 |
| 11 | 现实的“证明”只是宣誓 | Paravision 合规报告 | 真实案例 |
| 12 | 整体 = 最弱一环 | 系统 B：平均 0.26，攻击者看到 1.00 | 实验 4、4b |

---

## 二、时间表

| 页 | 主题 | 讲者 | 时长 | 累计 |
|---:|---|:-:|:-:|:-:|
| 1 | 封面 | A | 0:10 | 0:10 |
| 2 | 承诺 | A | 0:40 | 0:50 |
| 3 | 法律 | A | 0:45 | 1:35 |
| 4 | 三环模型 | B | 0:50 | 2:25 |
| 5 | 小 Ever 和指标 | B | 1:00 | 3:25 |
| 6 | T：删了照片，人还在 | B | 1:00 | 4:25 |
| 7 | D 概念：分片 | B | 0:35 | 5:00 |
| 8 | D 实测 | B | 0:45 | 5:45 |
| 9 | M 概念：证明的标准 | B | 0:30 | 6:15 |
| 10 | M 实测 | B | 1:00 | 7:15 |
| 11 | 判决与结局 | A | 0:55 | 8:10 |
| 12 | 最弱一环 | A | 0:55 | 9:05 |
| 13 | 最后一句 | A | 0:20 | 9:25 |
| 14 | 谢谢 | A & B | 0:10 | 9:35 |

**余量约 25 秒**，很紧。

- **第 8 分钟提醒时，应该在第 11 页快讲完的地方。** 如果提醒响时还在第 10 页，第 12 页跳过 4b 那句，直接讲系统 B。
- **超时时按这个顺序砍**：
  1. 第 12 页的 4b（漏追踪）那句，约 10 秒；
  2. 第 3 页三张法律卡片各压成半句，约 15 秒；
  3. 第 7 页“IF D BREAKS”那句不讲，约 5 秒。
- **讲者时间**：B 约 5:05，A 约 4:30。如果要更平衡，可以把第 12 页交给 B，A 从第 11 页接回、讲第 13 页收尾。

---

## 三、逐页内容

每页按“**屏幕上有什么 → 要讲清楚的点 → 台词骨架**”排列。台词是骨架，不要背成逐字稿，要讲成自己的话。

### 第 1 页 封面 · A · 0:10

- **屏幕**：Forgettability；When can a company honestly say “deleted”?
- **台词**：“Good morning. I’m Qingyang LI, and this is Jinghan ZHAO. Today we have one question: when can a company honestly say ‘deleted’?”

### 第 2 页 承诺 · A · 0:40

- **屏幕**：客服原话“…this will permanently delete all photos and videos stored on your account.”；大大的 **0**；“would that have been enough?”
- **要讲清楚**：
  1. Ever 告诉停用的用户，照片会被永久删除。
  2. FTC 查出：直到至少 2019 年 10 月，**一个停用用户的照片都没删**。
  3. 抛问题：就算全删了，够不够？并预告结局。
- **台词**：
  > “Let’s start with a real story. A photo app called Ever told users who deactivated: this will permanently delete all your photos. According to the FTC, until at least October 2019, it deleted [停一拍] none.
  >
  > That part is easy to judge. But here is the harder question: even if Ever had deleted every photo — would that have been enough? Hold on to that. We’ll tell you what actually happened to Ever at the end.”
- **注意**：不要说 “In 2017, Ever promised”（起诉书没给年份）。

### 第 3 页 法律 · A · 0:45

- **屏幕**：三张卡片 GDPR 第 17 条 / EDPB 2024 / PIPL 第 47 条；“Legal promise ? Technical reality”；底部：“no delete button for model parameters”。
- **要讲清楚**：删除是法律权利；但法律问的已经不是“文件删了没”，而是“文件变成了什么”。
- **台词**：
  > “In Europe, the GDPR gives a right to erasure. In 2024, European regulators asked: if personal data can still be extracted from a model, is that model really anonymous? China’s PIPL says: when deletion is technically hard, stop processing.
  >
  > So the question is no longer ‘did you delete the file?’ — it’s ‘what did the file become?’ The obligation is clear. The technical path is not: there is no delete button for model parameters.”
- **交接一**：A：“So what would Ever actually have needed to keep its promise?”

### 第 4 页 三环模型 · B · 0:50

- **屏幕**：T、D、M 三个环；**C = min(T, D, M)**；“Credible deletion is only as strong as its weakest link.”
- **要讲清楚**：三个动作缺一不可；不是打分，是一条链。
- **台词**：
  > “We think the answer is three links in a chain. T, traceability: do you know where the data went? D, deletability: can you take its influence out? M, measurable forgetting: can you prove it’s gone? Know, do, prove.
  >
  > A chain is only as strong as its weakest link — so credible deletion is the minimum of the three. And we didn’t want to argue this only with examples. So we built one.”

### 第 5 页 我们搭了一个小 Ever · B · 1:00

- **屏幕**：左边流程图（1,000 名人 / 600 用户 / 约 40% 照片是朋友传的 → 主模型 → 特征库、手机版、学生模型、旧存档）。右边“THE METRIC · LEAKAGE”卡片，分三步：① 给每个被删的人打分（系统把他的新照片和他本人对得上的程度）；② 在没见过他们的参照模型上再打一次；③ 比较所有配对，AUC = 删除后的系统得分更高的比例。下面是公式 **Leakage = 2 · AUC − 1**，以及 0 到 1 的刻度（0 = 抛硬币 = 忘了；1 = 每次都认得）。最后两行判定规则：整个 90% 区间 ≤ 0.1 才算通过（界值事先定好）；整个系统看最差的那个副本。
- **要讲清楚**：
  1. 测试台像一家真公司：主模型加四个下游副本。
  2. **指标**：不是看“还认不认得出”（人脸模型本来就能认陌生人），而是和从没见过这些人的模型比，能不能分得出来。
  3. 怎么判通过、整个系统怎么算。
  4. 诚实声明，一次说清。
- **台词**：
  > “We built a mini-Ever: a thousand celebrities, six hundred of them app users, and a pipeline like a real company’s — a main model, a face gallery, a phone copy, a smaller model distilled from it, and old checkpoints. Twenty users ask to be deleted; we delete them, then check every copy.
  >
  > Our metric is leakage. For each deleted person, we score how well the system matches a new photo of them. We do the same on a model trained without them. Then we compare every pair: AUC is how often the deleted system scores higher, and leakage is two AUC minus one. Zero is a coin flip — forgotten. One means it always still knows them. A copy passes only if its whole interval stays below 0.1, fixed in advance — and a system is only as good as its worst copy.
  >
  > It’s a small model on celebrity photos, not Ever’s system — it shows where the structure breaks, not how Ever would have scored.”
- **Q&A 后手**：名人数据集的问题见附录 A3（实验 0）。

### 第 6 页 T：删了照片，人还在 · B · 1:00

- **屏幕**：上面 Ever 的真实数据链；左下 6 个节点的泄露条形图（**特征库 1.00** 强调色，主模型 / 手机版 / 旧存档 0.46，学生 0.04，照片库 0）；右下“删本人账户再重训”三根条：0.46 / **0.16** / 0。
- **要讲清楚**：T 环断在两处：① 不知道下游有哪些副本；② “这个人的照片” ≠ “这个账户的照片”。
- **台词**：
  > “First: where did the photos go? Ever promised to delete only the first box. But photos from users who never consented — and users who left after training — had already shaped the model.
  >
  > So we deleted every photo of twenty users, and only the photos. The photo store was empty. The face gallery still matched every one of them. The model, its phone copy and its old checkpoint still knew them almost as well as before.
  >
  > Then we did what a careful company would do: delete everything the users uploaded themselves, and retrain. A third of the memory was still there — because their friends had uploaded photos of them too. Deleting an account is not forgetting a person.”
- **注意**：不要再说 “the influence had already travelled down the chain”（训练集排除了已停用账户）。

### 第 7 页 D 概念：分片 · B · 0:35

- **屏幕**：左“一个模型给所有人”（删人 = 全部重训，或走捷径）；右“切成 10 片（SISA）”，第 3、7 片高亮（删人 = 只重训这两片）；“Recognition accuracy ⇄ Cheap to forget”（分片让删除便宜，代价是准确率）；右下深色框“So we ran it: one big model vs. 1–16 shards →”。
- **要讲清楚**：SISA 的思路：把数据切开，删一个人只重训他所在的那一片。代价是每片看到的数据变少了。
- **台词**：
  > “Now suppose Ever traced everything. Can it take the influence out? With one big model, you have two options: retrain everything, which is expensive, or take a shortcut by editing the model.
  >
  > There’s a design idea called SISA: split the data into shards, each with its own small model. If the users to forget sit in shards three and seven, you retrain only those two. Cheap to forget — but each small model sees less data. Ever’s real architecture isn’t public, so we tested the idea itself.”

### 第 8 页 D 实测 · B · 0:45

- **屏幕**：左折线图，“只重训模型”65 → 8 秒一路下降，“整条链”143 → 99 → 115 → **167** 秒先降后升（强调色）；右准确率柱状图 58% / 43% / 32% / 29% / **25%**；底部：“Design sets the ceiling — and the ceiling has a price.”
- **要讲清楚**：只看模型，分片便宜 8 倍；但准确率掉了四成；算上下游，16 片和大模型差不多贵。删人本身不伤模型，伤模型的是“为了好删而做的设计”。
- **台词**：
  > “We ran it: twenty deletion requests, one at a time. Sixteen shards made each retraining about eight times cheaper. But recognition accuracy fell from forty-three percent to twenty-five.
  >
  > And that was only the model. A real deletion also rebuilds everything downstream — the gallery, the phone copy, the distilled model. Counting all of that, deleting from sixteen shards cost about as much as retraining the big model. Design sets the ceiling — and the ceiling has a price.”

### 第 9 页 M 概念：证明的标准 · B · 0:30

- **屏幕**：整页一张“标准”卡片：删除后的模型 ≈ 从没见过的模型（Guo 等人，ICML 2020），以及“不是‘还认不认得出’，因为人脸模型本来就能认陌生人”；右下：“So we tested faces: six methods, five tests →”；底部：“The benchmark is not silence. It’s the never-trained model.”
- **要讲清楚**：“证明”的标准是**表现得和从没见过一样**，不是“认不出来”。一句话带到实测。
- **台词**：
  > “Last link: can Ever prove it worked? First, what does ‘proved’ mean? Guo and colleagues give the standard: a model that forgot should behave like a model that never saw the data — not merely fail to recognise them, because face models recognise strangers too. The benchmark is not silence. It’s the never-trained model. So we tested exactly that.”
- **已删除**：哈利·波特的反例（13% → 89%）不再上屏，也不再讲。被问到“压缩会不会让记忆回来”时，用第 10 页的结果回答：“Here they had never left.”

### 第 10 页 M 实测 · B · 1:00

- **屏幕**：6 种方法 × 5 关（L1–L5）的表格，第一列按类型分组：**捷径**（只屏蔽名字，只改输出）、**近似遗忘**（微调、NegGrad+、SCRUB，改动权重）、**精确重训**（全量、SISA，不用这些人的数据重训）。格子里只有 ✓/✗，最后一列是“过了几关”。只屏蔽名字的 L1、NegGrad+ 和 SCRUB 的 L5 是深色“✓ passed”格（看起来过关，但在不同的列）；✗ 用强调色；全量重训 5/5，SISA 3/3。左下只留讲稿里会说的两个数字：**74%**（关掉过滤后权重仍认得）和 **62–64%**（NegGrad+/SCRUB 擦掉暗号后仍叫得出名字）。右下：“One passed test is not proof.”；底部：“A changed output is not a changed model.”
- **具体数字**（每一关的百分比、泄露值）都在附录 A8。被问到“这个 ✗ 具体是多少”时翻过去。
- **要讲清楚**：两种捷径各过了一关，**过的不是同一关**；只有重训每关都过，而且只贵不到 2 倍。
- **台词**：
  > “We tested six deletion methods, each against the never-trained model. The shortcut — just hiding the names — passed the first test perfectly: zero percent. But switch the filter off, and the weights still recognised [停一拍] seventy-four percent of them. A hidden marker we had planted still fired every time.
  >
  > Two standard unlearning methods failed the other way. They erased the marker completely — a marker test would say: deleted. Yet the model still named about two out of three people.
  >
  > Compression didn’t bring the memories back — they had never left. Only retraining passed every test, at less than twice the cost. One passed test is not proof.”
- **交接二**：B：“So Ever couldn’t trace, couldn’t cheaply isolate, and couldn’t prove.” A：“So what did the regulator actually do — and what happened to Ever?”

### 第 11 页 判决与结局 · A · 0:55

- **屏幕**：FTC 要删的三类东西，下面标出我们的对应结果（Ever 0 张 / 特征库泄露 1.0 / 模型仍有 0.46）；三张卡片：Chopra 原话、我们的解读、“What actually happened”时间线；底部：“The only proof accepted was a sworn statement. No one tested the forgetting.”
- **要讲清楚**：① FTC 不只要删数据，还要删模型；② 用三环解释为什么要删整个模型；③ **兑现第 2 页的悬念**：结局本身就是 M 环的现实版。
- **台词**：
  > “In 2021, the FTC ordered Everalbum to delete three things: the photos, the face embeddings, and the models and algorithms built with users’ photos. Not just the data — the models too. Commissioner Chopra said the company must ‘forfeit the fruits of its deception.’
  >
  > Through our lens: if you can’t trace, isolate or prove, deleting the whole model is the only deletion that needs no further proof.
  >
  > And what happened to Ever? It had already shut down in 2020. Paravision says it deleted everything the order required. The evidence? A sworn statement. No technical test. No fine. That is exactly the M link.”

### 第 12 页 最弱一环 · A · 0:55

- **屏幕**：上方 Trace / Isolate / Prove；左边系统 B 两根条：“各部分平均 0.26”对“攻击者看到的 **1.00**”；右边 A–D 四个系统的泄露；底部：“Credible deletion is only as strong as its weakest link.”
- **要讲清楚**：min(T, D, M) 不只是口号。修好不是最弱的环，整体不变；只有每个节点都做到，才和“从没见过”分不出来。
- **台词**：
  > “Ever’s promise was one sentence. Keeping it took three things: trace, isolate, prove.
  >
  > We tested the weakest-link idea, too. We retrained the main model perfectly — but left the old face gallery in place. The model was clean. The person was still found, every single time. Averaged over the parts, it looks like most of the job was done. But an attacker doesn’t average — they use the weakest part. Only the system that handled every copy was indistinguishable from one that never saw them.”
- **时间够再加 4b**：“Tracing can be imperfect, but not by much: missing one photo per person left no trace; missing eight brought back about forty percent of the memory.”

### 第 13 页 最后一句 · A · 0:20

- **台词**：“Deleting a record is an operation. Forgetting a person is a claim — and a claim needs proof.”（放慢，说完停两秒。）
- 这句话背后的证据：**operation**（实验 1）→ **forgetting a person**（实验 1b、4b）→ **claim needs proof**（实验 3、4，以及第 11 页的宣誓声明）。

### 第 14 页 谢谢 · A & B · 0:10

- A：“Thank you.” B：“We’re happy to take your questions.”

---

## 四、台上不能说的话

| ❌ 不要说 | ✅ 改成 | 原因 |
|---|---|---|
| “In 2017, Ever promised…” | “Ever told users who deactivated…” | 起诉书没给承诺的年份 |
| 给概括的承诺加引号 | 用客服原话，或不加引号 | 不是原话 |
| “The influence had already travelled down the chain” | “Photos from users who never consented, and users who left after training…” | 训练集构建时排除了已停用账户 |
| “Ever distilled / quantized its model” | “A pipeline like a real company’s also has a phone copy and a distilled model” | 起诉书没写 |
| “Approximate unlearning doesn’t work” | “With settings fixed in advance, they forgot only 10–16%” | 参数没调过 |
| “Compression doesn’t bring memories back in faces” | “Here they had never left” | 近似方法本来就没忘，仍是开放问题 |
| “Deleting the account does almost nothing” | “Deleting the account removed most of it — but a third remained” | 实测去掉了 60–75% |
| “Missing just 5% brought the leakage back” | “Missing one photo left no trace; missing eight brought it back” | 5% 只有 0.01 |
| “This is how Ever would have scored” | “This shows where the structure breaks” | 小模型、名人照片 |

---

## 五、Q&A：问题 → 回答 → 翻到哪一页

附录在第 16–27 页。每页右下角有“APPENDIX · FOR Q&A”标记，被问到时直接翻过去。

| 可能被问 | 回答要点 | 谁答 | 翻到 |
|---|---|:-:|---|
| 名人数据集，模型是不是早就认识他们？ | 用户数据进来前测过：遗忘组和其他用户一样；阳性对照里见过的人好认 16–20 个百分点，说明尺子灵 | B | A3 |
| 泄露 0.46 是什么意思？为什么两两比较？ | 100 次比较里 73 次删除后的系统更认得；攻击者只能拿分数和“没见过的人”比 | B | A2 |
| 90% 区间、界值是怎么定的？ | 按人重抽样 2,000 次；界值 0.1 跑之前就冻结在配置里 | B | A2 |
| 删账户剩的三分之一，是不是噪声？ | 两个“从没见过”的模型之间只差 0–0.1；三组里两组高于噪声线 | B | A5 |
| 学生模型为什么几乎干净？ | 教它的数据里没有这些人，影响只能经过老师间接传，这条路很弱 | B | A4 |
| ResNet-18 和 ResNet-50 比，公平吗？ | 加了 1 片 ResNet-18 对照：换小模型掉 15 个点，切 16 片再掉 18 个点 | B | A6 |
| SISA 删得干净吗？ | 按构造是精确的。SISA 的问题不是证明，是价格 | B | A6、A8 |
| 近似方法是不是参数没调好？ | 可能，参数是事先固定的。正因为如此才需要测试；而且重训只贵不到 2 倍 | B | A7、A8 |
| 成员推断用的是真正的攻击吗？ | 主结果是简化版；完整 U-LiRA 抽查：NegGrad+ AUC 0.95，重训 0.51（不会误报） | B | A8 |
| 暗号被擦掉了，暗号测试是不是没用？ | 有用，但不能单独用：暗号贴在要删的照片上，最先被擦掉；身份分散在全部照片里 | B | A8 |
| 取最大值是你们自己定义的吧？ | 是，因为攻击者用最弱的地方。实验的发现是：修好其他部分，整体不变 | A | A9 |
| 漏 5% 没事，追踪是不是不用很准？ | 漏 1 张测不出，漏 8 张明显回来。公司事先不知道自己在门槛哪一边 | A | A10 |
| 为什么 FTC 没罚款？ | 当时 FTC Act 下首次欺骗通常不能罚款，Chopra 也批评了这一点 | A | — |
| 删模型是 FTC 首创吗？ | Chopra 称其为 “course correction”：之前 Google/YouTube、Facebook 的和解都没要求交出算法 | A | — |
| Paravision 现在的模型干净吗？ | 公司自述只用公开数据、员工和第三方的同意数据训练，FTC 没有独立核实 | A | — |
| 你们的局限是什么？ | 每组 20 人、3 组；实验 2 一个种子；实验 3 主结果用简化攻击；不代表 Ever | 任一 | A11 |

**回答的格式**：先一句结论，再一个数字，最后（需要时）翻到附录那一页指给对方看。不确定的不要硬答，就说“我们的数据只能说明……”。

---

## 六、对照评分标准

| 评分项 | 在哪体现 |
|---|---|
| Significance | 第 2 页真实案例；第 3 页三地法律；第 11 页 FTC 首次要求删模型 |
| Originality | **第 4 页 min(T, D, M) 框架 + 第 5 页自己搭的测试台**，这是和其他组拉开差距的地方 |
| Diversity | 法律（欧盟、中国、美国）；技术（6 种删除方法、5 关测试）；立场（用户、公司、监管、攻击者） |
| Workload | 第 6、8、10、12 页都是自己测的数字；附录 11 页的完整流程 |
| Introduction | 第 1–2 页：一个问题 + 一个“0” |
| Organization | 问题 → 框架 → 测试台 → 每环“先概念、后实测” → 现实结局 → 最弱一环 → 一句话 |
| Clarity | 第 5 页先讲清 0 和 1 的含义；D 先讲分片概念、M 先讲证明标准，再给数字 |
| Q&A | 附录按问题组织，每个常见问题都能翻到对应的一页 |

---

## 七、排练清单

1. 两人各自把自己的页讲成自己的话，不背逐字稿。
2. 至少完整计时排练 2 次，记下每次第 8 分钟时讲到哪一页。
3. 在投影或大屏上过一遍附录，确认表格字号看得清。
4. 互相用第五部分的问题提问，练习“结论 → 数字 → 翻页”。
5. 在幻灯片放映模式里点一遍，确认每页的点击顺序和自己讲的顺序一致。
