# CA2 video script

Matches `resources/artifacts/presentation.pptx`, eleven slides, plus a live demo between slides 8 and 9.

**Target:** 9:31, which leaves about 29 seconds of slack under the 10:00 cap.
**Pace:** the timings assume roughly 140 words a minute. If you read slower than that, cut from beats 4 and 10 rather than letting the whole thing drift.
**Measured read-through:** `____` (fill this in after your first timed run).

Everything in the `Say` blocks is written to be spoken, not read off the screen. Say it in your own words if that comes out more naturally. The numbers are the part that must stay exact.

---

## Timing card

Print this or keep it on a second monitor.

| Beat | Screen | Window | Length |
|---|---|---|---|
| 1 | Slide 1, title and ethics | 0:00 to 0:41 | 41s |
| 2 | Slide 2, motivation | 0:41 to 1:20 | 39s |
| 3 | Slide 3, question and aims | 1:20 to 1:57 | 37s |
| 4 | Slide 4, system design | 1:57 to 2:41 | 44s |
| 5 | Slide 5, three paradigms | 2:41 to 3:41 | 60s |
| 6 | Slide 6, foundations | 3:41 to 4:12 | 31s |
| 7 | Slide 7, status | 4:12 to 4:53 | 41s |
| 8 | Slide 8, handoff | 4:53 to 5:06 | 13s |
| D | **Terminal and editor** | 5:06 to 7:09 | 123s |
| 9 | Slide 9, demo findings | 7:09 to 8:25 | 76s |
| 10 | Slide 10, conclusions | 8:25 to 9:04 | 39s |
| 11 | Slide 11, next steps | 9:04 to 9:31 | 27s |

If you run long, the two places to cut are beat 4 (the diagram largely explains itself) and the code portion of beat D. Beats 5, 9 and 10 carry the marks. Protect them.

---

## Before you press record

- [ ] Open the deck in PowerPoint, presenter view on, so you can see the notes.
- [ ] Second desktop: VS Code open at `project/`, and a terminal already `cd`'d into `project`.
- [ ] Terminal tab 1: empty prompt, ready for the demo.
- [ ] Terminal tab 2: run `uv run pytest -q -m "not live"` beforehand and leave the result on screen. It takes about 43 seconds, which is too long to watch on camera.
- [ ] Set the font size in the terminal large enough to read at 1080p. Test it.
- [ ] Kill the import warning. Run the demo like this:

```bash
TRANSFORMERS_VERBOSITY=error uv run python -m demo.main
```

Without that variable the first line of output reads `None of PyTorch, TensorFlow >= 2.0, or Flax have been found`. It is harmless, the embedder uses ONNX, but it looks like a crash on camera.

- [ ] Do one dry run of the demo. It takes **about 53 seconds** end to end with the indexes already built.
- [ ] Re-check the two numbers that can move: `sqlite3 benchmark.db "select count(*) from results;"` and the pytest total.

---

## Beat 1 · Title and ethics
`0:00 → 0:41` · 41s · Slide 1

**Do:** start on the title slide, full screen. Sit still, look at the camera if you have one.

**Say:**

> Hello, I'm Ojaswi Athghara, student number 201959096. This is my second assessment for COMP702, supervised by Blaine Keetch.
>
> The project compares three ways of finding an answer inside a company's annual report. Everything after retrieval is held identical, so any difference in the scores comes from retrieval itself.
>
> First, the ethics position, which is category A zero. Every source document is a US SEC 10-K filing from EDGAR, a public regulatory archive. No personal or confidential data, and no licence needed. No human participants. I have read the ethical guidance and I follow it throughout.

**Note:** the brief asks for this declaration, so do not rush it or skip it. Roughly ten of the forty seconds belong to the ethics block.

---

## Beat 2 · Motivation
`0:41 → 1:20` · 39s · Slide 2

**Do:** advance. Let the three shape boxes sit on screen while you talk.

**Say:**

> Most retrieval systems are tested on plain prose. An annual report is not plain prose.
>
> The answer hides in three different shapes. Sometimes management states it in a sentence, and meaning-based search handles that well. Sometimes it sits in one cell of a numeric table, where summarising the table destroys the thing you need. And sometimes it spans a footnote and the table that note qualifies, so the reader has to join the two.
>
> The corpus is thirteen filings from five companies, just over eighteen thousand addressable nodes, and a hundred and forty benchmark questions.

---

## Beat 3 · Research question and aims
`1:20 → 1:57` · 37s · Slide 3

**Do:** advance. Point at the question line, then work down the three numbered aims.

**Say:**

> So, the research question. Does the structure of a document decide which retrieval paradigm wins?
>
> That stays a question. No number in this deck answers it yet.
>
> Three aims follow. First, build three pipelines that differ only in how they index. Second, generate a benchmark where every question carries verified evidence, using two language models from different families to propose and to check. Third, measure retrieval, answer quality and cost as three separate things, because a paradigm can win on accuracy and lose badly on speed.

---

## Beat 4 · System design
`1:57 → 2:41` · 44s · Slide 4

**Do:** advance to the diagram. Trace the flow with the cursor, left to right, as you speak.

**Say:**

> This is the whole system. A filing comes down from EDGAR, through a parser, and out as a list of atomic nodes in SQLite. Every node has an ID, and that ID is the evidence anchor for everything downstream. Page numbers are unreliable in these documents. Node IDs are not.
>
> The three pipelines each build their own index over those same nodes. A question goes to all three. Each returns its top K nodes. Those go to one shared answerer, the answer is written to the database, and a separate judge scores it later.
>
> One variable changes across the three arms. Retrieval.

---

## Beat 5 · The three paradigms
`2:41 → 3:41` · 60s · Slide 5 · **protect this beat**

**Do:** advance to the comparison diagram. Take the three columns in order and do not hurry.

**Say:**

> Here is what actually differs.
>
> P1 is semantic. Every node is embedded with a small BGE model, and a cross-encoder reranks the top twenty candidates before the final three are picked. It understands paraphrase, so it finds the right sentence when the question uses different words. It pays for that in latency.
>
> P2 is statistical. BM25, with no model at all. The tokeniser is custom and keeps numbers, decimals, percentages and currency symbols, because a standard one strips them, and on a document made of figures that is fatal. It is blind to paraphrase, but very strong on exact values, and it costs nothing to run.
>
> P3 is structural. A language model summarised each section, then summarised those summaries into a tree. At query time the system walks that tree from the root down. No model runs at query time.

---

## Beat 6 · Foundations
`3:41 → 4:12` · 31s · Slide 6

**Do:** advance. Three items, quick pace, then stop.

**Say:**

> Three things pinned down before anything was run.
>
> The corpus size is a counted number rather than an estimate: thirteen filings, five companies, eighteen thousand two hundred and ninety-seven nodes.
>
> The test suite covers every stage, four hundred and ninety-four tests across ingestion, all three retrieval arms, dataset generation and the judge.
>
> And the reading includes financial question answering directly, starting from FinQA by Chen and colleagues. The dissertation widens that section.

---

## Beat 7 · Status
`4:12 → 4:53` · 41s · Slide 7

**Do:** advance. Point at the green figures, then deliberately at the two red ones.

**Say:**

> Where the project stands today. Six phases are built and tested. The benchmark itself has not run.
>
> Everything in green comes from the live database. Thirteen filings ingested, a hundred and forty questions generated, four hundred and ninety-four tests passing.
>
> Two numbers are red, and they are the honest part of this slide. Twenty golden questions still need hand-labelling, and until that is done the judge cannot be validated. The results table holds zero rows because the executor has never been run. I would rather say that plainly than imply a result I do not have.

---

## Beat 8 · Handoff
`4:53 → 5:06` · 13s · Slide 8

**Do:** advance. Say the line, then switch desktop. Do not narrate the switch.

**Say:**

> That is the introduction. Now the software itself: the source code, a live comparison of all three pipelines on the same question, the database behind those numbers, and the test suite.

---

## Beat D · The live demo
`5:06 → 7:09` · 123s · Terminal and editor

Four sub-beats. Keep an eye on the clock here, this is where a video overruns.

### D1 · One file of code
`5:06 → 5:31` · 25s

**Do:** in VS Code, open `project/pipelines/bm25/tokenizer.py`. It is fourteen lines, so the whole file fits on screen with no scrolling.

**Say:**

> Start with the smallest piece that matters. This is the BM25 tokeniser. One regular expression, and it keeps currency symbols, decimals, thousands separators and percentages together as single tokens. A standard tokeniser throws all of that away. On a document made of figures, this one line decides whether the pipeline works.

**If you have spare time later,** `project/pipelines/structural/p3_structural.py` around line 45 shows the `MockLLM` bound at load, which makes a query-time call to a paid endpoint impossible. Skip it if the clock is tight; slide 5 already makes the point.

### D2 · Run it
`5:31 → 6:33` · 62s

**Do:** switch to terminal tab 1. Type the command visibly, then press enter.

```bash
TRANSFORMERS_VERBOSITY=error uv run python -m demo.main
```

**Say, while the header and the index checks print:**

> This runs one question per difficulty quadrant through all three pipelines, at K equals three. Everything here is local. No API key is read and no quota is spent, which means it produces the same numbers on every run.

**Say, as the first query block appears:**

> Each block is one question. You get the top three node IDs that each pipeline returned, a star where that node is genuinely in the ground truth, then precision, recall and the latency for that retrieval.

**Do:** when query 3 is on screen, point at it.

**Say:**

> This one asks for a figure that lives in a table. BM25 finds two of the four correct nodes, the vector arm finds one, and the structural arm finds none of them.

**Do:** let the summary block finish printing. Pause for a beat. Say nothing over it.

### D3 · The database
`6:33 → 6:51` · 18s

**Do:** run it live.

```bash
sqlite3 benchmark.db "select count(*) from results;"
```

**Say:**

> And the results table, live. Zero. That is the red number on the status slide, and this is where it comes from. Nothing in this presentation is a benchmark result, because there are none yet.

### D4 · The test suite
`6:51 → 7:09` · 18s

**Do:** switch to terminal tab 2, where pytest has already finished.

**Say:**

> The test suite, run just before recording. Four hundred and ninety-four passing, with two live-API tests deselected so nothing spends quota. It takes about a minute and a half, so I am showing you the finished output rather than making you watch it.

**Do:** switch back to the deck. Advance to slide 9.

---

## Beat 9 · What the demo showed
`7:09 → 8:25` · 76s · Slide 9 · **protect this beat**

**Do:** work down the table first, then the three findings underneath.

**Say:**

> Those are the numbers, averaged over the four questions.
>
> BM25 came out ahead here at zero point five precision. Three of the four answers sat inside tables, its home ground. The vector arm found the evidence every time but ranked it more loosely, and spent over five seconds a question on the reranker.
>
> The structural arm scored zero throughout, and it is worth being precise about why. It did not crash and it did not come back empty. It routed into the lease tables in Item 8 instead of the properties table in Item 2. Both sections talk about leases. It picked a branch near the root, on a broad summary, and a tree walk cannot go back up. That is exactly what its architecture predicts.
>
> Two more things. Not once did all three pipelines agree on the evidence. And zero point three three was the maximum possible on the single-evidence questions, because the denominator is K.
>
> Four questions on one filing shows the mechanism. The real benchmark is nine hundred runs, and it has not started.

---

## Beat 10 · Conclusions
`8:25 → 9:04` · 39s · Slide 10

**Do:** advance. Three claims, one at a time.

**Say:**

> Three claims the work supports, and none of them come from the benchmark. They come from building it.
>
> The three paradigms genuinely disagree about which evidence answers a question, and you have just watched that happen.
>
> Cost separates them as sharply as accuracy might. BM25 retrieves with no model at all, while the vector arm pays for a cross-encoder on every single query.
>
> And free-tier limits shaped the architecture, not just the timetable. The quota runs out part-way through a run, which is why there are three providers and a resumable key.

---

## Beat 11 · Next steps and close
`9:04 → 9:31` · 27s · Slide 11

**Do:** advance. Run down the five steps briskly, then slow right down for the last sentence.

**Say:**

> Five steps left. Label the twenty golden questions, clear the judge against human scoring on sixty held-out outputs, build the remaining indexes, run the nine hundred cells, and report per quadrant rather than crowning a single winner.
>
> And if the benchmark shows no difference between the three paradigms, that falsifies the hypothesis, and it is still a finding worth reporting.
>
> Thank you.

**Do:** hold on the final slide for two seconds before stopping the recording.

---

## If you are asked afterwards

Short answers, ready to go.

**Why is BM25 beating the neural model?**
> On this sample of four questions, yes. Three of them turn on exact figures pulled from tables, which is BM25's home ground. Four questions on one filing is not a result. The benchmark is nine hundred runs and it has not started.

**Why not use a larger embedding model?**
> The small BGE model runs on CPU with no API cost, which keeps retrieval reproducible on any machine. A larger model changes the constant, not the comparison. It is a sensible extension rather than a fix.

**Is thirteen filings enough?**
> It started at nine and went to thirteen for more data to work with, across five companies. The unit of analysis is the question, not the filing, and there are a hundred and forty of those spread over four difficulty types.

**How do you know P3 is not simply broken?**
> It returns different nodes for different questions, all from the correct filing, and the sections it lands on are topically next door to the right ones. It is choosing, and choosing wrong.

**Why has the benchmark not run?**
> Twenty golden questions still need hand-labelling, and that gates the judge validation. Running nine hundred cells before the judge is validated would produce numbers nobody could defend.

**What stops a model marking its own work?**
> The generator and the critic are different model families, and so are the answerer and the judge. The three query sets are disjoint, so the judge is never validated on the questions it was taught with.

---

## Do not say

- Any accuracy or win figure framed as a benchmark result. There are none.
- "Which pipeline is best." The demo covers four questions on one filing.
- Bug numbers or deviation numbers read aloud. Describe the decision instead.
- The word "just" in front of anything you built. It undersells the work.
- Apologies for the zero results. State it once, plainly, and move on.

## Do not show

- `README.md`, its status section is stale.
- `Budget.md` or `Guardrails.md` model tables, both stale on routing.
- A live `pytest` run. Forty-three seconds of watching a progress bar.
- Any terminal with the `TRANSFORMERS_VERBOSITY` warning visible.

---

## Numbers to re-verify on the morning of filming

| Number | Where it appears | How to check |
|---|---|---|
| 494 tests | Slides 6, 7, 8 and beat D4 | `uv run pytest -q -m "not live"` |
| 0 results rows | Slide 7 and beat D3 | `sqlite3 benchmark.db "select count(*) from results;"` |
| 20 labels outstanding | Slide 7 | `sqlite3 benchmark.db "select count(*) from golden_queries where human_reasoning like '%PENDING%';"` |
| Demo figures | Slide 9 | re-run the demo, the numbers are deterministic |

If a figure has moved, change the slide before filming rather than talking around it on camera.
