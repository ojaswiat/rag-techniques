# Phase Plan — COMP702 RAG Benchmark Build

This plan covers the **technical build only** (not the CA1 proposal or the dissertation write-up). It is scoped to a **solo 10-week total budget**, with the final stretch reserved for the dissertation write-up — so active build work (Phases 1–6) must substantially wrap by the end of **Week 7**. The schedule below reflects a multi-filing corpus (2–3 companies × 2–3 fiscal years, ≈6–9 SEC 10-Ks) rather than a single filing — see `Architecture.md` §0/§8 for the full rationale.

It tracks the three in-scope pipelines (**P1 Vector**, **P2 BM25**, **P3 Structural**) and the phase structure in `Project_Idea.md §8`, with all constraints from `Guardrails.md` and `Budget.md` enforced.

## Scheduling notes (read before the phases)
- **The full benchmark must start early.** On strict $0 the 900-run matrix is TPD-bound and spans ~2–3 weeks of intermittent running (`Budget.md §2`). It therefore kicks off the moment the judge gate passes (~Week 7) and runs *in the background* via the SQLite resume logic while later analysis work proceeds. Paid Developer tier (~1–2 days) is the documented fallback if the schedule slips.
- **Two manual bottlenecks must be slotted in:** hand-labelling the 20 GQ exemplars (end of Phase 4) and hand-scoring the 60 gate outputs (Phase 6). Neither is parallelisable away.
- **Run everything under `LOCAL_TEST_THROTTLE = True` (3 items) first** in every phase that calls an LLM, before releasing the full batch (`Guardrails.md §7`).

---

# Phase 1: Environment, Infrastructure & Cost Guardrails
Stand up the repo, the SQLite state layer, and the rate-limit/throttle scaffolding that every later phase depends on. Nothing here calls a model in anger — it builds the rails that keep the project at $0 and crash-resilient.
**Week 1**

## Goals
1. Initialise the repo and pin exact versions (`llama-index==0.10.x`, fixed `rank-bm25`, `bge` models, Groq + LlamaParse SDKs) to guard against LlamaIndex drift.
2. Provision free-tier access: Groq API key, LlamaParse account; re-verify current Groq model availability and per-organization RPM/RPD/**TPM/TPD** limits at `console.groq.com`.
3. Build `database_manager.py` with the **five isolated SQLite tables**: `nodes`, `queries` (100 PQ), `golden_queries` (20 GQ), `judge_validation` (20 JEQ), `results` (900 runs).
4. Build a resilient Groq call wrapper: `tenacity` exponential backoff + randomised jitter on HTTP 429, and an `asyncio.Semaphore` capped at **≤ 5 parallel workers**.
5. Add the `LOCAL_TEST_THROTTLE` boolean pattern (forces `LIMIT 3`) to the top of every loop script template.

## Evaluations
1. A fresh clone installs cleanly from pinned versions with no dependency conflicts.
2. The five tables instantiate with correct schemas and enforce the disjoint-set constraint (no `query_id` can exist in more than one query table).
3. A deliberately rate-limited test triggers 429s and confirms the wrapper backs off and recovers instead of crashing.
4. Groq limits are recorded in-repo with the verification date.

## Deliverables
1. Version-pinned repo with `requirements.txt` / lockfile.
2. `database_manager.py` and an initialised, empty SQLite database.
3. Reusable async Groq client wrapper (backoff + semaphore) and the `LOCAL_TEST_THROTTLE` template.
4. A short `groq_limits.md` note recording verified limits and the check date.

---

# Phase 2: Ingestion & Parsing Pipeline
Turn raw SEC 10-K filings into a clean, metadata-rich node store. Every downstream metric keys off the `node_id` produced here, so correctness in this phase is load-bearing for the whole project.
**Weeks 1–3** *(extended from 2 to 3 weeks: the corpus is now ~6–9 filings — 2–3 companies × 2–3 fiscal years — not one)*

## Goals
1. Source the target 10-K filing(s) from SEC EDGAR.
2. Parse with **LlamaParse in atomic-table mode** (Cost-effective tier) into clean Markdown; never bisect a table block.
3. Enrich every node with metadata: **`node_id` (canonical evidence anchor)**, `parent_item_header`, `node_type` (Text vs Table), and `source_page_num` (display-only, never a match key).
4. Persist parsed Markdown + nodes to SQLite immediately and cache aggressively (re-parse within 48h is free).
5. Run the randomised **20-section parsing validation audit** (column truncation, table bisection, markdown rendering).

## Evaluations
1. Tables survive as intact, indivisible `TextNode`s with rows/columns aligned and titles/descriptions retained in metadata.
2. Every node carries a stable, unique `node_id`; the 20-section audit shows no fragmentation or truncation (or offending files are re-tuned/discarded).
3. The `nodes` table is fully populated and re-running ingestion hits the cache rather than re-parsing.

## Deliverables
1. Populated `nodes` table (canonical node store).
2. The ingestion/parsing script with caching.
3. A short parsing-audit report on the 20 sampled sections.

---

# Phase 3: P3 Summary-Index Build (one-time)
Build the hierarchical summary tree that P3 retrieves over (one tree per filing). This is the **only** index build permitted to use an LLM, and it must run once and be cached — never per query (`Guardrails.md §1`).
**Week 3**

## Goals
1. Build a hierarchical `SummaryIndex` (parent summaries over child nodes) using **`llama-3.1-8b-instant`** on Groq's free tier (chosen for its high daily request ceiling so it does not touch the tighter 70B/gpt-oss caps).
2. Run the build under `LOCAL_TEST_THROTTLE = True` first, then release in full.
3. Persist the summary index to disk/SQLite and confirm it is loaded from cache thereafter, never rebuilt.

## Evaluations
1. The summary tree covers all nodes and loads from cache on a second run with zero new LLM calls.
2. Build wall-clock and token cost are logged (these feed the Pillar 3 efficiency metric).
3. Spot-check confirms the documented risk — summaries dropping cell values/footnotes on table-heavy sections — so the expected Q3/Q4 weakness is observed, not hidden.

## Deliverables
1. Cached, persisted P3 summary index.
2. The one-time build script with the throttle and caching logic.
3. Logged build cost (wall-clock + tokens).

---

# Phase 4: Dataset Generation & Adversarial Verification
Produce the 140-query benchmark via cross-family generation and critique, then split it into three disjoint sets and human-label the teaching set.
**Weeks 4–5**

## Goals
1. **Generator (`openai/gpt-oss-120b`):** per-section (chunked, <128K) generation of quadrant-appropriate `query_text`, `ground_truth_answer`, and `gt_citations` (node IDs), accumulating to 35/quadrant (140 total).
2. **Critic (`Qwen3.6-27B`) — a different family — with a search tool over *all* nodes of the filing:** blind verification (answer + citations redacted), independently locating and citing evidence.
3. **Automated code cross-check:** compare Critic's cited nodes + value against the Generator's ground truth → Auto-Verify or discard-and-regenerate.
4. Split the verified pool into three **disjoint** sets: **PQ 100 / GQ 20 / JEQ 20**, 25/5/5 per quadrant.
5. **Human-label the 20 GQ** with "why this answer is good" notes and example 1–10 scores (the few-shot teaching material).

## Evaluations
1. Generator never injects a full filing in one call; per-section context stays in-window.
2. Generator and Critic remain different families, and the Critic searches the whole filing, not just the source section.
3. Cross-check is deterministic code (node-ID + value match), not an LLM judgement.
4. The three query tables are provably non-overlapping; each quadrant hits its target counts.
5. All 20 GQ carry complete human notes and example scores.

## Deliverables
1. Populated `queries` (100), `golden_queries` (20, human-labelled), and `judge_validation` (20) tables.
2. `async_generator.py` and `async_critic.py` (with search tool) plus the cross-check layer.
3. A short verification-yield log (accepted vs regenerated).

---

# Phase 5: Pipeline Implementation (P1 / P2 / P3)
Implement all three retrieval paradigms and the single shared answerer, with leakage controls and standardised context mass so any score difference is attributable to retrieval, not generation.
**Weeks 5–6**

## Goals
1. **P1 — Vector:** local `bge-small-en-v1.5` embeddings + local `bge-reranker-base` cross-encoder over a local index (FAISS/Chroma). **No metadata pre-filter / section head-start.**
2. **P2 — BM25:** `rank_bm25` (true Okapi BM25) with the **custom regex tokenizer** (preserves numbers, decimals, `%`, currency; strips table pipes but keeps cell values; no stemming; identical at index and query time). **No `KeywordTableIndex`.**
3. **P3 — Structural:** retrieval by traversing the cached summary index from Phase 3, via the real LlamaIndex `.as_retriever(retriever_mode="embedding")` on the index object built in Phase 3 (deferred here deliberately — see `docs/superpowers/specs/2026-07-22-phase3-summary-index-design.md`, "Out of scope").
4. **Shared answerer (`Llama 3.3 70B`, `temperature = 0`)** across all three pipelines at identical settings, with prompts that mandate node-ID citations and receive **only the query + retrieved nodes** (no exemplars, no ground truth, no answer-location hint).
5. Hold total context mass constant across pipelines at each K.

## Evaluations
1. P1 is a clean embeddings-plus-reranker pipeline with no section pre-filter; all retrieval compute runs locally on CPU at $0.
2. P2 retrieval is fully statistical, deterministic, and reproducible; the tokenizer is byte-identical at index and query time.
3. The answerer is identical (model + settings) across P1/P2/P3, and remains a different family from the Qwen judge.
4. A leakage spot-check confirms pipelines receive nothing beyond the query and their own retrieved nodes.

## Deliverables
1. Three runnable retrieval pipelines (P1/P2/P3) sharing one answerer module.
2. The custom BM25 tokenizer (documented).
3. `loop_executor.py` wired to the answerer and the `results` table.

---

# Phase 6: Judge Build & Validation Gate
Build the LLM-as-a-Judge with dynamic few-shot routing and code-based citation auditing, then **prove it against the human standard before any full run**. This is a hard gate.
**Weeks 6–7**

## Goals
1. **`async_judge.py`:** for each output, read the target quadrant and inject **exactly the 5 GQ exemplars matching that quadrant** → four cacheable prompt prefixes (rubric + 5 exemplars). Cached tokens don't count toward limits.
2. **Deterministic code metrics:** Citation Audit (output cited node IDs ⊆ `gt_citations`), Token-F1, Exact Match (Q1/Q3 only, numeric-normalised + ε tolerance), Precision@K, Recall@K, Evidence Hit Rate.
3. **Phase-2 gate:** run JEQ (20) on P1/P2/P3 at a **single K = 5** → 60 outputs; researcher hand-scores all 60; Judge scores the same 60; compute the human–judge **Agreement Rate**.
4. If agreement **≤ 80%**: change rubric and/or swap Judge to `gpt-oss-120b` (still ≠ the Llama answerer) and re-run the check.

## Evaluations
1. The Judge never sees all 20 GQ at once — only the 5 quadrant-matched exemplars — and the Judge has **no search tool**.
2. Citation matching is computed in code, never delegated to the Judge.
3. Agreement Rate clears **> 80%** before Phase 7 is permitted to begin.
4. JEQ never leaks into any prompt; GQ feeds only the Judge.

## Deliverables
1. `async_judge.py` with the four cached per-quadrant prefixes.
2. The deterministic metrics module (citation audit, F1, EM, retrieval metrics).
3. The 60-output validation set hand-scored + judge-scored, with the recorded Agreement Rate (the gate evidence).

---

# Phase 7: Full Benchmark Execution
Run the 900-cell matrix and score every output. Kicks off the instant the gate passes and runs in the background, TPD-paced, at $0.
**Weeks 7–9 onward (background, ~2–3 weeks)**

## Goals
1. Execute **PQ (100) × {P1, P2, P3} × K∈{3, 5, 10} = 900 runs**, each once at `temperature = 0`.
2. Score every run with the validated Judge + deterministic code metrics; flag coincidental correctness via the Citation Audit.
3. Pace the token-heavy answering phase across days; **commit to `results` after each run and resume from the last written row** on restart.
4. Hold the strict-$0 path by default; invoke the paid Developer tier only if the schedule demands compression.

## Evaluations
1. A mid-run crash resumes from the last committed row without re-spending calls or duplicating rows.
2. Throughput stays inside Groq's per-organization TPD/TPM ceilings (no sustained 429 storms).
3. All 900 cells are present in `results` with both judge scores and code metrics; mismatched-citation outputs are downgraded.

## Deliverables
1. A complete, populated `results` table (900 scored runs).
2. The paced execution log (tokens/day, retries, resume points).

---

# Phase 8: Results Consolidation & Analysis Scripts
Turn the raw `results` table into the analysis artefacts the dissertation will draw on. This is the build-side of analysis; the written chapters sit in the reserved write-up tail.
**Weeks 8–10 (overlapping the write-up reservation)**

## Goals
1. Aggregate `results` across the **tri-pillar** framework: retrieval (Precision/Recall/Hit Rate), answer quality (Judge 1–10 primary; F1/EM secondary), efficiency (latency, tokens, index-build cost).
2. Break results down **per quadrant** to expose where each paradigm wins and fails (esp. the semantic-vs-statistical contrast and P3's expected Q3/Q4 degradation).
3. Generate the comparison tables and charts the write-up will reference.

## Evaluations
1. Aggregations are reproducible from `results` alone (no manual data shuffling).
2. The per-quadrant breakdown clearly surfaces the core semantic-vs-statistical-vs-structural story.
3. Outputs are framed with appropriate statistical honesty (single temp-0 run per cell; ~80% gate on 60 samples is a pragmatic check, not strong proof).

## Deliverables
1. Analysis/aggregation scripts run against `results`.
2. Final comparison tables and figures.
3. A results summary feeding directly into the dissertation write-up (reserved for the remaining time within the 10 weeks).
