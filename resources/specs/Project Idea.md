### COMP702 M.Sc. Dissertation Project: Comprehensive Research Concept, Benchmarking Framework, and System Design

---

## 1. Research Overview and Core Objectives

The central objective of this research is to conduct an academically rigorous, multi-dimensional comparative performance analysis of three distinct Retrieval-Augmented Generation (RAG) retrieval paradigms when executed against highly complex, structurally dense financial data — specifically, United States SEC 10-K corporate filings.

The primary research question explores the performance boundaries, accuracy limits, and efficiency trade-offs between three retrieval paradigms:

* **Semantic retrieval (vector-based)** — retrieval by meaning, via dense embeddings.
* **Statistical retrieval (keyword-based)** — retrieval by exact-word frequency, via Okapi BM25.
* **Structural retrieval (hierarchical/summary-based)** — retrieval by traversing an LLM-generated summary tree.

The sharpest contrast in the study is **semantic vs. statistical** (meaning vs. exact words); the **structural** paradigm is included as a third in-scope architecture to test whether a summary-tree approach can compete on financial data despite its known vulnerability to table fragmentation. By evaluating these paradigms across multi-layered data structures (narrative text vs. granular financial tables), this study establishes explicit boundaries regarding when vector embeddings fail, where keyword indices excel, and where hierarchical summarisation breaks down.

---

## 2. Data Strategy and Ingestion Parsing Architecture

Financial SEC 10-K filings present severe token, layout, and structural parsing obstacles. To eliminate noise and guarantee structural parity across all downstream pipelines, the ingestion framework follows a strict structural mapping mechanism. **Critically, every chunk is assigned a stable `node_id` which serves as the canonical evidence anchor for the entire project** — all retrieval metrics, citation checks, and ground-truth mappings key off `node_id`, never off rendered page numbers (see Section 7).

```text
+------------------------------------------------------------------------+
|                      RAW SEC 10-K FILING (HTML / PDF)                   |
+------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|           LLAMAPARSE ENGINE (Atomic Table Extraction Mode)             |
+------------------------------------------------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+---------------------------------------+       +------------------------------------+
| Continuous Narrative Prose Paragraphs |       |  Tabular Data Blocks               |
| (Clean Markdown Strings)              |       | (Clean Markdown Tables) with clear |
|                                       |       | titles and descriptions to retain  |
|                                       |       | the relevance in metadata          |
+---------------------------------------+       +------------------------------------+
            |                                               |
            +-----------------------+-----------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|        TEXTNODE ENRICHMENT LAYER (Metadata Injected Programmatically)   |
|  - node_id (CANONICAL EVIDENCE ANCHOR)   - parent_item_header           |
|  - document_id                           - node_type (Text vs Table)    |
|  - source_page_num (DERIVED, DISPLAY-ONLY)                              |
+------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|          PARSING VALIDATION GUARDRAIL (Randomized 20-Section Audit)    |
|  - Checks: Column truncation, table bisection, markdown rendering      |
+------------------------------------------------------------------------+
```

* **Atomic Table Preservation**: Standard token-count or paragraph-based splitting breaks row-and-column alignment, destroying cell relationships and rendering tabular financial analysis incoherent. This project mandates the use of **LlamaParse** configured explicitly for **atomic table extraction into clean Markdown syntax**.
* **Node Atomicity**: The parser is programmatically configured to treat each isolated table as an independent, indivisible `TextNode`. It is strictly prohibited to bisect or slice a Markdown table block during parsing.
* **Canonical Node IDs**: Every node receives a stable, unique `node_id` at parse time. Because SEC filings are natively HTML (no intrinsic pages) and any PDF pagination is render-dependent, **page numbers are unreliable as a coordinate system.** `node_id` is therefore the single source of truth for "where evidence lives"; `source_page_num` is retained only as a human-readable display field.
* **Metadata Enrichment Layer**: Every node is enriched with structural context prior to indexing. This metadata binds parent section headers (e.g., *Item 1A: Risk Factors*, *Item 8: Financial Statements*) to each text snippet and table, preserving structural lineage.
* **Structural Parsing Validation**: A manual audit is carried out on a randomized sample of 20 distinct document sections. If table fragmentation, column truncation, or row misalignment is observed, parsing parameters are tuned or corrupted files discarded to ensure a pristine baseline.

---

## 3. The 140-Query Benchmark Dataset: Three Disjoint Sets

Evaluation rests on a stratified pool of **140 queries**, split into **three completely disjoint sets** stored in three separate SQLite tables. Keeping the sets disjoint is a deliberate machine-learning-hygiene decision: it prevents the data that *teaches* the automated judge from contaminating the data that *tests* it, and keeps both separate from the data the pipelines are *benchmarked* on.

```text
+-------------------------------------------------------------------------+
|                      VERIFIED QUERY POOL (140 total)                    |
+-------------------------------------------------------------------------+
            |                        |                        |
            v                        v                        v
   +----------------+      +-------------------+      +--------------------+
   | PQ : 100       |      | GQ : 20           |      | JEQ : 20           |
   | Pipeline Queries|     | Golden Queries     |     | Judge Eval Queries |
   | (25 / quadrant) |     | (5 / quadrant)     |     | (5 / quadrant)     |
   | TEST SET        |     | TEACHING SET       |     | VALIDATION SET     |
   +----------------+      +-------------------+      +--------------------+
   table: queries          table: golden_queries     table: judge_validation
   benchmarks pipelines    teaches the judge          tests the judge
                           (+ HUMAN "why good")       (+ HUMAN scores)
```

* **PQ — Pipeline Queries (100, the test set):** the queries every pipeline is benchmarked on. 25 per quadrant.
* **GQ — Golden Queries (20, the teaching set):** 5 per quadrant. Each carries a **human-written "why this answer is good" note** and a scored example, and is injected into the Judge's prompt as a few-shot exemplar so the Judge grades to a human standard. *Never seen by the pipelines.*
* **JEQ — Judge Evaluation Queries (20, the validation set):** 5 per quadrant. Used exclusively to validate the Judge: the researcher hand-scores the pipeline outputs for these queries, the Judge scores the same outputs, and the two are compared (see Section 5 / Section 7). *Never injected into any prompt.*

### The Four Quadrants

Each set is stratified across four operational quadrants so per-paradigm strengths and failure modes are exposed by query type:

```text
                           TEXT-HEAVY CONTEXT             TABLE-HEAVY CONTEXT
                    +------------------------------+------------------------------+
  DIRECT /          |              Q1              |              Q3              |
  EXPLICIT          |         Direct Text          |         Direct Table         |
  RETRIEVAL         |       (Fact Retrieval)       |     (Cell/Value Extraction)  |
                    +------------------------------+------------------------------+
  IMPLICIT /        |              Q2              |              Q4              |
  SYNTHESIS         |        Implicit Text         |        Implicit Table        |
  RETRIEVAL         |    (Multi-Hop Inference)     |   (Cross-Row/Footnote Calc)  |
                    +------------------------------+------------------------------+
```

* **Q1 — Direct Text:** fact retrieval from dense continuous prose (e.g., an explicitly stated legal liability or risk disclosure).
* **Q2 — Implicit Text:** thematic synthesis across disparate narrative pages (e.g., cross-referencing management's strategic outlook in the MD&A).
* **Q3 — Direct Table:** strict cellular extraction from tables (e.g., pulling an exact revenue figure or cash balance row).
* **Q4 — Implicit Table:** math-inference and comparative logic (e.g., multi-year segment-revenue change, or recalculation that cross-references rows with appended footnotes).

### Dataset Controls and Meta-Tagging

Every query is stored as a deterministic record with explicit ground-truth mappings anchored on **node IDs**, not pages:

```json
{
  "query_id": "Q4_087",
  "quadrant": "Q4_Implicit_Table",
  "query_text": "Using the operating-expense breakdown in the income statement, calculate the year-over-year percentage change in total operating expenses for FY2025, then adjust for the restructuring impairment disclosed in the footnotes.",
  "ground_truth_answer": "Operating expenses decreased 4.2% YoY. Factoring in the $15M impairment, normalized expenses rose 1.1%.",
  "gt_citations": ["SEC_10K_XYZ_2025_n0588", "SEC_10K_XYZ_2025_n0742"],
  "document_id": "SEC_10K_XYZ_CORP_2025"
}
```

> `gt_citations` is a list of `node_id`s (the canonical evidence anchor). `source_page_num` may be carried alongside for human readability but is never the match key.

---

## 4. Open-Model Generation and Adversarial Verification Architecture

To produce 140 ground-truth queries without manual authoring while remaining academically rigorous, the system uses **open-source instruction models served on Groq's free tier** (no credit card; rate-limited rather than billed). Because open models cap at a ~128K-token context window — far short of an entire 10-K — generation operates on a **per-section (chunked) basis**: each section (e.g., *Item 1A*, *Item 7 MD&A*, *Item 8*) is fed independently with its node range tracked, so the model always reasons over a context that fits in-window.

The **Generator and Critic use different model families** to break the circular-validation loop: agreement between two independent architectures is far stronger evidence of a query's soundness than agreement within one family.

```text
       +-------------------------------------------------------------+
       |        SEC 10-K SPLIT INTO PER-SECTION CHUNKS (<128K)        |
       +-------------------------------------------------------------+
                                      |
                                      v
                       +------------------------------+
                       |   Generator Agent            |
                       |   (openai/gpt-oss-120b)      |
                       |   Creates: query, answer,    |
                       |   node-ID citations          |
                       +------------------------------+
                                      |
                                      | (hide answer & citations from Critic)
                                      v
                       +------------------------------+
                       |   Critic Agent               |
                       |   (Qwen3.6-27B) + SEARCH TOOL  |
                       |   independent search over    |
                       |   ALL nodes of the filing    |
                       +------------------------------+
                                      |
                                      v
                       +------------------------------+
                       |    Automated Cross-Check     |
                       |    (node-ID + value match)   |
                       +------------------------------+
                                  /        \
                           (Yes) /          \ (No)
                                v            v
                +-------------------+    +-------------------+
                |   Auto-Verified   |    |      Discard      |
                |   140-Query Pool  |    |   & Regenerate    |
                +-------------------+    +-------------------+
```

### Step 1 — Per-Section Ground-Truth Synthesis (Generator: `openai/gpt-oss-120b`)

* A Python script targets the Groq API using **`openai/gpt-oss-120b`** to read one parsed section at a time.
* For each section the model outputs quadrant-appropriate questions plus the exact `gt_citations` (node IDs) and a detailed `ground_truth_answer` sourced directly from the material.
* Questions accumulate across sections until each quadrant reaches its target count (25 PQ + 5 GQ + 5 JEQ per quadrant = 35/quadrant; 140 total).

### Step 2 — Multi-Agent Adversarial Quality Control (Critic: `Qwen3.6-27B` + search tool)

The Critic runs on **`Qwen3.6-27B`** — a deliberately different family from the gpt-oss Generator — so agreement reflects cross-architecture consensus:

1. **Blind test:** the Critic receives *only* `query_text`. The ground-truth answer and node citations are redacted.
2. **Independent search:** the Critic is given a **search tool over all parsed nodes of the filing** (not just the section the Generator saw) and must independently locate the answer and cite the node(s) it relied on. Searching the whole filing — rather than the single source section — is what makes the verification genuinely independent.
3. **Automated cross-check (code):** a deterministic layer compares the Critic's cited nodes and value against the Generator's ground truth. Agreement → **Auto-Verified**; mismatch → **discard and regenerate**.

---

## 5. The Human Anchor: Two Roles, Two Sets

Two small human-labelled sets anchor the otherwise-automated evaluation. They do **different jobs** and must not be confused:

```text
   +-----------------------------+        +------------------------------+
   |   GQ — 20 TEACHING items    |        |   JEQ — 20 VALIDATION items  |
   |   "the textbook"            |        |   "the exam"                 |
   +-----------------------------+        +------------------------------+
   | Human writes "why good"     |        | Human hand-scores the        |
   | notes + an example score    |        | PIPELINE OUTPUTS for these   |
   |                             |        | queries                      |
   | -> INJECTED into Judge      |        | -> NEVER injected            |
   |    prompt (5 per quadrant)  |        | -> Judge scores same outputs |
   |    to TEACH the rubric      |        | -> compare Human vs Judge    |
   +-----------------------------+        +------------------------------+
            TEACHES the judge                   TESTS the judge
```

### Role 1 — GQ teaches the Judge (few-shot)

For each of the 20 GQ, the researcher records: the query and quadrant, an example pipeline output, a human 1–10 score, and a granular justification ("why this answer earned this score"). These become few-shot exemplars in the Judge's prompt so it learns the human grading standard. This avoids fine-tuning (and its black-box biases).

**Dynamic few-shot rerouting (mandatory):** injecting all 20 exemplars mixes table-grading and text-grading examples indiscriminately and bloats every call. Instead, before grading an output the worker reads the target query's `quadrant` and injects **only the 5 GQ exemplars matching that quadrant** (`WHERE quadrant = :current_quadrant`). The other 15 are omitted. This yields **four cacheable prompt prefixes** (one per quadrant) and keeps each Judge call tightly relevant.

### Role 2 — JEQ validates the Judge (the >80% gate)

Teaching is not the same as proving the teaching worked. To certify the automated Judge before trusting it at scale:

1. The 20 JEQ are run through the in-scope pipelines (see Section 7, Phase 2) to produce real outputs.
2. **The researcher hand-scores those outputs** on the same 1–10 rubric.
3. The Judge scores the same outputs, blind to the human scores.
4. The **LLM-Judge Agreement Rate** is computed across the JEQ outputs. The Judge must reach **>80% agreement** before it is permitted to grade the full benchmark. If it fails, the Judge's rubric or model is changed and the check repeats.

> If `Qwen3.6-27B` cannot clear the >80% bar, there are 3 fallback options:
> 1. Swap the Judge to `openai/gpt-oss-120b` — still a different family from the Llama answerer, so the no-self-judging rule holds.
> 2. Tune the scoring rubrics.
> 3. Both.

---

## 6. Multi-Pipeline Architectural Registry

This project benchmarks **three in-scope retrieval architectures (P1, P2, P3)**. Three further architectures are documented and reserved as future scope, ranked by increasing architectural complexity, to demonstrate deliberate scoping and preserve a clear future-work narrative.

```text
                  +---------------------------------------+
                  |       RESEARCH PIPELINE REGISTRY      |
                  +---------------------------------------+
                                      |
         +----------------------------+----------------------------+
         |                                                         |
         v                                                         v
+---------------------------------------+         +---------------------------------------+
|              IN SCOPE                 |         |        FUTURE SCOPE (if time)         |
+---------------------------------------+         +---------------------------------------+
| P1: Vector RAG (meaning)              |         | P4: Brute-Force Full-Context          |
|     bge embeddings + bge reranker     |         |     (no retrieval)                    |
| P2: Keyword RAG (exact words)         |         | P5: Naive Vector RAG                  |
|     rank_bm25 (true BM25)             |         |     (single-stage, flat)              |
| P3: Structural RAG (summary tree)     |         | P6: Hybrid Fusion RAG                 |
|     SummaryIndex + 1-time LLM build   |         |     (two-stage composite)             |
+---------------------------------------+         +---------------------------------------+
```

### In-Scope Pipelines

* **P1 — Vector RAG (retrieval by meaning).** Dense semantic retrieval: embeddings generated locally with `BAAI/bge-small-en-v1.5`, followed by a local cross-encoder **re-ranker** (`BAAI/bge-reranker-base`, CPU, $0) that re-orders the top-N candidates before generation. **Design note:** an earlier draft added a hard *metadata pre-filter* (restricting search to a target Item). That pre-filter was **dropped** for the core comparison — deciding the target section at query time risks leaking the answer location, and BM25 has no equivalent step, so it would compare "vector + a head-start + reranker" against "raw BM25" rather than paradigm-vs-paradigm. P1 is therefore a *clean* embeddings-plus-reranker pipeline. (A metadata-pre-filter ablation is a possible extension.)

* **P2 — Keyword RAG (retrieval by exact words).** Implemented via **`rank_bm25`**, applying the statistical **Okapi BM25** algorithm directly over tokenized nodes. It bypasses dense vector space entirely; retrieval is deterministic, reproducible, and needs no LLM at the retrieval step. **Tokenization is decisive and custom** (Section 7 / Guardrails §2): a regex tokenizer preserves numbers, decimals, `%`, and currency tokens, strips table-markdown pipes while keeping cell values, applies no stemming, and is used identically at index and query time. *Design note:* LlamaIndex's `KeywordTableIndex` is rejected for this role — it uses an LLM to extract keywords, so it is neither statistical nor deterministic.

* **P3 — Structural RAG (retrieval by summary-tree traversal).** Retrieval traverses a hierarchical `SummaryIndex` built from parent summaries over child nodes. **This pipeline requires a one-time summary-index build step (Phase 0.5) that uses an LLM** — `llama-3.1-8b-instant` on Groq's free tier, chosen for its high daily request ceiling so bulk per-node summarisation does not exhaust the tighter caps reserved for generation and judging. The index is built once and cached; it is never rebuilt. **Known risk (documented, not hidden):** summary generation can drop cell values, footnotes, and narrow row variables, so P3 is expected to be weakest on the table-heavy quadrants (Q3/Q4). Including it tests exactly how badly hierarchical summarisation degrades on dense financial tables.

### Future-Scope Pipelines (ranked by increasing complexity)

* **P4 — Brute-Force Full-Context [no retrieval].** Inject the entire parsed document into the context window. Infeasible for full 10-Ks under a ~128K cap; useful only as a context-ceiling reference on short filings.
* **P5 — Naive Vector RAG [single-stage].** Flat embedding space with top-K cosine similarity, no re-ranking — the un-optimised ablation of P1, isolating how much the re-ranker contributes.
* **P6 — Hybrid Fusion RAG [two-stage].** Routes queries through BM25 to narrow context, then vector search within that subset. Reserved due to cascading-routing-degradation risk: a faulty first-stage filter starves the second stage.

---

## 7. Tri-Pillar Evaluation, the Judge-Validation Gate, and the Full Benchmark

Pipelines are audited across three independent pillars. Both retrieval-bearing pipelines and P3 are tested at **three values of K**:

$$\mathbf{K \in \{3, 5, 10\}}$$

Evaluation runs in two distinct phases. **Phase 2 (judge validation) is a hard gate that runs before the expensive Phase 3 (full benchmark)** — so a broken judge can never silently grade the entire matrix.

```text
PHASE 2 — JUDGE VALIDATION GATE  (cheap; runs FIRST)
----------------------------------------------------
  Run JEQ (20) on P1, P2, P3 at a SINGLE K = 5   ->   60 outputs
        |                                                  |
        v                                                  v
  HUMAN scores 60                                  JUDGE scores 60
  (by hand)                                        (Qwen3.6-27B, few-shot by GQ)
        \                                                  /
         \------------------> Agreement > 80% ? <---------/
                                |            |
                             NO |            | YES
                                v            v
                       fix Judge       Judge trusted -> Phase 3
                       (rubric/model)
                                |
                                +--> re-test


PHASE 3 — FULL BENCHMARK  (expensive; runs only after the gate passes)
----------------------------------------------------------------------
  Run PQ (100) on P1, P2, P3  x  K = {3, 5, 10}   ->   900 runs
        |
        v
  Trusted Judge + deterministic code metrics score every run
        |
        v
  results table  ->  analysis & comparison
```

### Pillar 1 — Retrieval Metrics (deterministic, code-only; node-based)

All retrieval metrics operate on **node IDs**, which guarantees they are well-defined and bounded.

* **Precision@K** — of the K retrieved nodes, the fraction that are ground-truth-relevant:

$$\text{Precision}@K = \frac{|\{\text{retrieved top-}K\} \cap \{\text{GT nodes}\}|}{K}$$

* **Recall@K** — the fraction of *distinct* ground-truth nodes captured in the top-K (capped at 1 by construction; the numerator is the *set* of GT nodes hit, deduplicated):

$$\text{Recall}@K = \frac{|\{\text{distinct GT nodes appearing in top-}K\}|}{|\{\text{all GT nodes}\}|}$$

* **Evidence Hit Rate** — binary flag: is the critical ground-truth node present anywhere in the retrieved bundle?

### Pillar 2 — Answer-Quality Metrics

* **LLM-as-a-Judge (1–10) — PRIMARY.** The Judge (`Qwen3.6-27B`) scores each pipeline output against the stored `ground_truth_answer` using the fixed rubric plus the 5 quadrant-matched GQ exemplars. Because it scores semantic correctness against a reference, it handles the long, multi-phrased answers in Q2/Q4 that string metrics cannot.
* **Token-level F1 — SECONDARY (lexical).** Overlap between output and ground-truth text. Reported throughout but never primary.
* **Exact Match — Q1/Q3 ONLY.** EM requires an exact string match, which is meaningful only for short canonical answers (direct extraction). It is reported for Q1/Q3 with **numeric normalisation** (so `$394.3B` = `394,300 million`) and is **not** used for Q2/Q4. For numeric answers a tolerance check (parse and compare within ε) is preferred over raw string match.
* **Citation Audit — deterministic, code-only.** A code layer checks whether the node IDs cited in the output are a subset of the query's `gt_citations`. A correct-looking answer with mismatched citations is flagged as **coincidental correctness** and its score downgraded. This check is computed in code (not asked of the Judge), because LLMs are unreliable at comparing ID strings.
* **Agreement-Rate Guardrail.** The Phase-2 JEQ gate above; full benchmarking proceeds only at **>80%** human–judge agreement.

### Pillar 3 — Efficiency Metrics

* **Latency per query** (seconds, submission → final token).
* **Token consumption per query** (input/output volume).
* **One-time index-build cost** — wall-clock and (for P3) token cost of building each index: local vector index vs. `rank_bm25` statistical index vs. P3's LLM-built summary tree. This is a research metric, not a financial one.

### Determinism

All LLM calls run at **`temperature = 0`** for near-deterministic outputs. Because temperature 0 outputs barely vary between runs, each of the 900 cells is run **once** (repeated runs would multiply token cost to learn nothing). If a robustness check is wanted, a few seeded repeats are run on the JEQ subset only — never the full 100.

---

## 8. Complete Pipeline Structure (Bird's-Eye View)

```text
==================================================================
              SEC 10-K RAG BENCHMARK  —  BIRD'S-EYE FLOW
==================================================================

PHASE 0 — INGESTION
-------------------
   [ Raw 10-K Filings ]
            |
            v
   [ Parse + Chunk (+ metadata, node_id) ]
            |
            v
   [ Node Store ]
            |
            +--------------------------------------------------+
            |                                                  |
            v                                                  v

PHASE 0.5 — P3 SUMMARY INDEX BUILD  (one-time, P3 only)
--------------------------------------------------------
                                              [ Generate summary tree
                                                over all nodes
                                                (llama-3.1-8b-instant,
                                                 Groq free tier)       ]
                                                           |
                                                           v
                                              [ Summary Index Store ]

PHASE 1 — DATASET GENERATION
----------------------------
   [ Generate 140 queries (question + answer + node-ID citations)
     Generator: openai/gpt-oss-120b ]
            |
            v
   [ Critic verifies independently
     Qwen3.6-27B + search tool over all nodes ]
            |
            v
   [ Verified pool ] --- split into 3 DISJOINT sets --->
            |
            +---------------------+---------------------+
            v                     v                     v
      [ PQ : 100 ]          [ GQ : 20 ]           [ JEQ : 20 ]
       test set             teaching set           eval set
            |                     |                     |
       (-> Phase 3)        + HUMAN labels         (-> Phase 2)
                           "why good"
                           (teaches the judge)

PHASE 2 — JUDGE VALIDATION   (GATE: runs BEFORE the full benchmark)
------------------------------------------------------------------
   [ Run JEQ (20) on P1, P2, P3 at ONE K = 5 ]  =  60 outputs
            |
            +----------------------+----------------------+
            v                                              v
   [ HUMAN scores 60 ]                          [ Judge scores 60 ]
                                                (Qwen3.6-27B, few-shot by GQ)
            |                                              |
            +----------------------+----------------------+
                                   v
                       [ Agreement > 80% ? ]
                           |               |
                        NO |               | YES
                           v               v
                  [ Fix judge ]      ( judge trusted )
                  rubric / model            |
                           |                |
                           +--> (re-test)   |
                                            v

PHASE 3 — FULL BENCHMARK   (uses PQ + the trusted judge)
--------------------------------------------------------
   [ Run PQ (100) on P1, P2, P3  x  K = {3, 5, 10} ]  =  900 runs
     Answerer (shared): Llama 3.3 70B
            |
            v
   [ Trusted judge (Qwen3.6-27B) + code metrics score everything ]
            |
            v
   [ Results Store  ->  Analysis & Comparison ]

==================================================================
MODEL ROUTING (summary)
==================================================================
   Dataset generation ....... openai/gpt-oss-120b     (Groq, free)
   Dataset critique ......... Qwen3.6-27B + search tool (Groq, free)
   P3 summary-index build ... llama-3.1-8b-instant    (Groq, free)
   Pipeline answers (P1/P2/P3) Llama 3.3 70B          (Groq, free)
   Judge .................... Qwen3.6-27B, no search    (Groq, free)
   Embeddings ............... bge-small-en-v1.5        (local CPU, $0)
   Reranker (P1) ............ bge-reranker-base        (local CPU, $0)
   BM25 (P2) ................ rank_bm25                (local CPU, $0)

HUMAN-IN-THE-LOOP:
   *  Phase 1 — label the 20 GQ ("why this answer is good")
   *  Phase 2 — hand-score the 60 outputs for the judge gate
==================================================================
```

---

## 9. Limitations and Caveats

### Combinatorial Scale and Execution Overhead

```text
+-----------------------------------------------------------------------+
|                        COMBINATORIAL SCALE MATH                       |
+-----------------------------------------------------------------------+
|  100 Pipeline Queries (PQ; 25 per quadrant)                           |
|                                                                       |
|  In-scope pipelines: P1 (Vector), P2 (BM25), P3 (Structural)          |
|  Each runs at K = 3, 5, 10                                            |
|                                                                       |
|  3 Pipelines x 3 K-Values = 9                                         |
|  9 x 100 Queries = 900 runs                                           |
+-----------------------------------------------------------------------+
|  FULL-BENCHMARK PIPELINE GENERATIONS = 900 RUNS                       |
|  FULL-BENCHMARK JUDGE EVALUATIONS    = 900 RUNS                       |
|  + JUDGE-VALIDATION (Phase 2):  60 outputs x (human + judge)          |
+-----------------------------------------------------------------------+
```

* **Query-count baseline:** 100 PQ (25/quadrant) balances per-quadrant signal against a solo 10-week timeline; larger pools add little insight at this scope while multiplying load.
* **Run-count multiplier:** 3 pipelines × 3 K-values × 100 PQ = **900 generation runs**.
* **Evaluation volume:** each of the 900 outputs is judged once → **900 judge runs**, plus the 60-output Phase-2 validation (hand-scored *and* judge-scored).
* **Statistical honesty:** a single temperature-0 run per cell, with a single ~80% judge-validation pass on 60 samples, is a pragmatic reliability check appropriate to an M.Sc. — not a strong statistical proof of judge accuracy. The write-up should frame it as such.

### Asynchronous Batch Processing

Running 900 generations + 900 judgements via synchronous loops is slow and fragile (≈2s network wait per call, frequent socket timeouts). The system must use asynchronous worker pools (`asyncio` / native async SDK clients) with bounded concurrency, reducing wall-clock from hours to minutes per batch while respecting rate limits.

### Groq Free-Tier Rate Limits — the binding constraint is the **token-per-day (TPD)** ceiling, not request count

Free-tier limits are per-model and **per-organization** (extra API keys do not raise the ceiling). As verified mid-2026, `llama-3.3-70b-versatile` is published at ~30 RPM, ~1,000 RPD, ~12K TPM, and ~100K TPD; `openai/gpt-oss-120b` at ~30 RPM, ~1,000 RPD, ~8K TPM, ~200K TPD; `qwen/qwen3.6-27b` at ~60 RPM / ~6K TPM (TPM is its tight axis); `llama-3.1-8b-instant` allows far higher daily request volume. **The answer-generation and judging phases are token-heavy, so TPD — not RPD — is what gates throughput.** See `Budget.md` for the full reconciliation and the prompt-caching lever (cached tokens do not count toward limits). HTTP 429s are handled with `tenacity` exponential backoff + jitter (Guardrails §5). There is no spend ceiling to exhaust — only daily token throughput.

### Software Stack Version Instability (LlamaIndex Drift)

LlamaIndex changes rapidly with breaking syntax. Code must pin exact versions (e.g. `llama-index==0.10.x`, fixed `rank-bm25`) and current docs should be fed to any coding assistant to prevent invented parameters.

### Relational Data Management

900 runs across three pipelines and three K-values, plus three query tables, are unmanageable as loose CSV/JSON. A local **SQLite schema** is required from day one with isolated tables (`nodes`, `queries`, `golden_queries`, `judge_validation`, `results`); results are committed per-run so a crash resumes from the last written row instead of re-spending requests.

### Coincidental Correctness and Citation Blindspots

```text
                      COINCIDENTAL CORRECTNESS TRAP

   Target Query: "What was the FY2025 R&D spend?"  [True value: $150M, node n0451]

   [Faulty retrieval] ---> pulls node n0120 (unrelated marketing table)
                            n0120 happens to list a $150M lease expense.
   [Generation LLM]  ---> reads n0120, extracts "$150M".

   Result: looks 100% correct to Token-F1 / Exact-Match, but retrieval failed.
```

* **Mitigation (code):** the **Citation Audit** checks whether the output's cited node IDs are a subset of the query's `gt_citations`. On mismatch the score is programmatically downgraded, exposing the faulty retrieval step.

---

## 10. Academic Rigor and Methodological Principles

1. **Standardised context volumes.** To keep P1, P2, and P3 comparable, the total context mass (token volume passed to the answerer) is held constant across pipelines at each value of K.
2. **No leakage to the pipelines.** The pipelines receive *only* retrieved nodes + the query — never few-shot exemplars, never ground-truth answers or citations, and (per the dropped metadata pre-filter) no answer-location hints. This is what keeps the retrieval comparison honest.
3. **Separation of model roles.** Generator (`gpt-oss-120b`) ≠ Critic (`Qwen3.6-27B`); Answerer (`Llama 3.3 70B`) ≠ Judge (`Qwen3.6-27B`). No model grades its own output, and dataset agreement reflects cross-architecture consensus.
4. **Validated automated judging.** The automated Judge is trusted only after clearing the >80% human-agreement gate (Phase 2) on a held-out set (JEQ) that is disjoint from its teaching set (GQ).
5. **Explicit citation enforcement.** RAG prompts mandate node-ID source attributions so the Citation Audit can flag coincidental correctness.
6. **Methodological transparency.** The methodology chapter documents all six architectural iterations and gives engineering-based justifications for the in-scope three (P1/P2/P3) and the reserved three (P4/P5/P6), establishing a clear narrative of deliberate scoping around the core semantic-vs-statistical comparison, with structural RAG as a third paradigm.