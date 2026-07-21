# Benchmark design

Why the experiment is shaped the way it is. Primary source: `resources/specs/Project Idea.md`, with the evaluation gate detailed in `resources/specs/Guardrails.md` §4 and the schedule in `resources/specs/Phase Plan.md`.

## The three paradigms

The study compares three retrieval architectures over SEC 10-K filings (`Project Idea.md` §6):

| | Pipeline | Mechanism | Implementation |
|---|---|---|---|
| **P1** | Vector RAG — retrieval by *meaning* | Dense embeddings plus a cross-encoder re-ranker | `bge-small-en-v1.5` + `bge-reranker-base`, ChromaDB, all local CPU |
| **P2** | Keyword RAG — retrieval by *exact words* | Okapi BM25 over tokenised nodes | `rank_bm25`, local, no LLM at any point |
| **P3** | Structural RAG — retrieval by *summary-tree traversal* | Hierarchical `SummaryIndex` over parent summaries | LlamaIndex, one-time LLM build, local retrieval |

The sharpest contrast is **semantic versus statistical** — meaning against exact words. P3 is included as a third in-scope architecture specifically to test whether summary-tree retrieval can compete on financial data *despite* its known weakness: summarisation drops cell values, footnotes, and narrow row variables, so P3 is expected to degrade badly on table-heavy queries. That expected failure is the point, and it is documented rather than hidden.

Three further pipelines (P4 brute-force full-context, P5 naive vector, P6 hybrid fusion) are documented and deliberately reserved as future scope. No modules exist for them.

### Two design decisions that protect the comparison

Both are worth understanding before changing anything about P1 or P2:

- **P1 has no metadata pre-filter.** An earlier draft narrowed vector search to a target Item before retrieval. It was dropped, because deciding the section at query time risks deriving it from the answer key, and BM25 has no equivalent step — it would compare "vector plus a head start" against "raw BM25" rather than paradigm against paradigm.
- **P2 may never use LlamaIndex's `KeywordTableIndex`.** That index calls an LLM to extract keywords, which makes it neither statistical nor deterministic and would collapse the whole semantic-versus-statistical contrast. `rank_bm25` only. Its regex tokenizer is custom and decisive: it preserves numbers, decimals, `%`, and currency tokens, strips table-markdown pipes while keeping cell values, applies no stemming, and must be byte-identical at index time and query time.

## The 140-query dataset

Evaluation rests on 140 queries split into **three completely disjoint sets**, each in its own SQLite table (`Project Idea.md` §3):

| Set | Count | Table | Role |
|---|---|---|---|
| **PQ** — Pipeline Queries | 100 (25/quadrant) | `queries` | The test set. What the pipelines are benchmarked on. |
| **GQ** — Golden Queries | 20 (5/quadrant) | `golden_queries` | The teaching set. Carries human "why this answer is good" notes and scores; injected as few-shot exemplars into the judge's prompt. Never seen by the pipelines. |
| **JEQ** — Judge Evaluation Queries | 20 (5/quadrant) | `judge_validation` | The validation set. Used only to test the judge. Never injected into any prompt. |

Disjointness is machine-learning hygiene: the data that *teaches* the judge must not contaminate the data that *tests* it, and both must stay separate from the data the pipelines are *benchmarked* on. SQLite cannot express "no primary key may repeat across three named tables" declaratively, so this is enforced at write time in `dataset_gen/split_and_label.py`.

### The four quadrants

Every set is stratified across four query types, so each paradigm's strengths and failure modes are exposed by kind rather than averaged away:

|  | Text-heavy context | Table-heavy context |
|---|---|---|
| **Direct / explicit** | **Q1** Direct Text — fact retrieval from dense prose | **Q3** Direct Table — strict cell/value extraction |
| **Implicit / synthesis** | **Q2** Implicit Text — multi-hop inference across pages | **Q4** Implicit Table — cross-row and footnote calculation |

The quadrant is not just a reporting dimension. It drives the judge's few-shot routing, and it decides whether Exact Match applies at all (Q1/Q3 only).

### How queries get made: generator versus critic

Authoring 140 ground-truth queries by hand is not feasible solo, so they are generated — but with an adversarial check strong enough to be academically defensible (`Project Idea.md` §4):

1. **Generator** (`openai/gpt-oss-120b`) reads one parsed section at a time, because open models cap at roughly 128K tokens and a full 10-K does not fit. It emits a query, a ground-truth answer, and `gt_citations` as node IDs.
2. **Critic** (`Qwen3-32b`, a deliberately different model family) receives *only* the query text. The answer and citations are redacted. It is given a search tool over **all** nodes of the filing, not just the section the generator saw — searching the whole filing is what makes the verification independent.
3. **Cross-check** is deterministic code, not an LLM judgement: compare the critic's cited nodes and value against the generator's ground truth. Agreement auto-verifies; mismatch discards and regenerates.

Different families matter here. Agreement between two independent architectures is much stronger evidence than a model agreeing with itself.

## Evaluation: three pillars

Every run is audited across three independent pillars (`Project Idea.md` §7). All retrieval metrics operate on node IDs, which is what makes them well-defined and bounded.

**Pillar 1 — Retrieval (deterministic, code only).** Precision@K, Recall@K over distinct ground-truth nodes, and Evidence Hit Rate (a binary flag: did the critical ground-truth node appear anywhere in the retrieved bundle?).

**Pillar 2 — Answer quality.**
- *LLM-as-a-judge, 1–10 — primary.* Scores semantic correctness against the stored ground truth, which is the only thing that handles the long multi-phrased answers in Q2/Q4.
- *Token-level F1 — secondary.* Reported throughout, never primary.
- *Exact Match — Q1/Q3 only.* With numeric normalisation, so `$394.3B` equals `394,300 million`, compared within a tolerance rather than as raw strings.
- *Citation Audit — deterministic code.* Checks whether the output's cited node IDs are a subset of the query's `gt_citations`. This is computed in code, not asked of the judge, because LLMs are unreliable at comparing ID strings.

**Pillar 3 — Efficiency.** Latency per query, token consumption, and one-time index-build cost (wall-clock, plus tokens for P3's LLM-built summary tree). A research metric, not a financial one.

### The coincidental-correctness trap

The Citation Audit exists for one specific failure that every other metric misses. Ask for FY2025 R&D spend (truly $150M, in node `n0451`); retrieval faults and pulls `n0120`, an unrelated marketing table that happens to list a $150M lease expense; the model reads `n0120` and answers "$150M". Token-F1 and Exact Match both score it perfect, while retrieval in fact failed completely. Comparing cited node IDs against `gt_citations` is what exposes it, and the score is programmatically downgraded on mismatch.

## The judge-validation gate

The single most important control in the project (`Guardrails.md` §4b, `Project Idea.md` §5). Teaching a judge is not the same as proving the teaching worked, so the judge is certified before it is trusted at scale:

1. Run the 20 JEQ through P1, P2, and P3 at a **single K = 5** → 60 outputs.
2. The researcher hand-scores all 60 on the 1–10 rubric.
3. The judge scores the same 60, blind to the human scores.
4. Compute the human–judge Agreement Rate across the 60.
5. **The 900-run benchmark may begin only once agreement exceeds 80%.** If it fails, change the rubric or swap the judge model (to `gpt-oss-120b`, still a different family from the Llama answerer) and repeat.

This is a hard gate, and it is cheap by design — 60 outputs, run before the expensive 900-run matrix, so a broken judge can never silently grade the whole thing.

**Dynamic few-shot routing** makes the judge affordable: rather than one static prompt holding all 20 GQ exemplars (which mixes table-grading and text-grading examples and bloats every call), the judge reads the target query's quadrant and injects exactly the 5 exemplars matching it. That yields four cacheable prompt prefixes, one per quadrant, and cached tokens do not count against Groq's limits.

## Scale and honesty

The full matrix is 100 PQ × 3 pipelines × K ∈ {3, 5, 10} = **900 runs**, each judged once, plus the 60-output gate: 960 rows in `results`.

All calls run at `temperature = 0` and **each cell runs exactly once**. Repeated sampling at temperature 0 would multiply token cost to learn almost nothing. Any robustness repeats are confined to the JEQ subset.

`Project Idea.md` §9 is explicit that this is a pragmatic reliability check appropriate to an M.Sc., not a strong statistical proof of judge accuracy — a single temperature-0 run per cell, and one ~80% agreement pass over 60 samples. The write-up is required to frame it that way.

## Where this connects

- Which model runs each stage, and why the families must differ: [System architecture](system-architecture.md#model-routing)
- The tables these query sets live in: [System architecture](system-architecture.md#the-five-table-schema)
- The rules that make the above binding rather than advisory: [Working in this repo](working-in-this-repo.md)
