# Graph Report - rag-techniques  (2026-09-09)

## Corpus Check
- 277 files · ~3,323,772 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3239 nodes · 5095 edges · 302 communities (152 shown, 150 thin omitted)
- Extraction: 80% EXTRACTED · 20% INFERRED · 0% AMBIGUOUS · INFERRED: 1005 edges (avg confidence: 0.74)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `dc122e31`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Schema, Quota and Judge Gating
- Agent Steering and Document Style
- Proposal Compliance and Benchmark Design
- Pipeline Build Phases and Metrics
- Research Question and Literature Base
- Guardrails and Model Routing
- Benchmark Execution and Citation Audit
- Zero-Cost Storage and Specs Index
- Filing HTML and XBRL Markup
- Interest Rate Sensitivity Table
- Spec Document Set
- Corpus Scope and Timeline
- Phase Plan.md
- ally.b2f86d8b36422ca86a9f.js
- ally.b2f86d8b36422ca86a9f.js
- o
- f
- jQueryPrivate.js
- test_run_dataset_generation.py
- jQueryPrivate.js
- compare.py
- launch.js
- Guardrails.md
- launch.js
- test_score_gate_outputs.py
- profile.py
- logger.py
- RAG Techniques — COMP702 M.Sc. Dissertation
- t
- test_metrics.py
- The code demo, explained
- e
- loop_executor.py
- atomic_search_widget.js
- Anti-Leakage Disjoint Query Sets
- Anti-Self-Grading Invariant
- British English and Simple Punctuation Rule
- COMP702 M.Sc. Dissertation Project
- Post-build .docx Quarantine Clearing
- graphify Knowledge Graph Workflow
- Judge >80% Human-Agreement Gate
- LOCAL_TEST_THROTTLE Loop Safety Flag
- Native Word/PowerPoint Elements Only
- P2 Statistical Purity Constraint
- P3 Index Build Model (llama-3.1-8b-instant)
- PDF Verification via LibreOffice and PyMuPDF
- resources/ Steering Layer
- Resumable results UNIQUE Constraint
- Pipeline Answerer Role (Llama 3.3 70B)
- Critic Role (Qwen3-32b with search)
- Generator Role (openai/gpt-oss-120b)
- Judge Role (Qwen3-32b, no search)
- resources/specs/Architecture.md
- resources/specs/Budget.md
- resources/specs/Guardrails.md
- resources/specs/Phase Plan.md
- resources/specs/Project Idea.md
- Specs Reading Order
- SQLite aiosqlite WAL Storage
- src/ Project Code Folder
- Temperature 0, Single-Sample Determinism
- Zero-Cost Infrastructure Constraint
- test_async_judge.py
- exact_match
- rag-techniques-benchmark
- run_dataset_generation.py
- normalize_numeric
- 900-Run Full Benchmark
- 140-Query Benchmark Design (100 PQ / 20 GQ / 20 JEQ)
- LLM-as-Judge Evaluation Method
- P1 — Semantic Vector Pipeline (FAISS/ChromaDB)
- P2 — Statistical BM25 Pipeline (rank_bm25)
- P3 — Structural Summary-Tree Pipeline (LlamaIndex SummaryIndex)
- README — RAG Techniques Project
- Apple Inc. SEC 10-K Dataset (EDGAR XBRL)
- Auxiliary Evaluation Colours (Success/Error)
- Categorical Chart Palette (5+ series)
- Component Colour Mapping (Word/PPT/Diagrams/Tables)
- Diverging Gold-to-Blue Ramp
- Reserved Gold Accent
- Blue-Tinted Neutral Scale
- Oxford Ink Brand Palette
- Primary Blue Scale (Blue 50–950)
- Sequential Single-Hue Ramp
- 60/30/10 Usage Discipline
- Calibri Structural/Tabular Font
- Consolas Monospace Font
- Garamond Body/Reference Font
- No-Split Visual Elements Rule
- Paragraph and Layout Rules
- artifacts/Proposal_v1.0.0.docx
- PowerPoint Slide Type Scale
- COMP702 Typography System
- Word/PDF Size Scale (A4, 2.5cm margins)
- [[node:<node_id>]] Citation Marker Convention
- database_manager.py
- golden_queries table (20 GQ)
- groq_client.py
- JSON-in-SQLite List Column Convention
- judge_validation table (20 JEQ)
- LlamaIndex as Common Backbone
- loop_executor.py
- nodes table
- judge/numeric_normalizer.py
- Per-Document Retrieval Scope
- queries table (100 PQ)
- results table (960 rows, PQ + JEQ)
- UNIQUE(source_set, query_id, pipeline, k_value) Resume Key
- Retriever ABC (pipelines/base.py)
- source_set Discriminator Column
- Five-Table SQLite Schema (DDL)
- Revised 10-Week Timeline
- Groq Free Tier
- LlamaParse Free Tier (Cost-effective)
- Local CPU Compute (bge models, rank_bm25)
- Worst-Case Paid Fallback (Developer Tier)
- Prompt Caching of Static Judge Prefix
- TPD (Tokens-Per-Day) as Binding Constraint
- Zero-Spend Operating Model ($0.00)
- Anti-Leakage Rules (disjoint sets, no exemplars to pipelines)
- Concurrency & Rate-Limiting Enforcement (tenacity, Semaphore<=5)
- Crash-Resume State Persistence
- Determinism (temperature = 0, single run per cell)
- Dynamic Quadrant-Matched Few-Shot Filtering
- Absolute Infrastructure Ban (no per-hour / scale-to-non-zero)
- Judge Validation Gate (>80% Agreement Rate)
- KeywordTableIndex Ban (P2 must stay statistical)
- LOCAL_TEST_THROTTLE Safety Brake
- Mandated Model Assignment Map
- No Metadata Pre-Filter for P1
- P3 One-Time LLM Summary Build Exception
- Role Separation (Generator != Critic, Answerer != Judge)
- SQLite WAL Mode for Concurrent Writes
- Two Manual Human-in-the-Loop Bottlenecks
- Phase 1 — Environment, Infrastructure & Cost Guardrails
- Phase 2 — Ingestion & Parsing Pipeline
- Phase 3 — P3 Summary-Index Build (one-time)
- Phase 4 — Dataset Generation & Adversarial Verification
- Phase 5 — Pipeline Implementation (P1/P2/P3)
- Phase 6 — Judge Build & Validation Gate
- Phase 7 — Full Benchmark Execution (900 runs)
- Phase 8 — Results Consolidation & Analysis
- 140-Query Benchmark Dataset (PQ/GQ/JEQ)
- 900-Run Combinatorial Benchmark Matrix
- Academic Rigor & Methodological Principles
- Pillar 2 — Answer-Quality Metrics (Judge 1-10, Token-F1, EM)
- Atomic Table Preservation (LlamaParse markdown)
- node_id as Canonical Evidence Anchor
- Citation Audit (deterministic, code-only)
- Coincidental Correctness Trap
- Custom Regex Tokenizer for BM25
- Pillar 3 — Efficiency Metrics (latency, tokens, index-build cost)
- Four Query Quadrants (Q1-Q4)
- Future-Scope Pipelines P4/P5/P6
- Generator-Critic Adversarial Verification
- LlamaIndex Version Drift Risk
- P1 — Vector RAG (semantic, bge + reranker)
- P2 — Keyword RAG (Okapi BM25, rank_bm25)
- P3 — Structural RAG (SummaryIndex traversal)
- Randomised 20-Section Parsing Audit
- Per-Section Chunked Generation (128K context cap)
- Three-Paradigm RAG Comparison Research Question
- Pillar 1 — Retrieval Metrics (Precision@K, Recall@K, Evidence Hit Rate)
- Tri-Pillar Evaluation Framework
- async_judge.py
- Docstring and Comment Simplification Implementation Plan
- _retry_decorator
- Project Overview and FAQ
- t
- atomic_search_widget.js
- l
- Answerer
- test_database_manager_judge.py
- o
- _node
- loader.js
- loader.js
- P2BM25Retriever
- build_pools
- react-entry-a5fb72e8fa941b39.js
- react-entry-a5fb72e8fa941b39.js
- Z
- test_validation_gate.py
- script.js
- init
- init
- Phase 3 — P3 Summary-Tree Build Cost
- LLMFactory
- test_groq_client_backoff.py
- qe
- test_main_with_empty_document_ids_tuple_stays_empty_not_all_filings
- search_filing_nodes
- test_node_builder.py
- Working in this repo
- 4. Implementation Guardrails (Binding)
- Quickstart
- fetch_filings.py
- Guardrails are binding, not advisory
- Monitor Skill
- quickstart.md
- MSFT_2023.md
- dependencies
- Note 7 – Interest income and interest expense
- __init__.py
- MSFT_2025.md
- MSFT_2025.md
- TSLA_2024.md
- TSLA_2024.md
- JNJ_2024.md
- JNJ_2023.md
- JNJ_2023.md
- JNJ_2025.md
- JNJ_2025.md
- TSLA_2025.md
- WMT_2023.md
- WMT_2024.md
- WMT_2024.md
- WMT_2025.md
- AAPL_2023.md
- AAPL_2023.md
- AAPL_2024.md
- AAPL_2024.md
- AAPL_2025.md
- AAPL_2025.md
- P1VectorRetriever
- Deviations from Original Proposed Idea
- FastEmbedReranker
- build_vector_index.py
- tokenize
- File Structure
- test_build_bm25_index.py
- test_build_vector_index.py
- build_bm25_index.py
- Format
- test_run_dataset_generation.py
- test_cross_check.py
- run_dataset_generation.py
- config.py
- test_gq_labeling.py
- Challenges Encountered
- Global Constraints
- test_build_summary_index.py
- Research Issues Log
- Global Constraints
- group_sections
- Note 7 – Interest income and interest expense
- Deferred Items Log
- Monitor Skill
- Phase 2 — Human Action Report
- Challenges Encountered
- Research Issues Log
- opencode.json
- opencode.json
- dependencies
- conftest.py
- groq_limits.md
- backup_data.sh
- reload_backup.sh
- snippets.md
- directory-structure.md

## God Nodes (most connected - your core abstractions)
1. `o()` - 60 edges
2. `o()` - 60 edges
3. `t()` - 57 edges
4. `t()` - 57 edges
5. `l()` - 50 edges
6. `l()` - 50 edges
7. `e()` - 40 edges
8. `e()` - 40 edges
9. `Deviations from Original Proposed Idea` - 29 edges
10. `f()` - 27 edges

## Surprising Connections (you probably didn't know these)
- `test_format_underfill_summary_marks_only_below_target_quadrants()` --calls--> `format_underfill_summary()`  [INFERRED]
  project/tests/test_run_dataset_generation.py → project/dataset_generation/run_dataset_generation.py
- `815287()` --indirect_call--> `F()`  [INFERRED]
  resources/assignments/2nd Assessment_ Project Video and Q&A Sessions (15%)_ 202526-COMP702 - MSc Project_files/react-entry-a5fb72e8fa941b39.js → resources/assignments/2nd Assessment_ Project Video and Q&A Sessions (15%)_ 202526-COMP702 - MSc Project_files/ally.b2f86d8b36422ca86a9f.js
- `822551()` --indirect_call--> `E()`  [INFERRED]
  resources/assignments/2nd Assessment_ Project Video and Q&A Sessions (15%)_ 202526-COMP702 - MSc Project_files/react-entry-a5fb72e8fa941b39.js → resources/assignments/2nd Assessment_ Project Video and Q&A Sessions (15%)_ 202526-COMP702 - MSc Project_files/atomic_search_widget.js
- `152328()` --indirect_call--> `o()`  [INFERRED]
  resources/assignments/Marking Guidelines_ 202526-COMP702 - MSc Project_files/main-entry-1df6e4f76b61ffdd.js → resources/assignments/Marking Guidelines_ 202526-COMP702 - MSc Project_files/ally.b2f86d8b36422ca86a9f.js
- `199099()` --indirect_call--> `o()`  [INFERRED]
  resources/assignments/Marking Guidelines_ 202526-COMP702 - MSc Project_files/main-entry-1df6e4f76b61ffdd.js → resources/assignments/Marking Guidelines_ 202526-COMP702 - MSc Project_files/ally.b2f86d8b36422ca86a9f.js

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three retrieval paradigms share one answerer and one judge** — resources_artifacts_proposal_v1_0_0_p1_vector_pipeline, resources_artifacts_proposal_v1_0_0_p2_bm25_pipeline, resources_artifacts_proposal_v1_0_0_p3_structural_pipeline, resources_artifacts_proposal_v1_0_0_shared_answerer, resources_artifacts_proposal_v1_0_0_llm_judge [EXTRACTED 1.00]
- **Zero-spend quota safety pattern (throttle, WAL resume, disjoint sets, Groq free tier)** — resources_artifacts_proposal_v1_0_0_groq_free_tier, resources_artifacts_proposal_v1_0_0_local_throttle, resources_artifacts_proposal_v1_0_0_sqlite_wal_store, resources_artifacts_proposal_v1_0_0_risk_management_plan [INFERRED 0.85]
- **Guidelines and template constrain the submitted proposal** — resources_docs_proposalguidelines_required_structure, resources_docs_proposaltemplate_section_skeleton, resources_artifacts_proposal_v1_0_0_document, resources_artifacts_projectproposal_document [INFERRED 0.85]

## Communities (302 total, 150 thin omitted)

### Community 2 - "Proposal Compliance and Benchmark Design"
Cohesion: 0.05
Nodes (49): ProjectProposal (earlier draft of the COMP702 proposal), Draft Development and Implementation Summary (§4), BCS Project Criteria Mapping, 140-Query Human-Anchored Benchmark, Chen et al. (2021) FinQA Numerical Reasoning over Financial Data, Citation Audit (detects coincidentally-correct answers), Disjoint Query Sets PQ/GQ/JEQ (100/20/20), Design and Specification Proposal v1.0.0 (COMP702) (+41 more)

### Community 4 - "Research Question and Literature Base"
Cohesion: 0.18
Nodes (13): Encoding, chunk_section(), _get_encoding(), _log_oversized_node_skipped(), Logs the rare case where a single node, almost always one enormous     table, ex, Splits a group_sections() section into one or more Generator-sized     chunks, e, `n` single-token words. tiktoken's cl100k_base encoding tokenizes the bare     w, Naive greedy packing would close the chunk right before n2 (the     6-token text (+5 more)

### Community 5 - "Guardrails and Model Routing"
Cohesion: 0.50
Nodes (7): _download_bytes(), fetch_filing(), _find_10k(), _get_json(), _headers(), Downloads SEC 10-K filings, resolving filing URLs from SEC EDGAR's public JSON A, resolve_cik()

### Community 8 - "Filing HTML and XBRL Markup"
Cohesion: 0.28
Nodes (9): dei:EntityPublicFloat Fact, Inline Style and Entity Noise in Filing HTML, Inline XBRL (ix:nonFraction) Tagging, Apple 10-K Paragraph HTML Sample, Colspan Spacer-Cell Table Layout, Interest Rate Sensitivity Disclosure, SEC 10-K Filing Source Format, Apple 10-K Interest Rate Sensitivity Table HTML Sample (+1 more)

### Community 9 - "Interest Rate Sensitivity Table"
Cohesion: 0.38
Nodes (7): Apple 10-K Interest Rate Sensitivity Table Sample, Hypothetical 100 Basis Point Rate Increase, All Tenors, Interest Rate Sensitivity Disclosure, Investment Portfolio (Decline in Fair Value), SEC 10-K Tabular Financial Data, Table Retrieval Challenge for RAG Pipelines, Term Debt (Increase in Annual Interest Expense)

### Community 10 - "Spec Document Set"
Cohesion: 0.39
Nodes (6): _is_cache_fresh(), parse_filing(), Parses raw filings into clean Markdown via LlamaParse, using the cost-effective, test_parse_filing_calls_llamaparse_and_caches(), test_parse_filing_reparses_if_cache_older_than_48h(), test_parse_filing_skips_reparse_within_48h()

### Community 12 - "Phase Plan.md"
Cohesion: 0.00
Nodes (35): 102657(), 122842(), 152328(), 155769(), 168396(), 199099(), 245339(), 247767() (+27 more)

### Community 15 - "ally.b2f86d8b36422ca86a9f.js"
Cohesion: 0.08
Nodes (47): Ai(), an(), bn(), Bt(), dn(), ei(), et(), fn() (+39 more)

### Community 16 - "ally.b2f86d8b36422ca86a9f.js"
Cohesion: 0.08
Nodes (46): Ai(), an(), bn(), Bt(), dn(), ei(), et(), fn() (+38 more)

### Community 17 - "o"
Cohesion: 0.13
Nodes (52): A(), b(), C(), D(), F(), H(), ii(), j() (+44 more)

### Community 18 - "f"
Cohesion: 0.11
Nodes (51): A(), b(), C(), D(), F(), H(), ii(), L() (+43 more)

### Community 19 - "jQueryPrivate.js"
Cohesion: 0.07
Nodes (35): P(), A(), at(), b(), be(), ce(), e(), Ee() (+27 more)

### Community 20 - "test_run_dataset_generation.py"
Cohesion: 0.05
Nodes (42): next_target(), First still-unfilled (table, quadrant) slot, searched quadrant-major     then ta, _empty_counts(), _isolate_progress_log(), Attempt 1 is rejected via a citation mismatch (Critic cites an     unrelated nod, Simulates process A having already committed 2 accepted queries into     (querie, main() calls _configure_logging() on every entry; a process that (in     theory), Guards the unaffected case: document_ids=None (or omitted entirely)     must sti (+34 more)

### Community 21 - "jQueryPrivate.js"
Cohesion: 0.07
Nodes (32): P(), A(), at(), b(), be(), ce(), e(), Ee() (+24 more)

### Community 22 - "compare.py"
Cohesion: 0.07
Nodes (35): AST, Exception, aggregate(), build_retrievers(), _gt_list(), load_demo_queries(), Runs one query through all three retrieval paradigms and scores the overlap.  On, One query per quadrant, lowest query_id first so the pick is stable. (+27 more)

### Community 23 - "launch.js"
Cohesion: 0.13
Nodes (36): clearSessionStorage(), fetchAllPages(), getActiveCanvasAccount(), getCourseId(), getCSRFToken(), getCurrentCanvasLocale(), getCurrentCanvasUserId(), getEesyServerURL() (+28 more)

### Community 24 - "Guardrails.md"
Cohesion: 0.14
Nodes (12): 1. Absolute Infrastructure Ban: No Per-Hour or Scale-to-Non-Zero Infrastructure, 2. Model Routing Matrix and Local Compute (per-stage LLM assignment), 3. Anti-Leakage: What Each Model May and May Not See, 4. Judge Few-Shot Filtering and the Mandatory Validation Gate, 4a. Dynamic few-shot filtering, 4b. The judge-validation gate (hard prerequisite for the full run), 5. Concurrency and Rate-Limiting Enforcement, 6. Relational Data Management and State Persistence (+4 more)

### Community 25 - "launch.js"
Cohesion: 0.13
Nodes (36): clearSessionStorage(), fetchAllPages(), getActiveCanvasAccount(), getCourseId(), getCSRFToken(), getCurrentCanvasLocale(), getCurrentCanvasUserId(), getEesyServerURL() (+28 more)

### Community 26 - "test_score_gate_outputs.py"
Cohesion: 0.09
Nodes (28): compute_agreement_rate(), _parse_args(), prompt_human_scores(), Namespace, Human scoring and the Judge validation gate.  Collects a human_score for each of, Prompt for any missing human scores, then compute and report the gate., True when the two 1-10 scores agree within the tolerance band on 0-100., Agreement Rate and gate verdict over rows carrying both scores.      Every row m (+20 more)

### Community 28 - "logger.py"
Cohesion: 0.13
Nodes (14): 10. P3 build logged zero token cost despite generating real summaries (2026-08-04), 11. LLM temperature silently fell back to 0.1, not the mandated 0 (2026-08-04), 12. Empty filing-list argument was indistinguishable from "not provided" (2026-08-04), 13. No duplicate-question check let near-identical questions into the benchmark set (2026-08-04), 1. Reasoning-tuned models could return `content=None`, crashing `json.loads()` in Generator and Critic (2026-08-12), 2. Dataset-generation orchestrator only ever saw 9 of the 13 in-scope filings (2026-08-11), 3. Real Groq API failures crashed the whole dataset-generation run instead of being retried (2026-08-11), 4. LLMFactory's retry/backoff wrapper was silently never applied (2026-08-11) (+6 more)

### Community 29 - "RAG Techniques — COMP702 M.Sc. Dissertation"
Cohesion: 0.06
Nodes (33): 0. Decisions Carried Over From the Scoping Discussion, 10. Consolidated Dependency Manifest, 11. Open Items / Recommendations, 1. Design Review: Issues Found and Resolved, 2.1 Component View, 2.2 Deployment View, 2.3 Data-Flow Summary, 2. High-Level Design (HLD) (+25 more)

### Community 30 - "t"
Cohesion: 0.21
Nodes (33): ae(), at(), be(), ce(), de(), e(), ee(), fe() (+25 more)

### Community 31 - "test_metrics.py"
Cohesion: 0.09
Nodes (31): citation_audit(), precision_at_k(), True when every cited node id is one of the ground-truth citations.      An empt, Ground-truth nodes among the top-k retrieved, divided by k.      The denominator, Fraction of ground-truth nodes that appear anywhere in retrieved.      No k argu, SQuAD-style token-overlap F1 between the answer and the ground truth.      Multi, recall_at_k(), token_f1() (+23 more)

### Community 32 - "The code demo, explained"
Cohesion: 0.07
Nodes (28): 10. Commands, 11. File map, 1. The short version, 2. The whole system, end to end, 3. What the demo does, step by step, 4. The three pipelines in plain terms, 5. How the scores are worked out, 6. Reading the output on screen (+20 more)

### Community 33 - "e"
Cohesion: 0.26
Nodes (28): ae(), be(), ce(), de(), e(), ee(), fe(), ge() (+20 more)

### Community 34 - "loop_executor.py"
Cohesion: 0.10
Nodes (20): ABC, build_cells(), build_retrievers(), main(), _parse_args(), Namespace, Runs a single benchmark cell, one (source_set, query_id, pipeline, k_value) run,, Construct only the requested retrievers, importing each module     lazily so an (+12 more)

### Community 35 - "atomic_search_widget.js"
Cohesion: 0.13
Nodes (23): ct(), N(), Qt(), connectedCallback(), ee(), G(), H(), k() (+15 more)

### Community 64 - "test_async_judge.py"
Cohesion: 0.14
Nodes (24): compute_deterministic_metrics(), parse_judge_score(), Computes the code-computed metric columns for one gate row (no LLM).      eviden, Pull a 1-10 integer out of the Judge's reply, clamped into range.      Prefers t, _exemplar(), _fake_judge_client(), OpenAILike, async_judge: quadrant-filtered few-shot, no search tool, folded metrics.  The Ju (+16 more)

### Community 65 - "exact_match"
Cohesion: 0.13
Nodes (23): _contains_subsequence(), exact_match(), Decimal, Deterministic, LLM-free scoring metrics for a single results row.  Citation matc, Relative comparison so notation-equal figures match within epsilon.      The gap, True when `needle` appears as a contiguous run of tokens in `haystack`., Whether the ground-truth answer can be found inside the model output.      Retur, Lowercased word tokens, citation markers and punctuation removed. (+15 more)

### Community 67 - "run_dataset_generation.py"
Cohesion: 0.14
Nodes (23): _accept_query(), append_failure_log(), _attempt_fill(), _configure_logging(), format_underfill_summary(), _get_all_filings(), __getattr__(), _load_all_filings() (+15 more)

### Community 68 - "normalize_numeric"
Cohesion: 0.15
Nodes (21): normalize_numeric(), Decimal, Reduces a financial figure written as free text to a single Decimal.  "$394.3B", Return (numeric core, power-of-ten exponent) after peeling one suffix.      Word, _split_multiplier(), normalize_numeric: currency and separator stripping, suffix expansion.  Exact Ma, The two spellings collapse to one value., test_case_insensitive_suffix() (+13 more)

### Community 166 - "async_judge.py"
Cohesion: 0.13
Nodes (17): build_prefix(), _build_target_message(), _format_exemplar(), Judge, judge_jeq_rows(), Scores each JEQ gate output 1-10 against its ground truth and writes the determi, Wraps the Qwen judge client; enforces the fixed model and temperature.      The, Scores every JEQ gate row: deterministic metrics plus judge_score, one write eac (+9 more)

### Community 167 - "Docstring and Comment Simplification Implementation Plan"
Cohesion: 0.10
Nodes (20): Docstring and Comment Simplification Implementation Plan, Global Constraints, Phase 2: test files, Self-review, Steps, Task 0: Style contract and the AST equivalence checker, Task 10: Pipeline tests (11 files), Task 11: Dataset-generation tests (8 files) (+12 more)

### Community 168 - "_retry_decorator"
Cohesion: 0.15
Nodes (14): BaseException, get_nim_client(), AsyncOpenAI, NVIDIA NIM client provider.  Returns a ready-to-use AsyncOpenAI instance pointed, Return an AsyncOpenAI client configured for NIM endpoint.      The returned obje, get_openrouter_client(), AsyncOpenAI, OpenRouter client provider.  Returns a ready-to-use AsyncOpenAI instance pointed (+6 more)

### Community 169 - "Project Overview and FAQ"
Cohesion: 0.11
Nodes (17): How are the questions generated and checked?, How do the three pipelines differ architecturally?, How do we grade the pipeline answers?, How do we test them fairly?, Project Overview and FAQ, What are the four question types?, What are the three pipelines?, What does "cost" mean in this project? (+9 more)

### Community 170 - "t"
Cohesion: 0.11
Nodes (18): at(), lt(), oe(), yt(), t(), 102657(), 245339(), 260208() (+10 more)

### Community 171 - "atomic_search_widget.js"
Cohesion: 0.22
Nodes (14): connectedCallback(), G(), H(), k(), L(), O(), _onConnect(), p() (+6 more)

### Community 172 - "l"
Cohesion: 0.13
Nodes (16): j(), k(), U(), w(), x(), l(), Wt(), 122842() (+8 more)

### Community 173 - "Answerer"
Cohesion: 0.16
Nodes (11): Answerer, AnswerResult, build_prompt(), NodeWithScore, Turns a query plus its retrieved nodes into a cited answer.  All three pipelines, Builds the user-role message: retrieved sources, then the question., Constructing an Answerer must not reach for credentials; the client     is built, test_answerer_construction_does_not_build_a_client() (+3 more)

### Community 174 - "test_database_manager_judge.py"
Cohesion: 0.28
Nodes (12): _golden(), _jeq(), Read/update helpers on database_manager for the Judge.  Additive: upsert_result, _result_row(), test_get_golden_queries_by_quadrant_filters(), test_get_jeq_judging_rows_excludes_pq(), test_get_jeq_judging_rows_joins_ground_truth(), test_update_result_human_score() (+4 more)

### Community 176 - "o"
Cohesion: 0.14
Nodes (14): N(), o(), ee(), 152328(), 199099(), 300251(), 307463(), 42176() (+6 more)

### Community 178 - "_node"
Cohesion: 0.20
Nodes (13): classify_section(), _node(), If accepted counts never actually rise from the DB's point of view     (e.g. get, End-to-end content-aware routing check: a document with one text     section and, A single table node among mostly-text nodes is still enough material for a     Q, The common case: a section under _MAX_SECTION_TOKENS must produce exactly     on, _section(), test_chunk_section_under_limit_returns_itself_unchanged() (+5 more)

### Community 179 - "loader.js"
Cohesion: 0.28
Nodes (12): allowedBrowser(), allowedBrowserBasedOnAgentPattern(), createCustomEvent(), eesyInitUserValues(), eesyIssueUserRequests(), eesyLoadCss(), eesyLoadJs(), eesySetRoleInactive() (+4 more)

### Community 180 - "loader.js"
Cohesion: 0.28
Nodes (12): allowedBrowser(), allowedBrowserBasedOnAgentPattern(), createCustomEvent(), eesyInitUserValues(), eesyIssueUserRequests(), eesyLoadCss(), eesyLoadJs(), eesySetRoleInactive() (+4 more)

### Community 181 - "P2BM25Retriever"
Cohesion: 0.27
Nodes (9): P2BM25Retriever, Path, P2: BM25 statistical retrieval.  Loads the per-document BM25Okapi corpus and ran, _fake_node(), _seed_index(), test_retrieve_filters_to_given_document_id(), test_retrieve_raises_clearly_when_index_not_built(), test_retrieve_returns_correct_top_k() (+1 more)

### Community 182 - "build_pools"
Cohesion: 0.20
Nodes (10): build_pools(), _company_of(), First underscore-delimited token of a document_id (e.g. 'AAPL_2023' ->     'AAPL, Flattens per-company section lists into one list by taking one     section from, Builds the two content pools upfront, across all filings.      `documents` is a, _round_robin_interleave(), Two companies, each with one text section and one table section.     Pools must, test_build_pools_routes_by_content_type_and_interleaves_companies() (+2 more)

### Community 185 - "Z"
Cohesion: 0.33
Nodes (7): ct(), qe(), Qt(), ut(), Xe(), Z(), 56639()

### Community 187 - "script.js"
Cohesion: 0.53
Nodes (4): clamp(), next(), prev(), show()

### Community 188 - "init"
Cohesion: 0.83
Nodes (3): handler(), init(), ready()

### Community 189 - "init"
Cohesion: 0.83
Nodes (3): handler(), init(), ready()

### Community 191 - "LLMFactory"
Cohesion: 0.05
Nodes (51): CallbackManager, generate_query(), Generator: proposes a query, ground truth answer and citations for one filing se, LLMFactory, Any, Return a client for the model and provider routed to this stage., Static factory that returns LlamaIndex-compatible LLM client objects., Return a LlamaIndex LLM instance for the given provider and model.          Args (+43 more)

### Community 192 - "test_groq_client_backoff.py"
Cohesion: 0.16
Nodes (16): call_groq(), get_groq_client(), Any, AsyncOpenAI, Groq client provider.  Builds an AsyncOpenAI client for Groq's OpenAI-compatible, Return an AsyncOpenAI client configured for Groq with retries and concurrency li, Send a chat completion to Groq and return the raw response., _FakeResponse (+8 more)

### Community 193 - "qe"
Cohesion: 1.00
Nodes (3): qe(), ut(), Xe()

### Community 195 - "search_filing_nodes"
Cohesion: 0.09
Nodes (40): BaseModel, FunctionTool, _build_search_tool(), critique_query(), Critic: independently re-derives an answer using a local search tool.  Uses qwen, Wraps search_filing_nodes as a LlamaIndex tool bound to one filing.      The nod, Runs the Critic's search-then-answer loop.      Returns {"cited_node_ids": [...], Local, dependency-free keyword search the Critic uses to find evidence.  Not a r (+32 more)

### Community 198 - "test_node_builder.py"
Cohesion: 0.17
Nodes (23): parse_citations(), Node ids cited in `raw_text`, deduplicated, first-appearance order., _fake_llm_client(), _node(), NodeWithScore, OpenAILike, Answerer: citation parsing, anti-leakage, token/latency capture.  The LLM stand-, The whole payload, both roles, carries only the question, node ids,     node tex (+15 more)

### Community 200 - "Working in this repo"
Cohesion: 0.06
Nodes (34): Deliverables, Deliverables, Deliverables, Deliverables, Deliverables, Deliverables, Deliverables, Deliverables (+26 more)

### Community 202 - "4. Implementation Guardrails (Binding)"
Cohesion: 0.24
Nodes (6): build_nodes(), _is_table_block(), Splits parsed Markdown into atomic TextNode-shaped dicts.  A table is kept as on, ingest_one(), main(), Orchestrates fetch -> parse -> node_builder -> database_manager.insert_node for

### Community 203 - "Quickstart"
Cohesion: 0.16
Nodes (23): _query(), loop_executor: cell construction, resume-skip, throttle, row shape.  Uses a stub, P2 drives its DB read with asyncio.run() inside sync retrieve(), which     raise, Default the suite to unthrottled; the throttle tests opt back in., golden_queries is the Judge's exemplar set and must stay unreachable     from an, _seed(), StubAnswerer, StubRetriever (+15 more)

### Community 204 - "fetch_filings.py"
Cohesion: 0.07
Nodes (29): 10. Academic Rigor and Methodological Principles, 1. Research Overview and Core Objectives, 2. Data Strategy and Ingestion Parsing Architecture, 3. The 140-Query Benchmark Dataset: Three Disjoint Sets, 4. Open-Model Generation and Adversarial Verification Architecture, 5. The Human Anchor: Two Roles, Two Sets, 6. Multi-Pipeline Architectural Registry, 7. Tri-Pillar Evaluation, the Judge-Validation Gate, and the Full Benchmark (+21 more)

### Community 205 - "Guardrails are binding, not advisory"
Cohesion: 0.08
Nodes (26): Connection, _dumps(), get_all_query_texts(), get_golden_queries(), get_golden_queries_by_quadrant(), get_jeq_judging_rows(), get_queries(), get_results() (+18 more)

### Community 208 - "Monitor Skill"
Cohesion: 0.09
Nodes (22): AAPL_2023_n0019 (text), AAPL_2023_n0073 (text), AAPL_2023_n0417 (text), AAPL_2023_n0568 (text), AAPL_2023_n0611 (table), AAPL_2024_n0108 (text), AAPL_2024_n0165 (text), AAPL_2024_n0197 (text) (+14 more)

### Community 211 - "quickstart.md"
Cohesion: 0.10
Nodes (19): author, bugs, url, dependencies, claude-mem, description, directories, doc (+11 more)

### Community 212 - "MSFT_2023.md"
Cohesion: 0.57
Nodes (6): build_index_for_document(), index_path(), is_document_indexed(), main(), Path, Builds the per-document P2 BM25 index: one pickled BM25Okapi corpus per filing u

### Community 213 - "dependencies"
Cohesion: 0.08
Nodes (23): Beat 10 · Conclusions, Beat 11 · Next steps and close, Beat 1 · Title and ethics, Beat 2 · Motivation, Beat 3 · Research question and aims, Beat 4 · System design, Beat 5 · The three paradigms, Beat 6 · Foundations (+15 more)

### Community 214 - "Note 7 – Interest income and interest expense"
Cohesion: 0.11
Nodes (17): AGENTS.md — OpenCode Agent Instructions for rag-techniques, Binding Constraints (from `resources/specs/Guardrails.md`), Critical Architecture Facts, Critical Execution & Problem-Solving Rules, Development Commands, Document/Styling Rules (for deliverables), Environment, Execution Restrictions (+9 more)

### Community 215 - "__init__.py"
Cohesion: 0.11
Nodes (16): 1. Cost Model at a Glance, 2. Provider Free Tiers — The LLM Workload, 3. LlamaParse — The Ingestion Workload, 4. Local Compute — $0, but Not Free of Constraints, 5. What Changed From the Original Budget, 6. Single Hard Rule, COMP702 Dissertation — Cost & Resource Plan, Cost-control rules (+8 more)

### Community 218 - "MSFT_2025.md"
Cohesion: 0.18
Nodes (14): main(), Writes golden_queries_to_label.md so a researcher can hand-write the 'why this a, render_label_markdown(), main(), parse_label_markdown(), Reads the filled-in golden_queries_to_label.md back into golden_queries., An entry missing only the Good Example line must still parse, not     silently v, test_parse_label_markdown_handles_entry_missing_good_example_line() (+6 more)

### Community 219 - "MSFT_2025.md"
Cohesion: 0.12
Nodes (8): A document_id with zero ingested nodes must fail loudly, not silently     build/, The same CallbackManager must reach both LLMFactory.get_client_for_stage()     a, A crash between persist() and the atomic rename must never leave a     false-pos, A leftover temp dir from a prior crashed build must not break the next attempt., test_build_index_for_document_cleans_stale_temp_dir_before_retry(), test_build_index_for_document_crash_leaves_only_temp_dir(), test_build_index_for_document_raises_on_no_nodes(), test_build_index_for_document_shares_callback_manager_with_llm_and_tree()

### Community 220 - "TSLA_2024.md"
Cohesion: 0.12
Nodes (16): 1.1 Primary Blue, 1.2 Neutral (blue-gray), 1.3 Gold accent — reserved, 1.4 Auxiliary evaluation colors, 1. Core scales, 2.1 Categorical (5+ series), 2.2 Sequential (ordinal data, heatmaps), 2.3 Diverging (delta / baseline-relative data) (+8 more)

### Community 221 - "TSLA_2024.md"
Cohesion: 0.12
Nodes (15): 1. Project Overview, 2. The `resources/` Folder — User Files and Steering Layer, 3. Styling and Document Rules, CLAUDE.md — Agent Instructions, Diagramming & Testing Guidelines, Draw.io Diagrams, graphify, monitor — operations log + reports (+7 more)

### Community 224 - "JNJ_2024.md"
Cohesion: 0.13
Nodes (14): 1. The Idea, 2.1 Data — CORRECTED THIS SESSION, 2.2 Code — what actually exists right now, 2.3 Tests — VERIFIED LIVE THIS SESSION, 2.4 API usage, models, providers, 2.5 Dataset generation progress — NOT empty, NOT finished, 2.6 Rate limits (live-verified figures, per spec docs), 2.7 Bugs found and fixed (13 logged in `bugs.md`, all resolved except one open item) (+6 more)

### Community 226 - "JNJ_2023.md"
Cohesion: 0.14
Nodes (13): File Structure, Global Constraints, Notes for the implementer, Phase 7: Full Benchmark Execution Implementation Plan, Self-Review, Task 1: Generalize the judging reader for PQ and add resume filter, Task 2: Generalize async_judge to judge any source_set, resumably, with a pacing cap, Task 3: Add a per-invocation pacing cap to loop_executor (+5 more)

### Community 227 - "JNJ_2023.md"
Cohesion: 0.15
Nodes (12): Execution Handoff, Global Constraints, Human Intervention Ledger (read this before starting), Phase 1 — Environment, Infrastructure & Cost Guardrails Implementation Plan, Self-Review Notes, Task 1: Repo skeleton and pinned dependency manifest, Task 2: `database_manager.py` — five-table SQLite schema in WAL mode, Task 3: `groq_client.py` — resilient async Groq wrapper (backoff + semaphore) (+4 more)

### Community 228 - "JNJ_2025.md"
Cohesion: 0.15
Nodes (12): Execution Handoff, Global Constraints, Human Intervention Ledger (read this before starting), Phase 2 — Ingestion & Parsing Pipeline Implementation Plan, Self-Review Notes, Task 1: Filings manifest + Phase 2 dependencies, Task 2: `ingest/fetch_filings.py` — download filings from SEC EDGAR, Task 3: `ingest/parse_filing.py` — LlamaParse atomic-table parsing (+4 more)

### Community 229 - "JNJ_2025.md"
Cohesion: 0.15
Nodes (13): Citation markers, Key interfaces, Model routing, Numeric normalisation, Retrieval scope: per document, not cross-corpus, Shape of the system, System architecture, The central loop (+5 more)

### Community 230 - "TSLA_2025.md"
Cohesion: 0.17
Nodes (11): After All Tasks: Full Test Suite + Throttled Live Smoke Run, Global Constraints, Phase 4: Dataset Generation & Adversarial Verification Implementation Plan, Task 1: Database helpers for queries / golden_queries / judge_validation, Task 2: Section grouper, Task 3: Cross-check (deterministic accept/reject), Task 4: Local search tool for the Critic, Task 5: `call_groq` tools param + async Generator (+3 more)

### Community 232 - "WMT_2023.md"
Cohesion: 0.18
Nodes (10): File Structure, Global Constraints, P1 Vector Pipeline Implementation Plan, Task 1: Add dependencies, Task 2: `Retriever` ABC, Task 3: `FastEmbedReranker` postprocessor, Task 4: Vector index build script, Task 5: `P1VectorRetriever` (+2 more)

### Community 233 - "WMT_2024.md"
Cohesion: 0.18
Nodes (11): Benchmark design, Evaluation: three pillars, How queries get made: generator versus critic, Scale and honesty, The 140-query dataset, The coincidental-correctness trap, The four quadrants, The judge-validation gate (+3 more)

### Community 235 - "WMT_2024.md"
Cohesion: 0.20
Nodes (9): Global Constraints, Notes for the full-corpus release (not part of this plan's tasks), Phase 3 — P3 Summary-Index Build Implementation Plan, Task 1: Add `llama-index-llms-groq` dependency, Task 2: Node-to-TextNode conversion, Task 3: Build-and-persist core logic (atomic cache, mocked in tests), Task 4: Cost logging, Task 5: Sequential orchestrator (`main()`) (+1 more)

### Community 238 - "AAPL_2023.md"
Cohesion: 0.22
Nodes (8): Architecture, Deviation to log post-implementation, Files, Goal, Out of scope, P2 BM25 Pipeline — Design, Spec constraints (binding, copied verbatim from source docs), Testing

### Community 239 - "AAPL_2023.md"
Cohesion: 0.44
Nodes (7): group_sections(), Groups filing nodes into per-section chunks for the Generator.  A "section" is e, _node(), test_excludes_null_and_empty_headers(), test_groups_nodes_by_document_and_header(), test_keeps_documents_separate(), test_normalizes_header_case_into_one_section()

### Community 241 - "AAPL_2024.md"
Cohesion: 0.22
Nodes (8): Format, Phase 1 — Infrastructure, Phase 2 — Ingestion & Parsing, Phase 3 — P3 Summary-Tree Build, Phase 4 — Dataset Generation & Adversarial Verification, Phase 5 — Retrieval Pipelines (P1/P2/P3) + Answerer + Loop Executor, Phases 6-8, Test Suite Reference

### Community 242 - "AAPL_2025.md"
Cohesion: 0.25
Nodes (7): File Layout, Global Constraints, P2 BM25 Pipeline Implementation Plan, Post-implementation (not a task — do after Task 3 is reviewed clean), Task 1: Tokenizer, Task 2: BM25 Index Builder, Task 3: P2 BM25 Retriever

### Community 243 - "AAPL_2025.md"
Cohesion: 0.25
Nodes (8): Document and styling rules, Known stale or unresolved content, Rebuilding a `.docx` on macOS, The knowledge graph, The two-layer split, Verifying a PDF, Version drift, Working in this repo

### Community 244 - "P1VectorRetriever"
Cohesion: 0.15
Nodes (17): MockLLM, P3StructuralRetriever, NodeWithScore, Path, P3: structural summary-tree retrieval.  Loads the per-filing TreeIndex built by, _ForbiddenLLM, Fails loudly if the query path ever calls an LLM., _seed_index() (+9 more)

### Community 245 - "Deviations from Original Proposed Idea"
Cohesion: 0.07
Nodes (29): 10. P3 index build bypasses the shared Groq client wrapper (2026-07-22), 11. LlamaParse table-header extraction defect (2026-07-26), 12. Dataset-generation retry and grading were too rigid (2026-07-28), 13. Embedding library unavailable on this platform (2026-07-28), 14. No token-size guard on Generator prompts (2026-07-29), 15. P3 summariser model judged too weak (2026-07-29), 16. GQ hand-labelling scale had no validation (2026-07-29), 17. Query ID format was long and quadrant-label-ambiguous (2026-07-29) (+21 more)

### Community 246 - "FastEmbedReranker"
Cohesion: 0.05
Nodes (40): BaseNodePostprocessor, NodeWithScore, Custom BM25 tokenizer: preserves numbers, decimals, percentages and currency amo, tokenize(), nodes_to_llama_nodes(), Converts nodes-table rows into LlamaIndex TextNode objects.  Kept separate from, build_index_for_document(), get_collection() (+32 more)

### Community 247 - "build_vector_index.py"
Cohesion: 0.39
Nodes (5): _fake_node(), test_build_index_for_document_atomic_write_survives_interruption(), test_build_index_for_document_builds_and_pickles_corpus(), test_build_index_for_document_isolates_nodes_across_documents(), test_build_index_for_document_skips_if_already_indexed()

### Community 249 - "tokenize"
Cohesion: 0.25
Nodes (7): Final Run, Issues, Organise information, Plan a code base search, Planning Research, Research, Using information

### Community 250 - "File Structure"
Cohesion: 0.25
Nodes (7): Deliverables (build in this order, TDD, fixture-driven — don't need real DB rows to start), Non-negotiables (Guardrails, will get flagged in review if violated), Phase 6 kickoff prompt — paste into new Claude Code session, Prompt to paste, Start by, Testing conventions, What Phase 6 is

### Community 253 - "test_build_bm25_index.py"
Cohesion: 0.29
Nodes (7): 4. Implementation Guardrails (Binding), Fixed Model Routing, Infrastructure, Judge Gate, Loop Safety, Pipeline Constraints, Storage

### Community 254 - "test_build_vector_index.py"
Cohesion: 0.29
Nodes (6): Components, Decision: Real LlamaIndex objects over a custom builder, Open technical verification (do first, before locking implementation), Out of scope (deferred to Phase 5), Phase 3 — P3 Summary-Index Build: Design, Testing

### Community 255 - "build_bm25_index.py"
Cohesion: 0.29
Nodes (7): Current state and open items, Quickstart, Reading order for the specs, Repository layout, The one thing to know first, The shape of the project in one paragraph, Where to go next

### Community 256 - "Format"
Cohesion: 0.25
Nodes (7): Benchmark Design, Knowledge Graph, RAG Techniques — COMP702 M.Sc. Dissertation, Repository Layout, Research Question, Status, The Three Pipelines

### Community 257 - "test_run_dataset_generation.py"
Cohesion: 0.29
Nodes (6): 1. Empty filing-list argument silently meant "use all filings", 2. No duplicate-question check before acceptance, 3. Questions clustered by company by accident, 4. Silent shortfall -- no warning if the dataset came up short, Development History, Format

### Community 258 - "test_cross_check.py"
Cohesion: 0.10
Nodes (36): check_query(), citations_overlap(), diagnose_rejection(), embedding_similarity(), embedding_similarity_ok(), extract_numbers(), _get_embedding_model(), Deterministic accept/reject logic for the Generator/Critic adversarial loop.  Pl (+28 more)

### Community 259 - "run_dataset_generation.py"
Cohesion: 0.29
Nodes (6): Global Constraints, Phase 4 Dataset Generation: Fix Corpus Scope + Throttled First Run, Self-Review, Task 1: Derive `_ALL_FILINGS` from `data/filings_manifest.json`, Task 2: Throttled real first run of Phase 4, Task 3: Fix `_ATTEMPT_EXCEPTIONS`'s wrong `APIStatusError` class, re-verify with a real throttled run

### Community 261 - "test_gq_labeling.py"
Cohesion: 0.40
Nodes (5): npx, drawio, playwright, @drawio/mcp, @playwright/mcp

### Community 262 - "Challenges Encountered"
Cohesion: 0.33
Nodes (6): Anti-leakage, Determinism and state, Guardrails are binding, not advisory, Loop safety, The judge gate, The single hard rule

### Community 263 - "Global Constraints"
Cohesion: 0.33
Nodes (5): Fonts, Paragraph and layout rules, Sizes (Word / PDF, A4, 2.5cm margins), Slide deck (PowerPoint), Typography — COMP702 Proposal / Dissertation / Slides

### Community 264 - "test_build_summary_index.py"
Cohesion: 0.33
Nodes (5): Diagram Palette — Tailwind 500 Only, Provider colours (10), Quadrant colours (04, and quadrant bars in 13), Rules, Semantic colour assignment

### Community 265 - "Research Issues Log"
Cohesion: 0.33
Nodes (5): 1. P3 retrieval pipeline (`as_retriever(retriever_mode="embedding")`), 2. Full unthrottled ingestion (MSFT ×3, TSLA ×3 — 6 filings), 3. Full migration off `llama_cloud_services` to the raw `llama-cloud` SDK, Deferred Items Log, Format

### Community 266 - "Global Constraints"
Cohesion: 0.33
Nodes (5): Code blast radius (critical analysis), Current state (fact, not fix), Doubt #11 Impact Assessment: `query_id` Naming Format, Recommendation, Verdict

### Community 267 - "group_sections"
Cohesion: 0.33
Nodes (5): Active — needs your input before Phase 1 is fully closed out, Known cosmetic gaps (logged, not blocking), Not yet needed (deferred to their own phase), Passive — already handled, no action needed unless you want to change it, Phase 1 — Human Action Report

### Community 269 - "Note 7 – Interest income and interest expense"
Cohesion: 0.33
Nodes (5): A real bug found and fixed this session, Build Progress — Phase 1 through Phase 5 Status Snapshot, Next steps, in dependency order, Phase-by-phase status, What needs attention (priority order)

### Community 270 - "Deferred Items Log"
Cohesion: 0.40
Nodes (4): Design, Open question before implementation, Phase 5/7 Loop Executor: Retry-Queue Design (for future implementation), Problem it solves

### Community 271 - "Monitor Skill"
Cohesion: 0.40
Nodes (4): Commands, Monitor Skill, Notes, Usage

### Community 272 - "Phase 2 — Human Action Report"
Cohesion: 0.40
Nodes (4): Active — needs your input before Phase 2 is fully closed out, Not yet needed (deferred to their own phase), Passive — already handled, no action needed unless you want to change it, Phase 2 — Human Action Report

### Community 276 - "Challenges Encountered"
Cohesion: 0.50
Nodes (3): 1. NIM API limits still throttling P3, now the longest-running phase (2026-08-05), 2. Groq free tier could not sustain the P3 summary build (2026-07-31), Challenges Encountered

### Community 277 - "Research Issues Log"
Cohesion: 0.50
Nodes (3): 1. LlamaParse table header misalignment, Format, Research Issues Log

## Knowledge Gaps
- **592 isolated node(s):** `@playwright/mcp`, `@drawio/mcp`, `$schema`, `plugin`, `@opencode-ai/plugin` (+587 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **150 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `P1VectorRetriever` connect `FastEmbedReranker` to `loop_executor.py`, `compare.py`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Why does `build_retrievers()` connect `loop_executor.py` to `P1VectorRetriever`, `P2BM25Retriever`, `FastEmbedReranker`?**
  _High betweenness centrality (0.006) - this node is a cross-community bridge._
- **Why does `t()` connect `t` to `e`, `atomic_search_widget.js`, `l`, `ally.b2f86d8b36422ca86a9f.js`, `o`, `f`, `jQueryPrivate.js`, `init`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Are the 52 inferred relationships involving `o()` (e.g. with `A()` and `an()`) actually correct?**
  _`o()` has 52 INFERRED edges - model-reasoned connections that need verification._
- **Are the 52 inferred relationships involving `o()` (e.g. with `A()` and `an()`) actually correct?**
  _`o()` has 52 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `t()` (e.g. with `ae()` and `b()`) actually correct?**
  _`t()` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `t()` (e.g. with `ae()` and `b()`) actually correct?**
  _`t()` has 54 INFERRED edges - model-reasoned connections that need verification._