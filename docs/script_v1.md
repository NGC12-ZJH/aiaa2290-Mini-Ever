# Pre 逐字稿：两种分工版本（script v1）

> Source: `2290presentation讲稿.docx`. Speakers: **A** = Qingyang LI, **B** = Jinghan ZHAO. Italic lines are stage directions.

| 页 | 主题 | 讲者 | 时间 |
|---:|------|:----:|------|
| 1 | 封面 | A | 0:00–0:10 |
| 2 | 承诺 | A | 0:10–0:55 |
| 3 | 法律 | A | 0:55–1:55 |
| 4 | 三环模型 | B | 1:55–3:15 |
| 5 | T | B | 3:15–4:20 |
| 6 | D | B | 4:20–5:30 |
| 7 | M | B | 5:30–6:40 |
| 8 | 判决 | A | 6:40–7:45 |
| 9 | 三个动词 | A | 7:45–8:30 |
| 10 | 最后一句 | A | 8:30–8:55 |
| 11 | Thank You | A & B | 8:55–9:05 |

---

## 第 1 页 封面 · A · 0:00–0:10

Good morning, everyone. I’m Qingyang LI, and this is Jinghan ZHAO. Today, we have one simple question: when can a company honestly say “deleted”?

## 第 2 页 承诺 · A · 0:10–0:55

*站在屏幕左侧，说到“0”时停一拍。*

Let’s start with a real story. In 2017, a photo app called Ever made a simple promise to its users: deactivate your account, and we delete your photos.

According to the US Federal Trade Commission, that promise was not kept. Until at least October 2019, Ever deleted none of those photos. It kept them indefinitely.

That part is easy to judge. It’s a broken promise.

But here is the harder question we want to explore today. Even if Ever had deleted every single photo — would that have been enough?

Hold on to that question. We’ll tell you what actually happened to Ever at the end.

## 第 3 页 法律 · A · 0:55–1:55

*依次指三张卡片，最后指下方的问号。*

Ever’s promise was not just company policy. In many places, deleting your data is a legal right.

In Europe, the GDPR gives people a right to erasure, although there are exceptions. In 2024, Europe’s data protection authorities raised a harder question for AI: if personal data can still be extracted from a model, can that model really be called anonymous?

China’s PIPL addresses another problem: when deletion is technically difficult, further processing must stop, except for storage and security.

Put these rules together, and the question is no longer just: “Did you delete the file?” It becomes: “What did the file become?”

In AI, the data may already have shaped a model. The legal obligation is clear. The technical path is not. There is no simple delete button for model parameters.

### 交接一（A 抛问题，B 接）

**A:** So what would Ever actually have needed to keep its promise?

## 第 4 页 三环模型 · B · 1:55–3:15

*全场最重要的一页。讲到哪个环就指哪个环。*

**B:** We think the answer is three links in a chain.

The first link is T, traceability. Before you can delete anything, you need to know where the data went. That’s about knowing.

The second link is D, deletability. Once you’ve found it, can you actually take its influence out — and with which method? That’s about doing.

The third link is M, measurable forgetting. After you’ve taken it out, can you prove it’s really gone? That’s about proving.

Know, do, prove. And each link depends on the one before: you can’t remove what you can’t find, and you can’t prove a removal you never made.

That’s why we write credible deletion as the minimum of T, D and M. It’s not a scoring system. It’s a simple idea: a chain is only as strong as its weakest link. If one link breaks, the whole deletion claim breaks with it.

So let’s test Ever, one link at a time.

## 第 5 页 T · B · 3:15–4:20

*沿数据链从左往右指。*

First: where did the photos go?

Here is Ever’s real data chain. User photos were turned into face embeddings — numbers that describe each face. Those became training data for a face-recognition model. And according to the FTC, that technology also helped Ever’s enterprise business, Paravision.

Notice what Ever promised to delete: only the first box. And it didn’t even do that.

But even if it had, the influence had already travelled down the chain. And research shows models can hold on to individual data. In 2021, Carlini and colleagues extracted names, phone numbers and email addresses directly from GPT-2’s training data. **[可删]** Not every example is memorized — but some are.

So the trace can’t stop at storage. It has to go into the model itself. If this link breaks, the most Ever can honestly say is: “We deleted the records we could find.”

You cannot credibly delete an influence you cannot trace.

## 第 6 页 D · B · 4:20–5:30

*先说明是推演；讲分片时指驼色的 3 和 7。*

Now suppose Ever traced everything. Can it take the influence out?

We don’t know how Ever really built its model, so this is a thought experiment.

On the left: one big model trained on everyone’s photos. To forget some users, Ever has two options — retrain everything, which is very expensive, or take a shortcut by editing the existing model.

On the right: the same data split into ten shards, each training its own small model. This idea is called SISA. If the deactivated users sit in shards 3 and 7, Ever only retrains those two.

But there’s a trade-off. Shards make forgetting cheap, but each small model sees less data. A model that is cheap to train may be expensive to forget.

If this link breaks, Ever can only say: “We can’t remove it without rebuilding.”

So: design sets the ceiling. Method decides whether you reach it.

## 第 7 页 M · B · 5:30–6:40

*先指左边的“≈”，再指右边的柱状图。说“89 percent”前停一拍。*

Without shards, Ever would probably take the shortcut. So the last question: can it prove the shortcut worked?

First, what does “proved” mean? Guo and colleagues give a clear standard: a model that saw the photos and then forgot them should behave like a model that never saw them at all. The benchmark is not silence. It’s the never-trained model.

So the obvious move is to test it. If the model no longer recognises those faces, it has forgotten them, right?

Not quite. In a study on language models, researchers made a model forget Harry Potter. Only about 13 percent of the knowledge remained. Then they compressed the model — a routine step companies take to run models on phones. The knowledge came back: about 89 percent. Nobody attacked it. Normal deployment undid the forgetting.

That study was on text, not faces. But the lesson carries over: one passed test is not proof. A changed output is not a changed model.

### 交接二（B 总结，A 接）

**B:** So Ever couldn’t trace, probably couldn’t isolate, and couldn’t prove.

**A:** So what did the regulator actually do?

## 第 8 页 判决 · A · 6:40–7:45

*说“Not just the data — the models too”时加重语气。*

In 2021, the FTC ordered Everalbum to delete three things: the photos and videos of deactivated users; the face embeddings made from users who never consented; and the face-recognition models and algorithms built with Ever users’ photos.

Not just the data — the models too. FTC Commissioner Rohit Chopra said the company had to “forfeit the fruits of its deception.”

Now, the FTC didn’t reason in our terms. And through our three-link framework, the decision suddenly makes sense. If you can’t trace the data, isolate its influence, or prove that influence is gone, deleting the whole model is the only deletion that needs no further proof.

Deletion should follow what the data became, not only where it began.

## 第 9 页 三个动词 · A · 7:45–8:30

*每个动词后停一拍。*

Which brings us back to Ever’s promise. It was just one sentence. But keeping it would have taken three things.

Trace — know where the data went.

Isolate — be able to take its influence out.

Prove — show that it’s really gone.

Trace, isolate, prove: our T, D and M. And credible deletion is only as strong as the weakest of the three.

## 第 10 页 最后一句 · A · 8:30–8:55

*放慢语速，说完停顿两秒。*

So we’ll leave you with this. Deleting a record is an operation. Forgetting a person is a claim — and a claim needs proof.

## 第 11 页 Thank You · A & B · 8:55–9:05

**A:** Thank you.

**B:** We’re happy to take your questions.
