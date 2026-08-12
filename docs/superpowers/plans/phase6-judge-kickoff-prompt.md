# Phase 6 kickoff prompt — paste into new Claude Code session

Working directory for this session: `/Users/ojaswi/Projects/ragbench-phase6` (a git worktree, branch `dev`, already synced to the tip of `phase4-dataset-generation`/`phase5-pipeline-implementation` as of 2026-08-12). This is a real, separate checkout of the same repo — commits here land on `dev`. Do not push without asking me first.

---

## Prompt to paste

I'm building **Phase 6 (Judge Build & Validation Gate)** of a COMP702 M.Sc. dissertation project: a benchmark comparing three RAG retrieval paradigms (vector / BM25 / structural-summary-tree) against SEC 10-K filings. Phases 1–5 are done and merged into this `dev` branch: ingestion, all three pipelines (P1/P2/P3), a shared answerer, and `loop_executor.py` which writes benchmark cells into a `results` table. Phase 4 (dataset generation) is running live in a sibling worktree right now, filling `queries`/`golden_queries`/`judge_validation` — don't assume those tables are fully populated yet; build against fixtures first, real-data gate run comes later.

**Read `CLAUDE.md` in the repo root first** — it governs everything: `resources/` is read-only steering, don't touch it unless told; British English/no em-dashes apply only to `resources/artifacts/` documents, not code; no dev-history comments/docstrings in code (put narrative in commit messages, not `# fixed X` comments); use `monitor` (`/monitor:record`) after real code changes; log new bugs to `resources/research/bugs.md`, deviations from spec to `resources/research/deviations.md`.

### What Phase 6 is

Read these specs in full before writing anything — they are binding, not advisory:
1. `resources/specs/Architecture.md` §3.2 (full DDL for `judge_validation` and `results`), §4.1 (`judge/metrics.py` function signatures), §4.2 (citation marker convention), §4.3 (numeric normalization), §4.5(b) (sequence diagram for the validation gate)
2. `resources/specs/Guardrails.md` §2 (model routing), §3 (anti-leakage), §4 (Judge few-shot filtering + the hard gate), §6 (schema), §7 (throttle requirement)
3. `resources/specs/Phase Plan.md`, "Phase 6" section (goals/evaluations/deliverables)

Condensed for convenience, but verify against the specs above — they're authoritative if anything here drifts:

**Schema (`database_manager.py` already implements `upsert_result`, `get_completed_keys`, `get_golden_queries`, `get_queries` — reuse these, don't reinvent):**
```sql
CREATE TABLE judge_validation (
    query_id TEXT PRIMARY KEY, quadrant TEXT NOT NULL CHECK (quadrant IN
        ('Q1_Direct_Text','Q2_Implicit_Text','Q3_Direct_Table','Q4_Implicit_Table')),
    query_text TEXT NOT NULL, ground_truth_answer TEXT NOT NULL,
    gt_citations TEXT NOT NULL,  -- JSON array of node_id
    document_id TEXT NOT NULL
    -- no pipeline_output/human_score/judge_score here -- those live in `results`
);

CREATE TABLE results (
    result_id TEXT PRIMARY KEY,
    source_set TEXT NOT NULL CHECK (source_set IN ('PQ','JEQ')),
    query_id TEXT NOT NULL,
    pipeline TEXT NOT NULL CHECK (pipeline IN ('P1_vector','P2_bm25','P3_structural')),
    k_value INTEGER NOT NULL CHECK (k_value IN (3,5,10)),
    retrieved_node_ids TEXT NOT NULL,  -- JSON array
    pipeline_output TEXT, cited_node_ids TEXT,  -- JSON array
    precision_at_k REAL, recall_at_k REAL,
    evidence_hit INTEGER CHECK (evidence_hit IN (0,1)),
    citation_match INTEGER CHECK (citation_match IN (0,1)),
    token_f1 REAL,
    exact_match INTEGER CHECK (exact_match IN (0,1)),  -- NULL for Q2/Q4
    judge_score INTEGER CHECK (judge_score BETWEEN 1 AND 10),
    human_score INTEGER CHECK (human_score BETWEEN 1 AND 10),  -- only source_set='JEQ'
    latency_sec REAL, input_tokens INTEGER, output_tokens INTEGER,
    UNIQUE (source_set, query_id, pipeline, k_value)
);
```
`golden_queries` already has `query_id, quadrant, query_text, ground_truth_answer, gt_citations, example_output, human_score (0-100), human_reasoning, is_good, document_id` — the 20 GQ teaching exemplars, hand-labelled at end of Phase 4 (may still be in progress).

**Model routing (from `llm_client/config.py` `MODEL_ROUTING`, do not change without a deviations.md entry):**
- Judge: `qwen/qwen3.6-27b` on Groq, **no search tool** — it already gets ground truth + citations, just scores against them.
- Judge ≠ Answerer (`llama-3.3-70b-versatile`) — different families, anti-self-grading invariant. Never violate this.

### Deliverables (build in this order, TDD, fixture-driven — don't need real DB rows to start)

1. **`judge/numeric_normalizer.py`** — `normalize_numeric(text: str) -> Decimal | None`. Strips currency symbols (`$`, `£`, `€`) and thousands separators, expands suffix multipliers (K/M/B/T, "thousand"/"million"/"billion"/"trillion"), returns `Decimal` or `None` if not numeric.

2. **`judge/metrics.py`** — pure, deterministic, no LLM calls:
   ```python
   def citation_audit(cited_node_ids: list[str], gt_citations: list[str]) -> bool: ...  # cited ⊆ gt
   def precision_at_k(retrieved: list[str], gt: list[str], k: int) -> float: ...
   def recall_at_k(retrieved: list[str], gt: list[str]) -> float: ...
   def token_f1(output_text: str, gt_text: str) -> float: ...
   def exact_match(output_text: str, gt_text: str, *, numeric_tolerance: float = 0.01) -> bool | None: ...
       # None for Q2/Q4 quadrants (caller passes quadrant, EM is Q1/Q3-only).
       # Try normalize_numeric() on both sides; if both parse, compare within
       # relative epsilon. If either fails to parse, fall back to normalized-
       # string comparison (lowercased, punctuation-stripped).
   ```
   Citation parsing convention already implemented in `pipelines/answerer.py::parse_citations` — `pipeline_output` contains `[[node:<node_id>]]` markers, kept in the text (not stripped). Reuse that regex/convention, don't reinvent.

3. **`judge/async_judge.py`** — the LLM Judge itself. Follow the async-client pattern already used in `pipelines/answerer.py` (`Answerer` class) and `dataset_generation/async_critic.py` for retry/semaphore-wrapped calls via `LLMFactory.get_client_for_stage("judge")` (`llm_client/llm_factory.py:110`). Core behaviour, per Guardrails §4a:
   - For a given `results` row (JEQ), read its quadrant, then query `golden_queries WHERE quadrant = :quadrant` to get **exactly the 5 matching GQ exemplars** (never all 20).
   - Build one of **four** cacheable prompt prefixes (rubric + 5 quadrant exemplars) — reuse the same prefix across every JEQ row of that quadrant so provider-side prompt caching applies.
   - No search tool. Score `judge_score` (1-10) against the row's `pipeline_output`, ground truth, and citations.
   - `temperature = 0` (Guardrails, every LLM call at temp 0).

4. **`validation_gate.py`** — orchestrates running the 20 JEQ through P1/P2/P3 at **K=5 only** via the existing `loop_executor.py::run_cell` (reuse it, don't duplicate retrieval/answering logic) → 60 `results` rows with `source_set='JEQ'`. Must respect `LOCAL_TEST_THROTTLE`/`apply_throttle()` from `loop_template.py` (Guardrails §7 — every loop script needs this hardcoded throttle boolean; copy the exact pattern already used in `loop_executor.py`).

5. **`score_gate_outputs.py`** — two responsibilities per the Architecture §4.5(b) sequence diagram:
   - Prompt the researcher (me) for a `human_score` per one of the 60 rows, `UPDATE results SET human_score=...`.
   - After both `human_score` and `judge_score` are populated for all 60, compute the **Agreement Rate** (define the comparison method explicitly in code/docstring — e.g. exact match on a 1-10 scale, or within ±1 — and justify the choice; this number is dissertation evidence, be precise) across the 60 `source_set='JEQ'` rows.
   - Gate: **Agreement Rate > 80%** required before Phase 7 (full 900-run benchmark) may start. If not met, that's a decision point for me (rubric change or Judge model swap to `gpt-oss-120b`, still ≠ Llama answerer) — don't silently retry, surface the result and stop.

### Non-negotiables (Guardrails, will get flagged in review if violated)
- Citation matching (`citation_audit`) is deterministic code — never delegate to the Judge.
- Judge never sees all 20 GQ at once, only the 5 quadrant-matched ones.
- JEQ rows are never injected as exemplars anywhere (not the Judge's few-shot, not the pipelines).
- Every loop script gets the hardcoded `LOCAL_TEST_THROTTLE` pattern from `loop_template.py`.
- Judge stays `qwen/qwen3.6-27b` (or `gpt-oss-120b` if the gate fails and you swap it) — never the same family as the Llama-3.3-70B answerer.

### Testing conventions
Follow the existing test style — see `tests/test_answerer.py` and `tests/test_loop_executor.py` for the pattern: mock the raw LLM client (`AsyncMock` on `chat.completions.create`), fixture-driven `results`/`golden_queries` rows, no live API calls in the default suite (live-smoke tests are separate, named `test_*_live_smoke.py`, skipped by default — see `tests/test_async_critic_live_smoke.py` for the pattern). Run `uv run pytest -q` after each module; full suite must stay green (243 passed, 1 skipped as of this sync).

### Start by
1. Confirming you've read `CLAUDE.md`, the three specs above, and the existing `database_manager.py`, `llm_client/llm_factory.py`, `pipelines/answerer.py`, `loop_executor.py`, `loop_template.py` files (all already exist, reuse their patterns/functions, don't duplicate).
2. Writing `judge/numeric_normalizer.py` + tests first (smallest, no dependencies), TDD style.
3. Then `judge/metrics.py` + tests.
4. Then `judge/async_judge.py` + tests (mocked LLM).
5. Then `validation_gate.py` + `score_gate_outputs.py`.
6. Stop and report before running anything against the real `benchmark.db` — check with me first, since that DB is shared state and Phase 4 may still be writing to a copy of it elsewhere.

Ask me anything that's ambiguous rather than guessing — this feeds a dissertation, precision matters more than speed.
