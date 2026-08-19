# Deep Project Audit — 2026-08-18

Verified against live repo state (code, `benchmark.db`, `git log`, `pytest` run), not against
stale docs. Every number below was re-checked this session; where a doc disagreed with reality,
that's called out explicitly. Superseded by a later audit if state materially changes.

---

## 1. The Idea

**Research question:** which retrieval paradigm — semantic (vector), statistical (BM25), or
structural (summary-tree) — performs best on SEC 10-K financial filings, and where does each
break down?

- **P1 Vector**: `bge-small-en-v1.5` embeddings + `bge-reranker-base` cross-encoder rerank.
- **P2 BM25**: `rank_bm25` (Okapi BM25), custom regex tokenizer (preserves numbers/%/currency, no stemming).
- **P3 Structural**: LlamaIndex `TreeIndex` built once via LLM, traversed at query time with `MockLLM` bound (no LLM call at retrieval).
- Sharpest contrast is semantic vs. statistical; structural is the third paradigm, expected to be weakest on tables.
- Anti-leakage: pipelines see only query + retrieved nodes, never exemplars/ground truth/answer-location hints.
- Anti-self-grading: Generator ≠ Critic model family; Answerer ≠ Judge model family.
- Everything targeted at $0 infra spend, all free-tier or local CPU.

This part of the design is unchanged since the proposal and is not in question — the professor's
"A" grade and "strong report" comment applies to this layer. What follows is what actually got
built against that idea, verified today.

---

## 2. Current State, By Aspect

### 2.1 Data — CORRECTED THIS SESSION

**Corpus is 13 filings, not 18, not 6 companies.** This was the exact mistake flagged and now fixed
in `video_script_checklist.md`.

| | |
|---|---|
| Companies | 5 — AAPL, MSFT, TSLA, JPM, JNJ (**no Walmart**) |
| Filings | AAPL/MSFT/TSLA × FY2023–2025 (3 each) + JPM/JNJ × FY2023–2024 (2 each) = **13** |
| Nodes ingested | 26,050 rows in `benchmark.db.nodes` (verified via live query) |
| Manifest | `project/data/filings_manifest.json` — 13 entries, single source of truth, confirmed unique tickers |

Why 13 and not 18: originally scoped to 18 (6 companies × 3yr incl. Walmart), but only 13 had a
P3 summary-tree built by the time dataset generation was about to start. Rather than pay for 5
more LLM-based tree builds for no research benefit, the corpus was trimmed to the 13 already
built (`deviations.md` #20, 2026-08-11). This is a documented, deliberate scope cut — the
professor's "say the number instead of guessing" note is now answerable precisely: **13**.

`README.md`'s "Benchmark Design" section already states 13/5-companies correctly (line-checked
this session) — the drift was specifically in `video_script_checklist.md`, which I'd built from a
stale `openwiki/quickstart.md` line ("expanded to 6 companies... 18 filings") that itself predates
the trim and was never updated. Flagging `openwiki/quickstart.md` line 71 as stale too — it still
says 18 filings/6 companies.

**Known data-quality issue (documented, not fixed):** LlamaParse table header misalignment — units
caption merged into column-1 header on 31 tables across 5 of the original 9 audited filings
(`issues.md` #1). Neutral to the P1/P2/P3 comparison (affects all pipelines equally, only one
header label, not any data value). Left unfixed by design.

### 2.2 Code — what actually exists right now

Verified via live `find`/`ls` against `project/`, cross-checked against `git log` (most recent
commit: `3980945 Merge branch 'dev' into phase4-dataset-generation`).

| Phase | Modules | State |
|---|---|---|
| 1 — Infra | `llm_client/` (config, llm_factory, groq/nim/openrouter clients), `database_manager.py`, `loop_template.py` | Done |
| 2 — Ingestion | `ingest/fetch_filings.py`, `parse_filing.py`, `node_builder.py`, `parsing_audit.py`, `run_ingestion.py` | Done, 13/13 filings ingested |
| 3 — P3 index build | `pipelines/structural/build_summary_index.py`, `node_convert.py` | Done, 13/13 trees built |
| 4 — Dataset generation | `dataset_generation/` (async_generator, async_critic, search_tool, cross_check, section_grouper, gq_label_export/import, run_dataset_generation.py) | Code done — **and now actually running**, see §2.5 |
| 5 — Retrieval pipelines | `pipelines/vector/` (P1), `pipelines/bm25/` (P2), `pipelines/structural/p3_structural.py` (P3), `pipelines/answerer.py`, `loop_executor.py` | **All three retrievers + answerer + loop executor exist and are tested** — this is newer than the last written status doc (`build_progress.md`, dated 08-11, said P3's retriever "does not exist yet" and answerer/loop_executor "don't exist" — both now false, confirmed by file listing and `tests.md`'s own Phase 5 section) |
| 6 — Judge | `judge/async_judge.py`, `judge/metrics.py`, `judge/numeric_normalizer.py`, root-level `score_gate_outputs.py`, `validation_gate.py` | **Built** (`feat(phase6): Judge build and validation gate` commit) — not yet run against real data |
| 7 — Full benchmark | none yet | **Planning doc only** (`docs/superpowers/plans/` per commit `docs(phase7): add full-benchmark execution implementation plan`) — no `run_benchmark.py` exists |
| 8 — Analysis | none | Not started |

**`README.md` repository-layout section is badly stale** — it still describes a `claude/` folder,
says "Technical build not yet started," and lists P1 as "FAISS / ChromaDB" when the actual build
uses `bge-small` + a local Chroma collection via `build_vector_index.py` (close enough on ChromaDB,
but "not yet started" is flatly wrong given 6 phases are built). Don't quote `README.md`'s Status
section on camera without checking it first — it hasn't been updated in a while.

### 2.3 Tests — VERIFIED LIVE THIS SESSION

Ran `uv run pytest -q -m "not live"` directly, not trusted from a doc:

```
338 passed, 2 deselected, 1 warning in 56.91s
340 tests collected total
```

`resources/research/tests.md` (dated 2026-08-11) says "240 tests collected... 239 pass + 1 skipped"
— **stale by 100 tests**, from before Phase 5/6 test files were added. The live number is **340
collected / 338 passing / 2 live-API smoke tests deselected by default** (these hit real Groq/
OpenRouter endpoints and are intentionally excluded from the default run).

Coverage now spans Phases 1–6: infra, ingestion, P3 build, dataset generation (37 tests, the
largest file), P1/P2/P3 retrieval, the answerer's citation-marker parsing and anti-leakage
guarantees, the loop executor's resumability, and judge metrics (`precision_at_k`, `recall_at_k`,
`token_f1`, `exact_match`, `citation_audit`). Nothing exists yet for Phase 7/8 because those
modules don't exist yet — that's a true gap, not a testing gap.

For the professor's "lack of code testing" note: this is now a genuinely strong section of the
project — 338 green tests is a real, honest thing to show on camera.

### 2.4 API usage, models, providers

Current live routing (`project/llm_client/config.py`, cross-checked against `Guardrails.md`):

| Stage | Model | Provider |
|---|---|---|
| Generator | `nvidia/nemotron-3-super-120b-a12b:free` | OpenRouter |
| Critic | `openai/gpt-oss-20b:free` | OpenRouter |
| P3 index build | `nvidia/nemotron-3-super-120b-a12b` (paid slug, no `:free`) | NVIDIA NIM |
| Answerer | `llama-3.3-70b-versatile` | Groq |
| Judge | `qwen/qwen3.6-27b` | Groq |
| Debug | `llama-3.1-8b-instant` | Groq |

Anti-self-grading invariant holds: Generator (NVIDIA family) ≠ Critic (OpenAI family); Answerer
(Llama) ≠ Judge (Qwen).

**Three providers now, not one** — this is a real, load-bearing deviation from the original "all
on Groq" design, driven by a chain of actual quota walls, not preference:
1. Groq alone couldn't sustain P3's build volume → added NVIDIA NIM (`deviations.md` #7).
2. Groq's `gpt-oss-120b` TPM ceiling (~8K TPM) structurally rejected any filing section over ~8K
   tokens for the Generator → moved Generator to NIM (#23), then to OpenRouter for more
   predictable published limits + a $10 top-up unlocking 1,000 req/day instead of 50 (#24), then
   swapped model twice more as OpenRouter's free-catalogue drifted live under us (#25).
3. Critic then hit Groq's 200K/day token cap once it was the only stage left there → moved to
   OpenRouter too (#26).

**Spec drift found this session:** `Guardrails.md` §2's model table (line 32) still says
`P3 summary-index build (1x) | llama-3.1-8b-instant | Groq free` — this is **two generations
stale**. The real history: `llama-3.1-8b-instant` (original) → `openai/gpt-oss-20b` (deviation
#15, quality reasons) → `nvidia/nemotron-3-super-120b-a12b` via NIM (deviation #7, provider
reasons, current). `Guardrails.md`'s Generator/Critic rows *are* current (correctly show OpenRouter
+ nemotron/gpt-oss-20b); only the P3 row was missed when the table was last edited.

`resources/specs/Budget.md`'s entire model table (lines 21–25) is **more stale still** — it lists
Generator=`gpt-oss-120b`/Groq and Critic=`Qwen3.6-27B`/Groq, i.e. the *original* Guardrails
assignment from before any of deviations #9, #23–26. Its RPM/RPD/TPM/TPD table is the origin of
the TPD-bound reasoning still worth citing conceptually, but the specific model names in it no
longer match what's running. Don't read Budget.md's model table on camera without caveating it.

### 2.5 Dataset generation progress — NOT empty, NOT finished

Checked `benchmark.db` directly this session:

| Table | Rows | Target |
|---|---|---|
| `queries` (PQ) | 75 | 100 |
| `golden_queries` (GQ) | 10 | 20 |
| `judge_validation` (JEQ) | 10 | 20 |
| `results` | 0 | 900 (eventual) |
| `nodes` | 26,050 | (ingestion, complete) |

This contradicts two different stale claims: `build_progress.md` (08-11) says all three query
tables are empty and "the pipeline has never been run end-to-end against live data"; the earlier
`openwiki/quickstart.md`-derived checklist said the same. **Neither is true anymore** — a real run
has produced 95 of 140 target rows (75+10+10) since then. It is genuinely in progress, genuinely
not finished. State this precisely on camera rather than either extreme.

### 2.6 Rate limits (live-verified figures, per spec docs)

- Groq: per-model, per-organization limits (extra keys don't help). `llama-3.3-70b-versatile`
  ~30 RPM / ~1,000 RPD / ~12K TPM / ~100K TPD. `qwen/qwen3.6-27b` ~60 RPM / ~8K TPM (tight axis).
  `llama-3.1-8b-instant` much higher RPD (~14,400).
- NVIDIA NIM: 40 RPM enforced in `nim_client.py`; no published TPM/TPD ceiling.
- OpenRouter: 20 RPM enforced in `openrouter_client.py`; 50 req/day free, or 1,000 req/day after a
  one-time $10 lifetime credit top-up (already done — this is the project's one disclosed,
  non-recurring deviation from the $0 headline, justified in `deviations.md` #24 against
  `Budget.md`'s own precedent for a disclosed paid fallback).
- Concurrency caps in `config.py`: `GROQ_MAX_CONCURRENCY=5`, `NIM_MAX_CONCURRENCY=5`,
  `OPENROUTER_MAX_CONCURRENCY=5` (simultaneous in-flight calls, separate axis from RPM).
- Binding constraint for the eventual full run: Llama 3.3 70B's ~100K TPD for answer generation —
  `Budget.md` estimates ~2–3 weeks of intermittent free-tier running for the full 900-run matrix,
  not 1–2 days.

### 2.7 Bugs found and fixed (13 logged in `bugs.md`, all resolved except one open item)

Highest-severity, most relevant to mention if asked "what went wrong":
1. Reasoning-tuned models returning `content=None` mid-JSON-parse — crashed ~2/3 of live Generator/Critic
   attempts before a `reasoning.effort="low"` fix (2026-08-12).
2. Dataset-generation orchestrator silently excluded JPM/JNJ (9-of-13 hardcode) — fixed by deriving
   from the manifest (2026-08-11) — **this is the same root pattern as the 18-vs-13 filing count
   mistake I made in this checklist**, just one layer deeper in the code instead of in a doc.
3. Real Groq API errors crashed the whole run instead of retrying (wrong exception class caught) — fixed.
4. `LLMFactory`'s retry/semaphore wrapper was silently never applied to any call, project-wide, for
   weeks — a `pydantic`/kwarg-name mismatch discarded it silently. Fixed; all already-completed P3
   builds were unaffected in correctness, only in resilience during the build.
5. Chroma silently dropped 2 real filing nodes on an ID collision with poisoned test data — critical,
   fixed with a post-build verification step that now hard-fails on a count mismatch.
6. P1's embedded text leaked structural metadata (`parent_item_header`, `node_type`,
   `source_page_num`), which would have given P1 an unfair advantage over P2/BM25 in the eventual
   comparison — methodology-invalidating if shipped, caught in review, fixed.
7. GQ hand-labelling accepted out-of-range scores and silently no-op'd on a typo'd query ID — fixed
   with validation + a real migration.
8. P3 build logged zero token cost despite generating real summaries — callback-manager wiring bug,
   fixed (cost audit trail was silently wrong until then).

**Still open (from `build_progress.md`, needs re-verification against current state — that doc is
08-11 and Phase 5/6 have since shipped, so some of this may already be resolved):**
- `async_critic.py`'s tool-calling call-shape bug was flagged as "still open" on 08-11, same class
  of bug as the generator fix. Given the Critic has since been moved to OpenRouter and is actively
  producing GQ/JEQ rows (§2.5), this is very likely fixed or moot now — verify by reading
  `async_critic.py` directly before claiming either way on camera, don't repeat this doc's number
  from memory.
- `dataset_generation_failures.json` has stale test-fixture rows mixed into the real production
  log — cosmetic, deferred, not blocking.

### 2.8 Metrics specified in the professor's feedback categories

Mapping the assessment table's specific line items to current state, so the video can address them
directly rather than in the abstract:

| Feedback category | Grade given | Current state relevant to it |
|---|---|---|
| Data Sources | A* | Now precisely 13 filings/5 companies (was the vague point the professor flagged) |
| Testing | **B** (lowest of any section) | 338 passing tests now exist, spanning 6 phases — this grade predates most of that test suite |
| Development and Implementation Summary | A* | 6 of 8 phases now built; Phase 7 has a written plan |
| Evaluation | A | Tri-pillar metric design (retrieval/answer-quality/efficiency) unchanged, now partly implemented in `judge/metrics.py` |
| Project originality / feasibility | A | Unaffected by implementation status |
| Fluency/Coherence | A | Report-writing quality, not implementation-dependent |

The written justification's two other named weaknesses — literature review not covering financial-
domain RAG specifically, and the filing-count vagueness — are report-writing issues, not
code/data issues; the second is now fully answerable (13, exact).

---

## 3. What Was Done So Far

- Full infra layer: multi-provider LLM client factory (Groq/NIM/OpenRouter), SQLite schema (5
  tables, WAL mode), resumable loop template.
- Full ingestion: 13 filings fetched from SEC EDGAR, parsed via LlamaParse into 26,050 atomic
  `TextNode`s with stable `node_id`s and structural metadata.
- P3's one-time summary-tree build, complete for all 13 filings.
- Dataset-generation pipeline built end-to-end (Generator → Critic → cross-check → 3-way disjoint
  split) and unit-tested; **now running for real**, 95/140 target rows produced so far.
- All three retrieval pipelines (P1 vector, P2 BM25, P3 structural) implemented and unit-tested,
  plus the shared answerer (citation-marker parsing, anti-leakage-verified prompt construction) and
  the loop executor that turns retrieval + answer into a `results` row.
- Judge module built: LLM-as-judge scoring, deterministic metrics (precision/recall@K, token-F1,
  exact match, citation audit), the score-gate comparison logic for the >80% human-agreement gate.
- 340 tests written, 338 passing, covering all of the above.
- 13 real bugs found and fixed via review/live-run testing, each logged with root cause and fix.
- 27 documented deviations from the original spec, each with reasoning — this is itself evidence
  of rigorous, disclosed engineering process worth mentioning on camera.

## 4. What Needs To Be Done

1. **Finish the Phase 4 dataset-generation run** — 45 more PQ, 10 more GQ, 10 more JEQ needed to
   hit the 140 target. Re-verify `async_critic.py`'s tool-calling shape is genuinely fixed before
   trusting a long unattended run (§2.7).
2. **Run the loop executor for real** — `results` table is at 0; nothing has gone through
   retrieval → answer → stored row yet, even though all the code exists and is unit-tested.
3. **Run the Phase 6 judge validation gate against real data** — the 60-output JEQ×3-pipelines
   check, human-scored vs. judge-scored, must clear >80% agreement before the full run is trusted.
   Not yet attempted against real generated data.
4. **Build Phase 7** — the full 900-run benchmark executor. A plan exists; no code yet.
5. **Build Phase 8** — analysis/aggregation/plotting. Not started, not planned yet either.
6. **Fix the stale docs found this session** (lower priority, doesn't block research):
   - `Guardrails.md` §2's P3-build model row (says `llama-3.1-8b-instant`/Groq, should say
     `nvidia/nemotron-3-super-120b-a12b`/NIM).
   - `Budget.md`'s entire model-assignment table (three generations behind current routing).
   - `README.md`'s Status section and repo-layout block (says build hasn't started).
   - `openwiki/quickstart.md` line 71 (still says 18 filings/6 companies).
   - `resources/research/build_progress.md` and `tests.md` (both dated 08-11, materially stale on
     Phase 5/6 status and test counts — worth a refreshed snapshot before relying on either again).

## 5. What's Left (in one line)

Phases 1–3 fully done. Phase 4 ~68% done by row count, running. Phase 5–6 code-complete,
zero real runs yet. Phase 7–8 not built. The single biggest unblock is running the loop executor
+ judge gate against whatever data Phase 4 has produced so far — everything downstream is coded
and tested but has never touched real output.
