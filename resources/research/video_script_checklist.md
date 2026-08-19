# 10-Min Project Video — Shooting Checklist

**Purpose:** strictly academic dissertation progress video. Broad concept coverage, shallow depth
per concept. Not an audience-facing explainer.

**Time budget:** main body 470s (7:50) + FAQ 90s (1:30) = **560s stated (9:20)**, leaving ~40s
delivery slack under 10:00. These are estimates. Do a timed read-through before filming and write
the measured figure here: `measured read-through: ____`

**Numbers re-verified 2026-08-19 (second pass)** against `benchmark.db`, `project/` and a live
`pytest` run. **Phase 4 dataset generation is now COMPLETE: 140/140.** Where the deep-audit doc and
the live DB disagree, the live DB wins. The figures below are now stable — the only number still
capable of moving before filming is `results`, which is at 0.

**Screen material:** 13 `.drawio` diagrams in `resources/assets/diagrams/` (all rebuilt 19 Aug 2026 on the
Tailwind-500 flat palette in `00-PALETTE.md`), the HTML deck for title/close only, live VSCode editor +
terminal.

**Every section carries a "Why this way" question.** These are the intrinsic, abstract points a
marker will probe. Each is worth more marks than any implementation detail in the same section —
if a section runs long, cut the *detail* bullets and keep the *why*.

---

## 1. Research question and why 10-Ks are hard (0:00 – 0:30, 30s)

**Concepts**
- Three retrieval paradigms compared head to head: semantic (vector), statistical (BM25),
  structural (summary tree)
- Domain: SEC 10-K annual financial filings
- Why 10-Ks are a hard target: dense numeric tables mixed into narrative prose, no reliable page
  anchors, answers often require joining a table cell to a sentence elsewhere
- Framed as an open question, not a preview of an answer — no results exist yet

> **Why this way — "Why compare paradigms at all, instead of just building the best possible RAG
> system?"**
> A tuned hybrid system produces a number that transfers to nobody else's problem. Isolating one
> paradigm per arm produces a finding about *when each approach is the right choice*, which is
> reusable. The goal is a comparative result, not a leaderboard entry.

**Say:** "This project asks which retrieval paradigm works best on SEC 10-K filings, and more
usefully, where each one breaks down. I compare paradigms rather than tune one system, because a
tuned system gives a number and a comparison gives a reason."

**Show:** HTML deck title slide + research-question slide. No diagram — stay on camera.

---

## 2. System overview and end-to-end data flow (0:30 – 1:10, 40s)

**Concepts**
- One flow, left to right: SEC EDGAR → LlamaParse → 26,050 `TextNode`s → three separate index
  builds → query → top-K retrieval → shared Answerer → `results` row → Judge → metrics
- Every pipeline shares the same corpus, the same Answerer, and the same Judge. Only the
  retrieval step differs
- `node_id` is the canonical evidence anchor; ground-truth citations point at node IDs, not page
  numbers, because parsed filings have no trustworthy pagination
- Anti-leakage: a pipeline receives the query and its own retrieved nodes, nothing else

> **Why this way — "Why is everything downstream of retrieval held constant?"**
> Retrieval is the independent variable. If the answering model or the judge also varied per arm,
> a difference in the final score could not be attributed to retrieval at all — the experiment
> would measure the wrong thing. Same corpus, same Answerer, same Judge, one variable.

**Say:** "Only the retrieval step changes between arms. Everything downstream is held constant,
which is the whole reason a score difference can be attributed to the paradigm."

**Show:** `01-high-level-overview.drawio` — the single most important figure in the video. Trace it left to
right with the cursor: EDGAR → LlamaParse → 26,050 nodes → three coloured arms → the one shared teal
Answerer band → `results` → Judge. The colour of each arm (P1 sky, P2 emerald, P3 violet) is reused in
every later diagram, so name the colours once here.

---

## 3. Corpus and ingestion (1:10 – 1:40, 30s)

**Concepts**
- **13 filings, 5 companies** — AAPL, MSFT, TSLA (FY2023–2025) and JPM, JNJ (FY2023–2024)
- Fetched from SEC EDGAR, parsed with LlamaParse in atomic table-extraction mode
- Nodes carry structural metadata: section header, node type (text vs table), source page
- 26,050 nodes ingested, all 13 filings complete

> **Why this way — "Why was the 10-K dataset used?"**
> Four reasons, in order of importance:
> 1. **Structural standardisation.** Every US filer submits the same form with the same numbered
>    items, so a question template transfers across companies and years. Cross-company comparison
>    is apples to apples by construction.
> 2. **The text/table mix is the actual research problem.** 10-Ks put audited numeric tables
>    directly beside narrative discussion — exactly the case where semantic and statistical
>    retrieval should diverge. A pure-prose corpus would not separate the paradigms.
> 3. **Verifiable ground truth.** The figures are audited and legally binding, so a generated
>    answer is objectively right or wrong. No annotator opinion needed.
> 4. **Free, public, licence-clean.** SEC EDGAR is a public API with no paywall or redistribution
>    restriction, which matters for a $0-infrastructure project and for reproducibility by anyone
>    marking it.
> Also worth one clause: two of the five are financials (JPM, JNJ is pharma), so the corpus is not
> monoculture tech.

**Say:** "The corpus is thirteen filings across five companies — exactly thirteen." Then the
four-reason answer, compressed to two sentences: standardised structure, and the table-plus-prose
mix is the thing being studied.

**Show:** `02-ingestion-parsing.drawio` — the five-step chain on the left, then point at the corpus grid on
the right while saying "thirteen": the grid *is* the count, 3+3+3+2+2. The four "why 10-Ks" cards under it
are the answer to the question below. Then a pre-run terminal `sqlite3` count on `nodes`.

> Say the exact filing count out loud. Direct fix for the professor's "vague count" note — do not
> paraphrase it as "around a dozen".

---

## 4. The three pipelines and how they differ (1:40 – 2:55, 75s) — CORE, PROTECT

**Concepts**
- **P1 Vector (semantic):** `bge-small-en-v1.5` embeddings in Chroma, `bge-reranker-base`
  cross-encoder rerank. Matches on *meaning*
- **P2 BM25 (statistical):** `rank_bm25` Okapi, custom regex tokenizer preserving numbers,
  percentages and currency symbols, no stemming. Matches on *exact tokens*. No LLM in this arm
- **P3 Structural:** LlamaIndex `TreeIndex`, built once by an LLM into a hierarchy of summaries,
  traversed at query time with `MockLLM` bound so retrieval makes zero LLM calls. Matches on
  *document structure*
- Every stated weakness is a hypothesis. Say the word *expected* each time

> **Why this way — "What do you actually know about the three pipelines, mechanically?"**
> Answer along three axes, one sentence per pipeline per axis:
> - **What it indexes.** P1: dense float vectors of chunk meaning. P2: a sparse term-frequency
>   table over literal tokens. P3: a tree of LLM-written summaries sitting above the raw nodes.
> - **What it matches on.** P1: cosine proximity in embedding space, then cross-encoder rerank.
>   P2: Okapi BM25 term overlap weighted by rarity and document length. P3: top-down traversal,
>   choosing a branch by summary relevance, never scanning all leaves.
> - **Where each is expected to break.** P1: near-identical phrasing across fiscal years, where
>   meaning barely differs but the answer does — "revenue increased" reads the same in FY23 and
>   FY24. P2: paraphrase and implicit questions, where the answer never shares a token with the
>   question. P3: tables, because summarisation flattens a numeric grid into prose and the
>   specific cell stops being retrievable.
> The honest form of this: I know their *mechanisms* precisely and their *rankings* not at all.
> The predictions above are the hypotheses the benchmark exists to falsify.

**Say:** One sentence per pipeline on indexing and matching, then the three expected failure
modes, then the closing line: "I know the mechanisms; the ranking is what has to be measured."

**Show:** `08-paradigm-comparison.drawio` first — it is built as exactly the three rows you are speaking
(what it indexes / what it matches on / where it is expected to break), so read down the columns. Then
`06-pipeline-registry.drawio` for two seconds to show these are real modules, not concepts.

---

## 5. Dataset generation — adversarial Generator and Critic (2:55 – 3:40, 45s)

**Concepts**
- 140 questions, **three disjoint sets**: PQ 100 (the benchmark), GQ 20 (teaches the judge), JEQ
  20 (validates the judge). No question crosses sets
- **Four quadrants**: direct-text, implicit-text, direct-table, implicit-table. Grouped by
  quadrant, not by company, so difficulty is balanced
- Adversarial loop: a **Generator** writes question, answer and node-ID citations; a **Critic**
  from a different model family independently re-verifies with a search tool
- **Anti-self-grading invariant:** Generator ≠ Critic family, Answerer ≠ Judge family
- Models: Generator `nvidia/nemotron-3-super-120b-a12b:free`, Critic `openai/gpt-oss-20b:free`
- **Dataset is COMPLETE: PQ 100/100, GQ 20/20, JEQ 20/20 = 140/140.** Finished, not in progress

> **Why this way — "Why generate the benchmark with LLMs instead of hand-writing the questions?"**
> Two reasons. **Scale with citation precision:** 140 questions each needing exact node-ID
> evidence across 26,050 nodes is not hand-producible at consistent quality by one person in the
> time available. **Reproducibility:** a documented Generator-plus-Critic protocol at
> `temperature=0` can be re-run and audited by a third party; one researcher's private judgement
> cannot. The Critic exists precisely because a single generating model would otherwise be both
> author and validator of its own benchmark — the same self-grading problem the Answerer/Judge
> split solves later in the pipeline.

**Say:** "Questions are not hand-written. One model generates with citations, a model from a
different family independently verifies, and only what survives both goes in — that makes the
dataset auditable rather than a matter of my own judgement."

**Show:** `03-three-query-sets.drawio` (the 100/20/20 counts are printed on it) →
`04-four-quadrants.drawio` → `05-adversarial-generation.drawio`. On the last one, follow the red dashed
return edge with the cursor — that loop is the adversarial part, and it reads instantly on screen. The
green DATASET COMPLETE panel on the right carries the 140/140 count.

---

## 6. Evaluation — tri-pillar metrics and the judge gate (3:40 – 4:20, 40s)

**Concepts**
- **Retrieval quality:** `precision_at_k`, `recall_at_k` against ground-truth node IDs.
  Deterministic, no LLM
- **Answer quality:** LLM-as-judge 1–10, plus `token_f1`, `exact_match`, and a `citation_audit`
  checking whether the answer cited the nodes actually holding the evidence
- **Efficiency:** latency and token cost per query
- **Judge validation gate:** judge scores 20 JEQ × 3 pipelines = 60 outputs against human scores,
  must clear **>80% agreement** before grading anything that counts
- Code: `project/judge/metrics.py`, `project/judge/async_judge.py`

> **Why this way — "Why validate the judge before trusting it, and why a citation audit on top of
> a score?"**
> The LLM judge is a measuring instrument. An unvalidated instrument makes every downstream number
> unfalsifiable — a marker cannot distinguish a real pipeline difference from judge noise. The
> >80% gate is what converts the judge from an assumption into a calibrated instrument, and it
> deliberately runs *before* the expensive 900-run batch rather than after.
> The citation audit exists because an answer can be **coincidentally correct**: the model knows
> Apple's revenue from pre-training and answers correctly while retrieving nothing relevant. Score
> alone would credit the retrieval arm for the language model's memory. The audit separates
> genuine retrieval from lucky generation, which is essential when the thing being compared *is*
> retrieval.

**Say:** Three pillars in one breath, then the judge gate, then the coincidental-correctness point
— that last one is the highest-value sentence in the section.

**Show:** `07-evaluation-phases.drawio` — Phase A on the left, Phase B on the right, the red `agreement >
80 %` box in the middle of the left column. Say the gate sentence while the cursor is on that red box. Then
`project/judge/metrics.py` briefly.

---

## 7. Backend, database, APIs and rate limits (4:20 – 4:55, 35s)

**Concepts**
- Python, SQLite in WAL mode, five tables, async workers throughout
- **Resumability:** `results.UNIQUE(source_set, query_id, pipeline, k_value)` — a crash never
  re-spends free-tier quota and the run resumes exactly where it stopped
- Determinism: `temperature = 0` everywhere, each cell runs exactly once, no repeated sampling
- `LOCAL_TEST_THROTTLE` — every loop script hard-caps at 3 rows and must run clean at throttle
  before release to a full batch
- No per-hour infrastructure anywhere; indexing and retrieval run locally on CPU

> **Why this way — "How are the APIs and rate limits handled?"**
> Five layers, all of which had to exist before any long run was attempted:
> 1. **Per-provider clients** (`groq_client`, `nim_client`, `openrouter_client`) behind one
>    `LLMFactory`, so a stage can be re-routed to a different provider by config, not by rewrite —
>    which is exactly what happened three times.
> 2. **Rate throttling at the client**: 40 RPM enforced in `nim_client.py`, 20 RPM in
>    `openrouter_client.py`, matched to each provider's published ceiling.
> 3. **Concurrency caps** separate from RPM: `GROQ_MAX_CONCURRENCY=5`, `NIM=5`, `OPENROUTER=5`
>    bound simultaneous in-flight calls, because RPM and parallelism are independent failure axes.
> 4. **Retry with backoff on real API errors**, catching the provider's own exception classes —
>    an early bug caught the wrong class and crashed whole runs instead of retrying.
> 5. **Resumability as the actual rate-limit strategy.** The daily token cap cannot be negotiated
>    with, so the design absorbs it: hit the cap, stop, resume tomorrow, lose nothing. The
>    `UNIQUE` key is what makes that safe.
> The binding constraint is tokens-per-day, not requests-per-minute — the Answerer's ~100K TPD
> ceiling on Groq is what sets the multi-week timeline.

**Say:** Lead with the layering, land on the last point: rate limits are absorbed by resumability
rather than fought, because on a free tier the limit is not negotiable.

**Show:** `10-provider-routing.drawio` for the five-stage → three-provider fan-out and the five numbered
defence layers — this diagram *is* the answer to the question above, so leave it up for the whole answer.
Then `09-database-schema.drawio`, landing on the red `UNIQUE` band at the bottom. Then
`project/loop_executor.py` (point at the `UNIQUE` comment and `K_VALUES`).

---

## 8. Code walkthrough and test suite (4:55 – 5:35, 40s)

**Concepts**
- Layout: `ingest/`, `dataset_generation/`, `pipelines/{vector,bm25,structural}/`, `judge/`,
  `llm_client/`, `tests/`
- Open exactly one real file and glance; do not explain internals
- **339 passing, 2 live-API smoke tests deselected by default, 341 collected**
- Coverage spans Phases 1–6: infra, ingestion, tree build, dataset generation, all three
  retrievers, the answerer's citation parsing and anti-leakage guarantees, loop-executor
  resumability, judge metrics
- Nothing for Phases 7–8 because those modules do not exist yet — a build gap, not a testing gap

> **Why this way — "Why this much testing on a research project rather than a product?"**
> Because the experiment's *validity* lives in code invariants, not just its correctness. Three
> things must be true for the comparison to mean anything: the three query sets stay disjoint, no
> pipeline sees ground truth or answer-location hints, and no model grades its own family's
> output. Those are not properties I can assert in the write-up and hope for — they are properties
> a test either enforces on every run or does not. A silent regression in any of them invalidates
> the results without failing anything visibly. The test suite is the methodology, expressed
> executably.

**Say:** State the number plainly — 339 passing — then the invariants point. No apology, no
over-claiming.

**Show:** VSCode file tree briefly → `project/pipelines/bm25/p2_bm25.py` → **pre-recorded** pytest
output.

> **Do NOT run pytest live and unedited.** Measured 49.7s wall clock, which alone blows this
> section. Pre-record or cut in editing.
>
> **Run it from `project/`, not from the repo root.** Two dataset-generation tests resolve
> `data/filings_manifest.json` relative to the working directory, so from the repo root they fail and
> you get two red lines on camera. `cd project && uv run pytest -q -m "not live"` gives the clean 339.

---

## 9. Research decisions, pivots, and the bugs that forced them (5:35 – 6:25, 50s) — PROTECT

**Concepts**
- **P2 held to pure `rank_bm25` on purpose.** LlamaIndex's `KeywordTableIndex` was rejected
  because it calls an LLM internally, which would have destroyed the semantic-vs-statistical
  contrast the study rests on
- **P3 moved from `SummaryIndex` to `TreeIndex`** — a flat summary index gave no real structural
  traversal, so the paradigm was not actually being represented
- **Corpus trimmed 18 → 13 filings.** Only 13 had summary trees built when dataset generation was
  ready; five more LLM tree builds bought no research benefit. A deliberate cut, not drift
- **One provider became three, forced by real quota walls:** Groq could not sustain the P3 build →
  added NVIDIA NIM; Groq's TPM ceiling structurally rejected any filing section over ~8K tokens
  for the Generator → moved to OpenRouter; the Critic then hit Groq's daily token cap as the last
  stage there → also moved to OpenRouter
- **Two methodology-relevant bugs**, one sentence each: structural metadata was leaking into P1's
  embedded text, which would have handed the vector arm an unfair advantage over BM25 — caught in
  review before any benchmark ran; and the dataset orchestrator was silently seeing only 9 of 13
  filings because of a hardcoded list, excluding JPM and JNJ with no error
- **27 deviations documented**, each with reasoning

> **Why this way — "Why document 27 deviations rather than quietly updating the proposal?"**
> Because several of them *are* findings. "A three-provider fallback chain was necessary to run a
> 900-cell LLM benchmark on free tiers" is a reproducibility result about the infrastructure
> available to an unfunded researcher — it belongs in the dissertation, not in a git history. The
> same holds for the bugs: the P1 metadata leak is evidence that in a controlled retrieval
> comparison, fairness is not a property of good intentions but something that has to be actively
> defended in code and can silently fail. Rewriting the proposal to match the outcome would delete
> exactly the part a marker should be able to audit.

**Say:** The P2 decision and the provider chain as the two worked examples, the two bugs in one
sentence each, then the deviations-as-findings framing. Do not read deviation or bug numbers
aloud.

**Show:** `11-pivot-timeline.drawio` — seven dated events on one axis, colour-coded by kind (violet model,
indigo provider, amber scope, red methodology). Point at the two red/amber cards for the bug sentences, and
at the two cards underneath for the "why published" framing.

---

## 10. Timeline — done, now, blockers, slowest operations (6:25 – 7:05, 40s)

**Concepts**
- **Done:** Phases 1–4 (infra, ingestion, P3 tree build for all 13 filings, and the full
  140-question dataset — finished as of today)
- **Code complete, zero real runs:** Phases 5 and 6 — all three retrievers, answerer, loop
  executor, judge and validation gate exist and are unit-tested, never touched real data
- **Not started:** Phase 7 (benchmark executor, planned only), Phase 8 (analysis)
- **Current blocker, plainly:** `results` is at 0 rows. Nothing has been through retrieve →
  answer → store yet. With the dataset now complete, nothing external is blocking it — the judge gate
  and the first benchmark run are both ready to start
- **Most time-consuming operations, both quota-bound not compute-bound:**
  1. P3 summary-tree build — longest wall-clock phase, 1.73M input / 0.97M output tokens across
     13 filings, throttled at 40 RPM on NIM, run resumably over multiple sittings
  2. Dataset generation — ran across days, paced entirely by free-tier daily token caps

> **Why this way — "Why is the dominant project cost wall-clock time rather than money?"**
> The $0 constraint does not remove cost, it converts it into a different currency. Every dollar
> not spent on inference becomes a day spent waiting for a daily token allowance to reset. That
> makes the schedule token-per-day-bound rather than compute-bound, and it is why resumability was
> built before the pipelines were: an operation that cannot survive being stopped halfway is
> simply not runnable under this constraint. The two slowest phases are both slow for the same
> reason — neither is CPU-limited, both are quota-limited.

**Say:** Be exact. Not "nearly done", not "just started". Dataset complete at 140/140, zero benchmark
rows executed. Then the money-becomes-time point.

**Show:** `12-phase-gantt.drawio` — ten weeks across, eight phases down, colour-coded by real status (green
complete for Phases 1–4, cyan built-but-never-run for 5–6, faded slate not started for 7–8). The cyan bars
are the point of the section: built and tested, zero live runs. Then a live `sqlite3` count showing
`results = 0`.

---

## 11. Expected results and when (7:05 – 7:30, 25s)

**Concepts**
- Target matrix: **900 runs = 3 pipelines × 3 K values (K = 3, 5, 10) × 100 PQ questions**
- Expected wall clock: roughly 2–3 weeks of intermittent free-tier running, bound by the
  Answerer's ~100K tokens/day. Not a one-evening job
- Reporting will be **per quadrant**, not one global winner — the useful finding is which paradigm
  wins on direct-table versus implicit-text, and by how much
- **No accuracy number is stated in this video, because none exists yet**

> **Why this way — "Why three K values, and what result would falsify the hypothesis?"**
> **Three K values** because retrieval depth interacts with paradigm rather than sitting
> orthogonal to it. BM25 may be sharply precise at K=3 and gain nothing from K=10, while the
> vector arm may need depth before recall becomes usable. A single K would silently pick a winner
> by choosing a favourable operating point, so K sensitivity is part of the result, not a nuisance
> parameter.
> **Falsification:** if all three paradigms score within noise across all four quadrants and all
> three K values, then paradigm choice is *not* the dominant factor for financial-document
> retrieval, and the answer to the research question is that something else — chunking, or the
> answering model — dominates. That is a publishable negative result, and the design has to be
> able to produce it.

**Say:** "Nine hundred runs is the target, not a result." Then K sensitivity, then the
falsification condition — a marker specifically looks for whether the design can fail.

**Show:** `13-benchmark-matrix.drawio` — the 3 × 3 grid, the blue `3 × 3 × 100 = 900 RESULT ROWS` band, and
the red `0 written so far` band directly beneath it. That red band is what stops this reading as a claim.

---

## 12. Next steps, future scope, close (7:30 – 7:50, 20s)

**Concepts**
- Immediate, and now unblocked: first real loop-executor run → clear the >80% judge gate → build the
  Phase 7 executor → Phase 8 analysis and plots
- Future scope: more companies and fiscal years, a hybrid P1+P2 arm, filing types beyond 10-K
- Contribution in one sentence: a disjoint-set, anti-leakage, anti-self-grading benchmark design
  for financial-document RAG, executable at effectively zero infrastructure cost

**Say:** Next steps in one breath, future scope in one, contribution in one. Sign off.

**Show:** HTML deck closing slide.

---

## 13. FAQ (7:50 – 9:20, 90s) — pick 3 or 4 while filming, ~25s each

Ten prepared questions. **Do not answer all ten** — 90s covers three or four at a comfortable
pace. Pick whichever the earlier sections left thinnest. Read the question aloud before answering
so the cut is clean in editing.

**Show throughout:** a single HTML deck slide listing the FAQ questions, or stay on camera.

1. **"Why not just use a hybrid retriever, since that is what production systems do?"**
   Because a hybrid confounds the variable. The point is to characterise each paradigm's failure
   surface; a hybrid can be assembled afterwards from that knowledge, but not the reverse. A
   hybrid arm is named as future scope.

2. **"Isn't an LLM-generated benchmark circular — LLMs writing questions for LLMs to answer?"**
   The circularity is broken in three places: the Critic is a different model family from the
   Generator, the Judge is a different family from the Answerer, and every ground-truth citation
   points at a specific `node_id` in the source filing that a human can open and check. The
   dataset is verifiable against primary documents, not against a model.

3. **"How do you know the judge is not just rewarding fluent writing?"**
   That is precisely what the >80% human-agreement gate on 60 outputs tests, and why the judge
   score sits beside deterministic metrics — `token_f1`, `exact_match`, `precision@k` — that
   fluency cannot influence. If the judge and the deterministic metrics disagree systematically,
   that disagreement is itself reportable.

4. **"Thirteen filings is a small corpus. Is that enough?"**
   The unit of statistical analysis is the query, not the filing: 100 questions × 3 pipelines ×
   3 K values = 900 observations. The corpus needs enough diversity to make questions
   non-trivial — five companies across three sectors and multiple fiscal years — not enough
   volume to stress an index. Scaling filings would raise cost without raising statistical power.

5. **"What happens if the judge fails the 80% gate?"**
   The full run does not proceed. The fallback is to revise the judge prompt using the GQ set —
   which exists for exactly that purpose and is disjoint from both the benchmark and the
   validation set — and re-test. Failing the gate is a reportable finding about LLM-as-judge
   reliability in a numeric domain, not a project failure.

6. **"Why summary trees rather than a knowledge graph for the structural arm?"**
   A summary tree matches the document's own hierarchy — a 10-K is already a numbered tree of
   items and sub-items — so the structural arm tests document structure rather than an
   extraction model's quality. A knowledge graph would introduce entity-extraction error as a
   confound and would need LLM calls at query time, breaking cost parity with P2.

7. **"How is the parsing quality controlled, given everything depends on it?"**
   A parsing audit runs over the ingested nodes, and one known defect is documented rather than
   hidden: LlamaParse merged a units caption into a column-one header on 31 tables. It was left
   unfixed deliberately because it affects all three pipelines identically — it degrades absolute
   scores slightly but not the comparison, which is what is being measured.

8. **"Is the $0 cost claim honest?"**
   Almost. There is one disclosed, non-recurring $10 credit top-up on OpenRouter, taken to raise a
   free-tier limit from 50 to 1,000 requests per day after a quota wall made the Generator stage
   unrunnable. It is documented as a deviation rather than absorbed silently. Everything else —
   all infrastructure, all indexing, all retrieval — runs locally or on free tiers, with no
   per-hour resource anywhere.

9. **"What is the biggest threat to the validity of your results?"**
   Ground-truth citation quality. If the Generator systematically cites the wrong nodes for a
   quadrant, every pipeline's `precision@k` in that quadrant is measured against the wrong
   target. The Critic cross-check and the four-quadrant balance are the mitigations; the residual
   risk is stated explicitly rather than claimed away.

10. **"What would you do differently if starting again?"**
    Build the provider abstraction on day one instead of after the first quota wall — three
    stages had to be re-routed later, and each re-route was cheap only because the abstraction
    eventually existed. Second: derive every filing list from the manifest from the start, since
    the one hardcoded list in the codebase silently excluded two companies from question
    generation for a period.

---

## Professor feedback to address explicitly on camera

- [ ] **Filing count:** say "thirteen" exactly (§3) — direct fix for the vague-count note
- [ ] **Testing (graded B, lowest section):** show 339 passing tests (§8) — the grade predates
      most of this suite
- [ ] Optional single line if it fits: literature review scope was RAG-general rather than
      finance-specific. Acknowledge, do not dwell

---

## Do NOT include

- Any accuracy, score, or "which pipeline won" claim. `results` is at 0 rows. There is nothing to
  report and claiming otherwise is the one unrecoverable error in an academic submission
- Engagement framing of any kind: no hooks, no "you won't believe", no calls to action. Strictly
  academic register
- Deviation numbers, bug numbers, or issue numbers read aloud. State the fact, not the index
- Live unedited `pytest` (56.9s) or any long-running command on camera
- `README.md`'s Status and repo-layout sections on screen — **stale**, still says the build has
  not started
- `resources/specs/Budget.md` and `Guardrails.md` model tables on screen — **stale on routing**,
  both predate the current three-provider setup
- `openwiki/quickstart.md` line 71 on screen — **stale**, still says 18 filings / 6 companies
- Flipping through all 13 diagrams. One or two per section, as mapped below — the mapping is deliberate
- Deep internals of any single file. Glance, name it, move on
- All ten FAQ answers. Three or four only

---

## Assets to prepare before filming

**Build first**
- [ ] Standalone HTML deck (later task) — now only needs: title slide, research-question slide, FAQ
      question list, closing slide. Every other slide previously listed here is now a real diagram
- [ ] Export each `.drawio` to PNG or PDF at 2x before filming — do not screen-share the draw.io editor
      itself, its chrome and grid will show

**Diagram mapping — one or two per section, do not flip through**

| § | Section | Diagram(s) |
|---|---|---|
| 1 | Research question | none — HTML deck title slide |
| 2 | System overview and data flow | `01-high-level-overview.drawio` |
| 3 | Corpus and ingestion | `02-ingestion-parsing.drawio` |
| 4 | Three paradigms (CORE) | `08-paradigm-comparison.drawio` then `06-pipeline-registry.drawio` |
| 5 | Dataset generation | `03-three-query-sets` then `04-four-quadrants` then `05-adversarial-generation` |
| 6 | Evaluation and judge gate | `07-evaluation-phases.drawio` |
| 7 | Backend, APIs, rate limits | `10-provider-routing.drawio` then `09-database-schema.drawio` |
| 8 | Code and tests | none — live editor + pre-recorded pytest |
| 9 | Decisions and pivots (PROTECT) | `11-pivot-timeline.drawio` |
| 10 | Timeline and blockers | `12-phase-gantt.drawio` |
| 11 | Expected results | `13-benchmark-matrix.drawio` |
| 12 | Next steps and close | none — HTML deck closing slide |
| 13 | FAQ | none — stay on camera |

**Diagrams carrying live numbers — all settled as of 19 Aug 2026, second pass**
- [x] `03-three-query-sets.drawio` — PQ 100/100, GQ 20/20, JEQ 20/20, dataset complete
- [x] `05-adversarial-generation.drawio` — same counts, green DATASET COMPLETE panel
- [x] `09-database-schema.drawio` — per-table row counts (26,050 / 100 / 20 / 20 / 0)
- [x] `12-phase-gantt.drawio` — Phase 4 green and complete, `results = 0` blocker band
- [ ] Only `results` can still change. If a benchmark run starts before filming, re-render `09` and `12`

**Edge labels**
- [ ] All four labelled arrows (two in `01`, two in `05`) carry a perpendicular offset so the text sits
      clear of the stroke. If you move a box in draw.io, re-check that the label did not snap back onto
      the line

**Pre-run and capture**
- [ ] `cd project && uv run pytest -q -m "not live"` — capture green output, confirms 339 passing.
      Must be run from `project/`; from the repo root two tests fail on a relative manifest path
- [ ] `sqlite3 project/benchmark.db` count query — the §5 and §10 figures are current as of the second
      pass; only `results` can still move
- [ ] Editor tabs pre-opened: `project/pipelines/bm25/p2_bm25.py`, `project/loop_executor.py`,
      `project/judge/metrics.py`, `project/llm_client/config.py`

**Diagram style contract**
- [ ] `resources/assets/diagrams/00-PALETTE.md` — Tailwind 500 only, flat, sharp corners, no borders or
      shadows, Inter for prose and JetBrains Mono for identifiers. Every concept keeps one colour across
      all 13 figures: P1 sky, P2 emerald, P3 violet, Generator indigo, Critic fuchsia, Answerer teal,
      Judge purple, metrics cyan, gates and blockers red. Read it before editing any diagram

**Cut order if the read-through runs long**
1. FAQ down to 3 questions, then 2
2. Detail bullets in §3, §7, §8 — but never the "Why this way" blocks
3. §11's falsification bullet, spoken as one clause instead of two sentences
Never cut §4 or §9.

---

## Full detail

`resources/research/project_deep_audit_2026-08-18.md` — verified section-by-section breakdown this
checklist was built from. Supporting logs: `bugs.md`, `deviations.md`, `challenges.md`,
`issues.md`, `token_usage.md`, `tests.md`.
