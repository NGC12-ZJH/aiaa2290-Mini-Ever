# Everalbum / Ever / Paravision 案例资料

> 用途：为 pre 第 2、5、8 页及 Q&A 提供可核对的事实依据。
> 主要依据 FTC 原始文件（起诉书、委员声明、Paravision 合规报告），新闻报道作为补充。引文保留英文原文，方便直接引用。
> 整理日期：2026-11-23。标注“待核”的条目未在原始文件中找到依据。

---

## 1. 一句话概括

Everalbum, Inc. 运营免费云相册 App **Ever**，同时用 Ever 用户照片中提取的人脸训练自研人脸识别技术，并通过企业品牌 **Ever AI（后改名 Paravision）** 卖给企业客户。FTC 认定其存在两项欺骗：

1. 默认对用户开启人脸识别，用户无法关闭；
2. 承诺用户停用账户后删除照片，实际一张也没删。

2021 年的和解令不仅要求删除数据，还要求删除**用这些数据训练出的模型和算法**。

---

## 2. 时间线

| 时间 | 事件 | 来源 |
|---|---|---|
| 2013 | NBC 报道称该 App 始于 2013 年 | [NBC News][nbc] |
| 2015 起 | Everalbum 向消费者提供 Ever，全球约 **1,200 万**次安装 | [FTC 起诉书][complaint] ¶3 |
| 2017-01 起 | 约 **36,000** 名用户停用了账户 | [FTC 起诉书][complaint] ¶17 |
| 2017-02 | 上线 “Friends” 功能，用人脸识别按人物分组照片；**对所有移动端用户默认开启，且无法关闭** | [FTC 起诉书][complaint] ¶5 |
| 2017-09 至 2019-08 | 把从用户照片中提取的“数百万”张人脸图像与公开数据集合并，先后构建 **4 个训练数据集** | [FTC 起诉书][complaint] ¶12 |
| 2018-05 | 仅对 **德州、伊利诺伊、华盛顿州和欧盟**用户弹窗征求同意，并提供开关 | [FTC 起诉书][complaint] ¶6 |
| 2018-06 | 用第 3 个数据集训练的技术提交给 NIST 做准确率测试 | [FTC 起诉书][complaint] ¶15 |
| 2018-07 起 | 帮助页面声称 “When face recognition is turned on, you are letting us know…”。FTC 认定该说法对其他地区用户具有误导性 | [FTC 起诉书][complaint] ¶9–10 |
| 2019-04 | 弹窗和开关推广到所有用户 | [FTC 起诉书][complaint] ¶7 |
| 2019-04-15 | NBC 联系公司一周后，隐私政策新增一句 “Some of these technologies may be used in our separate products and services for enterprise customers.” | [NBC News][nbc] |
| 2019-05-09 | NBC News 报道 Ever 用用户照片训练并对外销售人脸识别技术 | [NBC News][nbc] |
| 2019-08 | 第 4 个数据集（**只用已同意用户**的人脸）训练出的技术，同时用于 Ever App 和 Paravision 的企业服务 | [FTC 起诉书][complaint] ¶16 |
| 2019-10 | 此前**从未删除**任何停用用户的照片；从这时起才开始删除停用超过 3 个月账户的照片 | [FTC 起诉书][complaint] ¶22 |
| 2020-08-24 | 宣布关闭 Ever，称原因是来自 Apple 和 Google 的竞争；所有照片计划于 8 月 31 日删除 | [MacRumors][macrumors] |
| 2020-09 | 合规报告写的是 “In September 2020, Paravision voluntarily shut down…”，另一处写 2020-09-30 | [合规报告][compliance] |
| 2020-10-02 | 伊利诺伊用户依 BIPA 提起集体诉讼 *Walton v. Everalbum*（案号 4:20-cv-06895，加州），结果待核 | [ClassAction.org][classaction] |
| 2021-01-08 | Chopra 委员声明落款日期 | [Chopra 声明][chopra] |
| 2021-01-11 | FTC 公布起诉书和拟议和解，投票 **5-0** | [FTC 新闻稿 2021-01][pr-jan] |
| 2021-05-06/07 | 正式发出起诉书和决定令（Docket C-4743），终裁投票 **4-0** | [FTC 新闻稿 2021-05][pr-may]、[FTC 起诉书][complaint] |
| 2021-09-07 | Everalbum, Inc. 正式更名为 Paravision, Inc. | [合规报告][compliance] 脚注 1 |
| 2022-05-05 | Paravision 提交一周年合规报告 | [合规报告][compliance] |

---

## 3. “删除承诺”的原话（pre 第 2 页）

起诉书引用了三处承诺，**都没有注明是哪年做出的**：

- **停用界面** ¶18–19：“If you choose to deactivate your account, you will permanently lose access to [##] photos…” → “Are you sure? You will lose access to your account and we can't undo this.”（按钮写的是 **DELETE**）
- **客服回复** ¶20：“Please note that this will **permanently delete all photos and videos** stored on your account as well.”
- **隐私政策** ¶21，措辞有保留：“we will **try to delete** your information as soon as possible upon request… there might be latency… backed-up versions might exist after deletion.”

FTC 的认定 ¶22：

> “until at least October 2019, Everalbum did not, in fact, delete the photos or videos of **any** users who had deactivated their accounts and instead retained them indefinitely.”

---

## 4. 数据链与 Paravision（pre 第 5 页）

- 2017 年 2 月 Friends 刚上线时，用的是**公开的**人脸识别技术。之后公司开始自研，并 “in four instances” 用从用户照片中提取的人脸改进模型（¶11）。
- 4 个数据集的筛选条件（¶12）：
  - **不属于已停用账户**；
  - 不模糊、不太小、不重复；
  - 同一标注身份要有足够多的图片；
  - 其中 3 次排除了机器判定未满 13 岁的人脸。
- 各数据集的地区限制：

| 数据集 | 时间 | 额外排除 | 去向 |
|---|---|---|---|
| 1 | 2017 秋 | — | 测试后弃用（¶14） |
| 2 | 2018-04 | 美国和欧盟用户（按 IP 判断） | 测试后弃用（¶14） |
| 3 | 2018-06 | 伊利诺伊、德州、华盛顿州和欧盟用户 | 提交 NIST 测试（¶15） |
| 4 | 2019-08 | 未开启开关或未在弹窗中点 “Yes” 的用户 | Ever App + **Paravision 企业服务**（¶16） |

- 用途：Paravision 把技术卖给企业客户，用于 “security, access control, and facilitating payments”（¶16）。Chopra 声明提到客户包括 “security and air travel industries”。
- FTC 称公司 “has not shared images from Ever users' photos… with Paravision's customers”。泄露出去的是**模型**，不是照片本身。
- 规模：Ever AI 对外宣传有 “13 billion photos and videos” 的私有数据集，来自 “tens of millions of users in 95 countries”（[NBC][nbc]）。这是公司的营销说法，与 FTC 给出的约 1,200 万次安装不是同一口径。
- 营销与实际客户：Ever AI 曾向执法和军方推销（“enhance surveillance capabilities”）。但据 NBC，当时 “has secured contracts only with private companies”。

> ⚠️ **对 pre 的影响**：训练集在构建时会排除“已停用账户”的人脸。因此，“停用用户的照片 → 进入模型”这条链只对**在某个数据集构建之后才停用**的用户成立。FTC 要求删除模型，主要理由是模型用了**未经同意**的用户人脸，而不是停用用户的人脸。第 5 页说 “even if it had [deleted], the influence had already travelled down the chain”，建议改得更准确，例如 “photos from users who never consented, and users who left after training, had already shaped the model”，以防在 Q&A 被追问。

---

## 5. FTC 命令内容（pre 第 8 页）

依据：[FTC 新闻稿 2021-01][pr-jan]、[2021-05][pr-may]，以及[合规报告][compliance]中逐条转引的命令原文。

| 条款 | 内容 | 期限 |
|---|---|---|
| §I | 禁止就收集、使用、删除个人信息（含 face embeddings）作虚假陈述 | — |
| §II | 用用户生物信息生成 face embedding 或训练、修改人脸模型前，须明确披露并取得 **affirmative express consent**（仅对美国用户适用） | — |
| §III.A | 删除**截至命令日已申请停用**的用户的全部照片和视频 | **30 天**，须提交宣誓声明 |
| §III.B | 删除**未明确同意**用户的全部 face embeddings | **90 天**，须提交宣誓声明 |
| §III.C | 删除或销毁全部 **“Affected Work Product”**，即用 Ever 用户生物信息开发的模型和算法。[JOLT][jolt] 的表述是 “all models and algorithms developed in any part using any biometric information… collected from users of the Ever app” | **90 天**，须提交宣誓声明 |
| §IV–VII | 回执、合规报告、记录保存、配合监管 | 回执分发 10 年 |
| §VIII | 命令有效期 **20 年** | — |
| 罚款 | **无罚款**。之后每次违反命令，最高可罚 $43,280 | [FTC 新闻稿 2021-01][pr-jan] |

**执行结果**：Paravision 称已 “timely submitted written statements… confirming it deleted the data required under Order § III (A), (B), and (C)”。公司还声明，现在销售的技术只用以下数据训练：公开数据集、签过书面同意的员工影像、合同约定须取得同意的第三方数据（[合规报告][compliance]）。这些是公司**自述**，FTC 没有对其作独立核实。

---

## 6. Chopra 委员声明要点（已对照原文 PDF）

[原文][chopra]，日期 2021-01-08，标题 *In the Matter of Everalbum and Paravision*。

- > “the FTC's proposed order requires Everalbum to **forfeit the fruits of its deception**. Specifically, the company must delete the facial recognition technologies enhanced by any improperly obtained photos.”
- > “Commissioners have previously voted to allow data protection law violators to retain algorithms and technologies that derive much of their value from ill-gotten data. This is an important **course correction**.”
  - 脚注把此案与 Google/YouTube（2019，3-2）和 Facebook（2019，3-2）两起和解对比：那两起都**没有**要求交出算法。
- > “the settlement does not require the defendant to pay any **penalty**. This is unfortunate.”
- 他认为州法起了保护作用：伊利诺伊、华盛顿、德州有生物识别立法，公司对这些州的用户更谨慎，“The company's deception targeted Americans who live in states with no specific state law protections.”
- 开头立场很鲜明：“Today's facial recognition technology is fundamentally flawed and reinforces harmful biases.”

---

## 7. 对照 pre 的核对清单

| pre 中的说法 | 核对结果 | 建议 |
|---|---|---|
| “In 2017, … Ever made a simple promise” | ⚠️ 起诉书没有给出承诺的年份。2017 只对应 Friends 上线（2 月）和“自 2017 年 1 月起约 36,000 人停用” | 去掉 “In 2017”，改成 “Ever told users who deactivated…”；或改成 “Since 2017, about 36,000 users deactivated…” |
| “Until at least October 2019, Ever deleted none” | ✅ 起诉书 ¶22 原话是 “any users” | 保留 |
| 幻灯片引用 “Deactivate your account, and we delete your photos.” | ⚠️ 这是概括，不是原话。最接近的原话是客服回复 “this will permanently delete all photos and videos…” | 幻灯片上去掉引号，或换成原话 |
| 照片 → embeddings → 训练数据 → 模型 → Paravision | ✅ 有依据（¶12、¶16） | 补充“构建时排除停用账户”这一细节（见第 4 节） |
| FTC 下令删除三类东西 | ✅ | 可以补充 “within 90 days, sworn statements, no fine” |
| “forfeit the fruits of its deception” | ✅ 原文核对一致，Chopra 2021-01-08 | 保留 |
| “We'll tell you what actually happened to Ever at the end” | ✅ 补充：Ever 在命令下达前（2020 年 8–9 月）已自行关停 | Q&A 素材 |

---

## 8. Q&A 可能用到的补充点

- **为什么没有罚款？** 根据 FTC Act 当时的结构，首次违法的欺骗行为通常无法罚款，Chopra 对此提出了批评。
- **“删模型”是 FTC 首创吗？** JOLT 称本案是 FTC “first case primarily focused on misuse of facial recognition”。Chopra 称其相对以往和解是 “course correction”。此前 2019 年 Cambridge Analytica 的命令据称也涉及删除算法类“工作成果”，**待核**。之后的 WW/Kurbo（2022）、Rite Aid（2023）等案也有类似要求，**待核**，引用前需查原文。
- **能证明模型真的删了吗？** 唯一的证据是公司提交的**宣誓声明**，没有技术层面的审计。这正好对应我们的 M 环：法律接受“宣誓”，并不检验“遗忘”本身。
- **州法差异**：同一家公司对不同州的用户采取了不同的同意流程，说明有立法约束确实会改变公司的做法。

---

## 来源

**FTC 原始文件**
- [FTC 案件页 *Everalbum, Inc., In the Matter of*（File No. 1923172）][case]
- [FTC 新闻稿，2021-01-11：California Company Settles FTC Allegations It Deceived Consumers about use of Facial Recognition in Photo Storage App][pr-jan]
- [FTC 新闻稿，2021-05-07：FTC Finalizes Settlement with Photo App Developer Related to Misuse of Facial Recognition Technology][pr-may]
- [起诉书（终版，2021-05-06，Docket C-4743）][complaint]
- [决定令（终版）][order]：未直接阅读，条款依据合规报告中的逐条转引
- [Commissioner Rohit Chopra 声明，2021-01-08][chopra]
- [Paravision, Inc. 合规报告（2022，节选公开版）][compliance]

**新闻与评论**
- [NBC News，2019-05-09：Millions of people uploaded photos to the Ever app. Then the company used them to develop facial recognition tools.][nbc]
- [MacRumors，2020-08-24：Photo Storage Service 'Ever' Shutting Down and Deleting All Photos and Videos on August 31][macrumors]
- [Harvard JOLT Digest，2021-01-13：Everalbum, Inc. in First Facial Recognition Misuse Settlement, FTC Requires Destruction of Algorithms…][jolt]
- [ClassAction.org，2020-11-10：Class Action Says Paravision Illegally Mined 'Billions' of Everalbum Photos…][classaction]
- [Wikipedia：Paravision (identity verification service)][wiki]

**其他报道（搜索结果中出现，本次未逐篇阅读）**
- [CNBC，2019-05-09](https://www.cnbc.com/2019/05/09/ever-developed-facial-recognition-tools-using-photos-uploaded-to-app.html)
- [Engadget，2019-05-09](https://www.engadget.com/2019-05-09-ever-photo-storage-app-facial-recognition.html)
- [EPIC，2021-01](https://epic.org/2021/01/ftc-orders-photo-app-to-delete.html)
- [Weil 律所简报：FTC Orders Destruction of Algorithms…](https://www.weil.com/-/media/mailings/2021/q2/ftc-orders-destruction-of-algorithms-created-from-unlawfully-acquired-datax.pdf)

[case]: https://www.ftc.gov/enforcement/cases-proceedings/1923172/everalbum-inc-matter
[pr-jan]: https://www.ftc.gov/news-events/news/press-releases/2021/01/california-company-settles-ftc-allegations-it-deceived-consumers-about-use-facial-recognition-photo
[pr-may]: https://www.ftc.gov/news-events/press-releases/2021/05/ftc-finalizes-settlement-photo-app-developer-related-misuse
[complaint]: https://www.ftc.gov/system/files/documents/cases/1923172_-_everalbum_complaint_final.pdf
[order]: https://www.ftc.gov/system/files/documents/cases/1923172_-_everalbum_decision_final.pdf
[chopra]: https://www.ftc.gov/system/files/documents/public_statements/1585858/updated_final_chopra_statement_on_everalbum_for_circulation.pdf
[compliance]: https://www.ftc.gov/system/files/ftc_gov/pdf/paravision_compliance_report_redacted.pdf
[nbc]: https://www.nbcnews.com/tech/security/millions-people-uploaded-photos-ever-app-then-company-used-them-n1003371
[macrumors]: https://www.macrumors.com/2020/08/24/everalbum-shutting-down/
[jolt]: https://jolt.law.harvard.edu/digest/everalbum-inc-in-first-facial-recognition-misuse-settlement-ftc-requires-destruction-of-algorithms-trained-on-deceptively-obtained-photos
[classaction]: https://classaction.org/news/class-action-says-paravision-illegally-mined-billions-of-everalbum-photos-to-develop-facial-recognition-tech
[wiki]: https://en.wikipedia.org/wiki/Paravision_(identity_verification_service)
