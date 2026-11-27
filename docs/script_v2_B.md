# 逐字稿 v2 · B（Jinghan ZHAO）· 第 4–10 页

> 对应 `report/Forgettability_EPS_Presentation_v2.pptx` 第 4–10 页，约 **5 分钟**（2:25 → 7:15）。
> **原则：嘴上说的，屏幕上都有。** 台词里的**粗体**是屏幕上原样出现的字，说到时观众正好能看到。
> `▶ 点击` 表示按一下翻页笔，后面那句话就是这一下出现的内容。不要先说后点，要**先点再说**。

---

## 接棒（A 在第 3 页结尾）

**A**：“So what would Ever actually have needed to keep its promise?”

---

## 第 4 页 三环模型 · 0:50

*屏幕一开始只有标题。讲到哪个环就指哪个环。*

▶ **点击 1**（T 环出现）
> “We think the answer is three links in a chain. The first is **T — Traceability**: **where did the data go?** That’s about **knowing**.”

▶ **点击 2**（D 环）
> “The second is **D — Deletability**: **can it be taken out — and how?** That’s about **doing**.”

▶ **点击 3**（M 环）
> “The third is **M — Measurable forgetting**: **can you prove it’s gone?** That’s about **proving**.”

▶ **点击 4**（公式和底部两行）
> “Know, do, prove. So we write credible deletion as **the minimum of T, D and M**. **Credible deletion is only as strong as its weakest link.**
>
> This is **a conceptual model, not a scoring system**. And we didn’t want to argue it only with examples — so **we built a system to test each link**.”

---

## 第 5 页 我们搭了一个小 Ever · 1:00

*屏幕一开始只有标题和副标题：“Not Ever’s real system — a small, honest replica of its pipeline, trained from scratch.”*

> “**We built a mini-Ever.** It’s **not Ever’s real system — a small, honest replica of its pipeline, trained from scratch.**”

▶ **点击 1**（左边：流程图）
> “It has **one thousand celebrities**, **six hundred of them app users** — and about **forty percent of each person’s photos were uploaded by friends**. Remember that number.
>
> Like a real company, there’s a **main model**, and four **downstream copies**: a **face gallery**, a **phone copy**, a **distilled student** model, and an **old checkpoint**.
>
> **Twenty users ask to be deleted. We delete them, then check every box.**”

▶ **点击 2**（右边：指标卡片）
> “To check, we need **a metric**. We call it **leakage**, in three steps.
> **One: score** each deleted person — how well does the system match a new photo of them to them?
> **Two: repeat** that on a **reference model trained without them** — a model that **never saw them**.
> **Three: compare all pairs.** **AUC** is how often the deleted system scores higher.
>
> **Leakage equals two AUC minus one.** **Zero** is a **coin flip** — forgotten. **One** means it’s **always recognised**.
>
> A copy **passes** only if its **whole 90% interval** stays **below 0.1** — a threshold **fixed in advance**. And the **system** is scored by **its worst copy**, because that’s where an attacker looks.”

▶ **点击 3**（底部两行）
> “So **the test is not ‘can it still recognise them?’ — it is ‘does it act like it never met them?’** And to be clear: **small model, celebrity photos, twenty people per test — it shows where the structure breaks, not how Ever would have scored.**”

---

## 第 6 页 T：照片去哪了 · 1:00

*屏幕一开始只有标题 “T · Where Did the Photos Go?”*

> “First link: **where did the photos go?**”

▶ **点击 1**（数据链）
> “**User photos** train the **main model**, and the main model produces **downstream copies** — the **face gallery** of **embeddings**, the **phone copy**, the **student**, the **old checkpoint**. The FTC labels match: **§III.A** photos, **§III.B** embeddings, **§III.C** models.
>
> **Ever promised only this** — the photos — **and didn’t keep it.** But **the influence lives on** in everything to the right — **for Ever, all the way to Paravision’s customers.**”

▶ **点击 2**（左图：只删照片）
> “So **we deleted only their photos**. The **photo store**: zero. But the **face gallery**: **one point zero** — every person still found. The **main model**, **phone copy** and **old checkpoint**: about **zero point four six** each — still clearly remembered. Only the **distilled student**, taught without them, is near zero.”

▶ **点击 3**（右图：删本人账户并重训）
> “Then we did what a careful company would do: **delete their own uploads, then retrain** from scratch. Leakage dropped from **0.46** to **0.16** — but not to zero. **About a third of the memory remains — friends uploaded photos of them too.**”

▶ **点击 4**（关键句）
> “**Deleting an account is not forgetting a person.**”

---

## 第 7 页 D：概念 · 0:35

*屏幕一开始：标题 “D · Can Ever Take It Out?”，副标题：“The idea: SISA (Bourtoule et al., 2021)…”*

> “Second link: suppose Ever found everything. **Can Ever take it out?**”

▶ **点击 1**（左卡）
> “With **one model for everyone** — **all users’ photos, one model** — to **forget some users** you must **retrain everything, or take a shortcut**.”

▶ **点击 2**（右卡）
> “The design idea, **SISA**, is to **split into shards** — here, **ten**. If the users to forget are in shards **three and seven**, you **retrain shards three and seven only**.”

▶ **点击 3**（取舍）
> “But each shard sees less data. So there’s a trade-off: **recognition accuracy** against **cheap to forget**.”

▶ **点击 4**（过渡框 + 关键句）
> “**Design sets the ceiling. Method decides whether you reach it.** Ever’s real architecture isn’t public — **so we ran it: one big model versus one to sixteen shards.**”

---

## 第 8 页 D：实测 · 0:45

*屏幕一开始：标题 “D · We Ran It: Shards vs. One Model”，副标题：“20 deletion requests arriving one by one…”*

> “**Twenty deletion requests, arriving one by one.**”

▶ **点击 1**（左图：GPU 秒数）
> “The dark line is **retraining the model only**: from **sixty-five seconds** down to **eight** with sixteen shards. But a real deletion must rebuild the **whole chain** — **model, student, gallery, phone copy** — that’s the red line. It falls, then climbs back to **one hundred sixty-seven seconds**. **For comparison, one big model: one hundred eighty-six.**”

▶ **点击 2**（右图：准确率）
> “And **recognition accuracy** falls from **forty-three percent** with one shard to **twenty-five** with sixteen. So: **eight times cheaper to retrain the model — but forty-three to twenty-five percent accuracy, and the whole chain costs about the same.**”

▶ **点击 3**（关键句）
> “**Design sets the ceiling — and the ceiling has a price.**”

---

## 第 9 页 M：证明的标准 · 0:30

*屏幕一开始：标题 “M · Can Ever Prove It’s Gone?”*

> “Last link: **can Ever prove it’s gone?** First, what does ‘proved’ mean?”

▶ **点击 1**（标准卡片）
> “**The standard**, from **Guo and colleagues**: **match a model that never saw the data.** A model that **saw the photos, then unlearned**, should behave like one that **never saw the photos**. **Not ‘can it still recognise them?’ — face models recognise strangers too.**”

▶ **点击 2**（关键句）
> “**The benchmark is not silence. It’s the never-trained model.**”

▶ **点击 3**（过渡框）
> “**So we tested faces: six methods, five tests.**”

---

## 第 10 页 M：实测 · 1:00

*屏幕一开始：标题 “M · We Ran It: Six Methods, Five Tests”，副标题：“…every test compared with a model that never saw these people.”*

▶ **点击 1**（表格）
> “**Three types** of method. A **shortcut** that only changes **outputs**; three **approximate** methods that **edit the weights**; and two **exact** ones that **retrain without them**. Each faces **five tests**, from **‘says the name?’** to **‘marker fires?’**
>
> Look at the dark cells. **Hide the names** **passed** the first test, **L1** — and nothing else. **NegGrad+** and **SCRUB** **passed** only the last, **L5**: they erased a **hidden marker** we had planted. **Fine-tune** passed **none**. Each of these **passes one test — looks deleted, but isn’t.** Only **full retrain** passed **five out of five**.”

▶ **点击 2**（左下两个数字 + 右侧成本 + 深色框）
> “How far from deleted? **Filter switched off: the weights still name** [停一拍] **seventy-four percent** of them. **NegGrad+ and SCRUB still name sixty-two to sixty-four percent — marker gone.** And **retraining** costs **under twice as much**.
>
> **One passed test is not proof.**”

▶ **点击 3**（关键句）
> “**A changed output is not a changed model.**”

---

## 交棒（B → A）

> **B**：“So Ever couldn’t trace, couldn’t cheaply isolate, and couldn’t prove.”
>
> **A**：“So what did the regulator actually do — and what happened to Ever?”

*（这是唯一不在屏幕上的一句，是过渡，可以说。）*

---

## 排练提示

- **先点，再说。** 每次点击后停半拍，让观众先看到，再开口。
- **数字说慢一点**：0.46、0.16、74%、43 → 25，这几个是全场最重要的数。
- **指着说**：第 6 页指红色那根 1.00；第 10 页指两个深色格，再指 “1 / 5”。
- **超时先砍**：第 8 页“For comparison, one big model…”那句（约 5 秒）；第 5 页指标三步可以合成一句（约 10 秒）。
- **被问到细节**：翻附录，A2 指标、A4–A5 实验 1、A6 实验 2、A7–A8 实验 3。
