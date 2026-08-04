# Graph Report - rag-techniques  (2026-07-31)

## Corpus Check
- 96 files · ~140,409 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1003 nodes · 1069 edges · 194 communities (55 shown, 139 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 98 edges (avg confidence: 0.82)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `77fb6195`
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
- Project Idea.md
- test_config.py
- monitor_lib.py
- Benchmark design
- Proposal_v1.0.0_8228ebe1.md
- Budget.md
- 1. Core scales
- render_logs.py
- database_manager.py
- Human Intervention Ledger (read this before starting)
- Working in this repo
- Guardrails.md
- System architecture
- render_report.py
- profile.py
- logger.py
- RAG Techniques — COMP702 M.Sc. Dissertation
- Typography — COMP702 Proposal / Dissertation / Slides
- monitor — companion skills in this project
- groq_limits.md
- Changes.md
- directory-structure.md
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
- rag-techniques-benchmark
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
- todo.md
- Human Intervention Ledger (read this before starting)
- run_ingestion.py
- groq_client.py
- Phase 1 — Human Action Report
- Phase 2 — Human Action Report
- quickstart.md
- test_run_dataset_generation.py
- test_cross_check.py
- run_dataset_generation.py
- async_critic.py
- test_gq_labeling.py
- Global Constraints
- test_build_summary_index.py
- Global Constraints
- group_sections
- Phase 3 — P3 Summary-Index Build: Design
- Deferred Items Log
- Phase 5/7 Loop Executor: Retry-Queue Design (for future implementation)
- backup_data.sh
- reload_backup.sh

## God Nodes (most connected - your core abstractions)
1. `Ingestion Corpus Sample Reference` - 22 edges
2. `AGENTS.md — OpenCode Agent Instructions for rag-techniques` - 15 edges
3. `values_match()` - 12 edges
4. `_attempt_fill()` - 11 edges
5. `_node()` - 11 edges
6. `check_query()` - 10 edges
7. `diagnose_rejection()` - 10 edges
8. `search_filing_nodes()` - 10 edges
9. `System architecture` - 10 edges
10. `critique_query()` - 9 edges

## Surprising Connections (you probably didn't know these)
- `test_format_underfill_summary_marks_only_below_target_quadrants()` --calls--> `format_underfill_summary()`  [INFERRED]
  project/tests/test_run_dataset_generation.py → project/dataset_generation/run_dataset_generation.py
- `_attempt_fill()` --calls--> `critique_query()`  [INFERRED]
  project/dataset_generation/run_dataset_generation.py → project/dataset_generation/async_critic.py
- `_attempt_fill()` --calls--> `generate_query()`  [INFERRED]
  project/dataset_generation/run_dataset_generation.py → project/dataset_generation/async_generator.py
- `test_citations_overlap_false_on_disjoint_sets()` --calls--> `citations_overlap()`  [INFERRED]
  project/tests/test_cross_check.py → project/dataset_generation/cross_check.py
- `test_citations_overlap_true_on_any_shared_node()` --calls--> `citations_overlap()`  [INFERRED]
  project/tests/test_cross_check.py → project/dataset_generation/cross_check.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three retrieval paradigms share one answerer and one judge** — resources_artifacts_proposal_v1_0_0_p1_vector_pipeline, resources_artifacts_proposal_v1_0_0_p2_bm25_pipeline, resources_artifacts_proposal_v1_0_0_p3_structural_pipeline, resources_artifacts_proposal_v1_0_0_shared_answerer, resources_artifacts_proposal_v1_0_0_llm_judge [EXTRACTED 1.00]
- **Zero-spend quota safety pattern (throttle, WAL resume, disjoint sets, Groq free tier)** — resources_artifacts_proposal_v1_0_0_groq_free_tier, resources_artifacts_proposal_v1_0_0_local_throttle, resources_artifacts_proposal_v1_0_0_sqlite_wal_store, resources_artifacts_proposal_v1_0_0_risk_management_plan [INFERRED 0.85]
- **Guidelines and template constrain the submitted proposal** — resources_docs_proposalguidelines_required_structure, resources_docs_proposaltemplate_section_skeleton, resources_artifacts_proposal_v1_0_0_document, resources_artifacts_projectproposal_document [INFERRED 0.85]

## Communities (194 total, 139 thin omitted)

### Community 2 - "Proposal Compliance and Benchmark Design"
Cohesion: 0.05
Nodes (49): ProjectProposal (earlier draft of the COMP702 proposal), Draft Development and Implementation Summary (§4), BCS Project Criteria Mapping, 140-Query Human-Anchored Benchmark, Chen et al. (2021) FinQA Numerical Reasoning over Financial Data, Citation Audit (detects coincidentally-correct answers), Disjoint Query Sets PQ/GQ/JEQ (100/20/20), Design and Specification Proposal v1.0.0 (COMP702) (+41 more)

### Community 4 - "Research Question and Literature Base"
Cohesion: 0.14
Nodes (23): clean_logs(), clean_reports(), main(), Path, build_html(), _card(), _extract_tool(), _frag_card() (+15 more)

### Community 5 - "Guardrails and Model Routing"
Cohesion: 0.10
Nodes (19): 1. Project Overview, 2. The `resources/` Folder — User Files and Steering Layer, 3. Styling and Document Rules, 4. Implementation Guardrails (Binding), CLAUDE.md — Agent Instructions, Fixed Model Routing, graphify, Infrastructure (+11 more)

### Community 8 - "Filing HTML and XBRL Markup"
Cohesion: 0.28
Nodes (9): dei:EntityPublicFloat Fact, Inline Style and Entity Noise in Filing HTML, Inline XBRL (ix:nonFraction) Tagging, Apple 10-K Paragraph HTML Sample, Colspan Spacer-Cell Table Layout, Interest Rate Sensitivity Disclosure, SEC 10-K Filing Source Format, Apple 10-K Interest Rate Sensitivity Table HTML Sample (+1 more)

### Community 9 - "Interest Rate Sensitivity Table"
Cohesion: 0.38
Nodes (7): Apple 10-K Interest Rate Sensitivity Table Sample, Hypothetical 100 Basis Point Rate Increase, All Tenors, Interest Rate Sensitivity Disclosure, Investment Portfolio (Decline in Fair Value), SEC 10-K Tabular Financial Data, Table Retrieval Challenge for RAG Pipelines, Term Debt (Increase in Annual Interest Expense)

### Community 10 - "Spec Document Set"
Cohesion: 0.06
Nodes (33): 0. Decisions Carried Over From the Scoping Discussion, 10. Consolidated Dependency Manifest, 11. Open Items / Recommendations, 1. Design Review: Issues Found and Resolved, 2.1 Component View, 2.2 Deployment View, 2.3 Data-Flow Summary, 2. High-Level Design (HLD) (+25 more)

### Community 12 - "Phase Plan.md"
Cohesion: 0.06
Nodes (34): Deliverables, Deliverables, Deliverables, Deliverables, Deliverables, Deliverables, Deliverables, Deliverables (+26 more)

### Community 13 - "Project Idea.md"
Cohesion: 0.07
Nodes (29): 10. Academic Rigor and Methodological Principles, 1. Research Overview and Core Objectives, 2. Data Strategy and Ingestion Parsing Architecture, 3. The 140-Query Benchmark Dataset: Three Disjoint Sets, 4. Open-Model Generation and Adversarial Verification Architecture, 5. The Human Anchor: Two Roles, Two Sets, 6. Multi-Pipeline Architectural Registry, 7. Tri-Pillar Evaluation, the Judge-Validation Gate, and the Full Benchmark (+21 more)

### Community 14 - "test_config.py"
Cohesion: 0.20
Nodes (13): classify_section(), _node(), A single table node among mostly-text nodes is still enough material     for a Q, The overwhelmingly common case: a section under _MAX_SECTION_TOKENS     must pro, If accepted counts never actually rise from the DB's point of view     (e.g. get, End-to-end content-aware routing check: a document with one text     section and, _section(), test_chunk_section_under_limit_returns_itself_unchanged() (+5 more)

### Community 15 - "monitor_lib.py"
Cohesion: 0.08
Nodes (35): ArgumentParser, load_schema(), log_operation(), main(), Path, render_entry(), validate(), add_root_arg() (+27 more)

### Community 16 - "Benchmark design"
Cohesion: 0.18
Nodes (13): Encoding, chunk_section(), _get_encoding(), _log_oversized_node_skipped(), Doubt #8 fix: mirrors _log_attempt_outcome's structured-logging style     (modul, Splits a group_sections() section into one or more Generator-sized     chunks, e, `n` single-token words: tiktoken's cl100k_base encoding tokenizes     the bare w, Naive greedy packing would close the chunk right before n2 (the     6-token text (+5 more)

### Community 17 - "Proposal_v1.0.0_8228ebe1.md"
Cohesion: 0.20
Nodes (10): build_pools(), _company_of(), First underscore-delimited token of a document_id (e.g. 'AAPL_2023' ->     'AAPL, Flattens per-company section lists into one list by taking one     section from, Builds the two content pools upfront, across ALL filings.      `documents` is a, _round_robin_interleave(), Two companies, each with one text section and one table section.     Pools must, test_build_pools_routes_by_content_type_and_interleaves_companies() (+2 more)

### Community 18 - "Budget.md"
Cohesion: 0.11
Nodes (16): 1. Cost Model at a Glance, 2. Groq Free Tier — The LLM Workload, 3. LlamaParse — The Ingestion Workload, 4. Local Compute — $0, but Not Free of Constraints, 5. What Changed From the Original Budget, 6. Single Hard Rule, COMP702 Dissertation — Cost & Resource Plan, Cost-control rules (+8 more)

### Community 19 - "1. Core scales"
Cohesion: 0.12
Nodes (16): 1.1 Primary Blue, 1.2 Neutral (blue-gray), 1.3 Gold accent — reserved, 1.4 Auxiliary evaluation colors, 1. Core scales, 2.1 Categorical (5+ series), 2.2 Sequential (ordinal data, heatmaps), 2.3 Diverging (delta / baseline-relative data) (+8 more)

### Community 20 - "render_logs.py"
Cohesion: 0.33
Nodes (5): plugin, $schema, @ephemushroom/opencode-claude-mem, https://github.com/anthonystepvoy/caveman-opencode.git, superpowers@git+https://github.com/obra/superpowers.git

### Community 21 - "database_manager.py"
Cohesion: 0.05
Nodes (13): Connection, _dumps(), get_golden_queries(), init_db(), insert_golden_query(), insert_judge_validation(), insert_query(), _loads() (+5 more)

### Community 22 - "Human Intervention Ledger (read this before starting)"
Cohesion: 0.15
Nodes (12): Execution Handoff, Global Constraints, Human Intervention Ledger (read this before starting), Phase 1 — Environment, Infrastructure & Cost Guardrails Implementation Plan, Self-Review Notes, Task 1: Repo skeleton and pinned dependency manifest, Task 2: `database_manager.py` — five-table SQLite schema in WAL mode, Task 3: `groq_client.py` — resilient async Groq wrapper (backoff + semaphore) (+4 more)

### Community 23 - "Working in this repo"
Cohesion: 0.33
Nodes (5): Code blast radius (critical analysis), Current state (fact, not fix), Doubt #11 Impact Assessment: `query_id` Naming Format, Recommendation, Verdict

### Community 24 - "Guardrails.md"
Cohesion: 0.14
Nodes (12): 1. Absolute Infrastructure Ban: No Per-Hour or Scale-to-Non-Zero Infrastructure, 2. Model Routing Matrix and Local Compute (per-stage LLM assignment), 3. Anti-Leakage: What Each Model May and May Not See, 4. Judge Few-Shot Filtering and the Mandatory Validation Gate, 4a. Dynamic few-shot filtering, 4b. The judge-validation gate (hard prerequisite for the full run), 5. Concurrency and Rate-Limiting Enforcement, 6. Relational Data Management and State Persistence (+4 more)

### Community 25 - "System architecture"
Cohesion: 0.04
Nodes (45): Benchmark design, Evaluation: three pillars, How queries get made: generator versus critic, Scale and honesty, The 140-query dataset, The coincidental-correctness trap, The four quadrants, The judge-validation gate (+37 more)

### Community 26 - "render_report.py"
Cohesion: 0.50
Nodes (3): plugin, $schema, .opencode/plugins/graphify.js

### Community 28 - "logger.py"
Cohesion: 0.09
Nodes (22): AAPL_2023_n0019 (text), AAPL_2023_n0073 (text), AAPL_2023_n0417 (text), AAPL_2023_n0568 (text), AAPL_2023_n0611 (table), AAPL_2024_n0108 (text), AAPL_2024_n0165 (text), AAPL_2024_n0197 (text) (+14 more)

### Community 29 - "RAG Techniques — COMP702 M.Sc. Dissertation"
Cohesion: 0.29
Nodes (6): Benchmark Design, RAG Techniques — COMP702 M.Sc. Dissertation, Repository Layout, Research Question, Status, The Three Pipelines

### Community 30 - "Typography — COMP702 Proposal / Dissertation / Slides"
Cohesion: 0.33
Nodes (5): Fonts, Paragraph and layout rules, Sizes (Word / PDF, A4, 2.5cm margins), Slide deck (PowerPoint), Typography — COMP702 Proposal / Dissertation / Slides

### Community 167 - "todo.md"
Cohesion: 0.25
Nodes (7): Daily Cap Limit, Doubts, Organise information, Plan a code base search, Planning Research, Research, Using information

### Community 170 - "Human Intervention Ledger (read this before starting)"
Cohesion: 0.15
Nodes (12): Execution Handoff, Global Constraints, Human Intervention Ledger (read this before starting), Phase 2 — Ingestion & Parsing Pipeline Implementation Plan, Self-Review Notes, Task 1: Filings manifest + Phase 2 dependencies, Task 2: `ingest/fetch_filings.py` — download filings from SEC EDGAR, Task 3: `ingest/parse_filing.py` — LlamaParse atomic-table parsing (+4 more)

### Community 171 - "run_ingestion.py"
Cohesion: 0.07
Nodes (20): _download_bytes(), fetch_filing(), _get_json(), _headers(), Downloads SEC 10-K filings, resolving real URLs from SEC EDGAR's public JSON API, resolve_cik(), build_nodes(), _is_table_block() (+12 more)

### Community 173 - "groq_client.py"
Cohesion: 0.06
Nodes (23): BaseException, Model routing, throttle flag, and env loading for the whole benchmark build., generate_query(), Generator: proposes a query + ground truth + citations for one filing section., _is_rate_limit_error(), Resilient async Groq wrapper: tenacity backoff on 429 + bounded concurrency.  Se, Reusable LOCAL_TEST_THROTTLE pattern for every Phase 2-7 loop script.  Guardrail, append_cost_log() (+15 more)

### Community 180 - "Phase 1 — Human Action Report"
Cohesion: 0.33
Nodes (5): Active — needs your input before Phase 1 is fully closed out, Known cosmetic gaps (logged, not blocking), Not yet needed (deferred to their own phase), Passive — already handled, no action needed unless you want to change it, Phase 1 — Human Action Report

### Community 181 - "Phase 2 — Human Action Report"
Cohesion: 0.40
Nodes (4): Active — needs your input before Phase 2 is fully closed out, Not yet needed (deferred to their own phase), Passive — already handled, no action needed unless you want to change it, Phase 2 — Human Action Report

### Community 182 - "quickstart.md"
Cohesion: 0.11
Nodes (17): AGENTS.md — OpenCode Agent Instructions for rag-techniques, Binding Constraints (from `resources/specs/Guardrails.md`), Critical Architecture Facts, Critical Execution & Problem-Solving Rules, Development Commands, Document/Styling Rules (for deliverables), Environment, Execution Restrictions (+9 more)

### Community 257 - "test_run_dataset_generation.py"
Cohesion: 0.07
Nodes (31): next_target(), First still-unfilled (table, quadrant) slot, searched quadrant-major     then ta, _empty_counts(), _isolate_progress_log(), main() calls _configure_logging() on every entry; a process that (in     theory), Simulates process A having already committed 2 accepted queries into     (querie, Attempt 1 is rejected by check_query (citation mismatch: Critic cites     a node, When the first attempt is accepted outright, generate_query must be     called e (+23 more)

### Community 258 - "test_cross_check.py"
Cohesion: 0.10
Nodes (36): check_query(), citations_overlap(), diagnose_rejection(), embedding_similarity(), embedding_similarity_ok(), extract_numbers(), _get_embedding_model(), Deterministic accept/reject logic for the Generator/Critic adversarial loop.  Pl (+28 more)

### Community 259 - "run_dataset_generation.py"
Cohesion: 0.16
Nodes (19): _accept_query(), append_failure_log(), _attempt_fill(), _configure_logging(), format_underfill_summary(), _load_counts(), _log_attempt_outcome(), main() (+11 more)

### Community 260 - "async_critic.py"
Cohesion: 0.13
Nodes (24): critique_query(), Critic: independently re-derives an answer using a local search tool.  Uses qwen, Run the Critic's search-then-answer loop and return the parsed final     answer, Local, dependency-free keyword search the Critic uses to find evidence.  Not a r, search_filing_nodes(), _tokenize(), _final_response(), ONE live, throttled smoke test proving async_critic.critique_query() actually sp (+16 more)

### Community 261 - "test_gq_labeling.py"
Cohesion: 0.18
Nodes (14): main(), Writes golden_queries_to_label.md so the researcher can hand-write the 'why this, render_label_markdown(), main(), parse_label_markdown(), Reads the filled-in golden_queries_to_label.md back into golden_queries., An entry from an older-format golden_queries_to_label.md (exported     before th, test_parse_label_markdown_handles_entry_missing_good_example_line() (+6 more)

### Community 263 - "Global Constraints"
Cohesion: 0.17
Nodes (11): After All Tasks: Full Test Suite + Throttled Live Smoke Run, Global Constraints, Phase 4: Dataset Generation & Adversarial Verification Implementation Plan, Task 1: Database helpers for queries / golden_queries / judge_validation, Task 2: Section grouper, Task 3: Cross-check (deterministic accept/reject), Task 4: Local search tool for the Critic, Task 5: `call_groq` tools param + async Generator (+3 more)

### Community 264 - "test_build_summary_index.py"
Cohesion: 0.18
Nodes (6): A document_id with zero ingested nodes must fail loudly, not silently     build/, A crash between persist() and the atomic rename must never leave a     false-pos, A leftover temp dir from a prior crashed build must not break the next attempt., test_build_index_for_document_cleans_stale_temp_dir_before_retry(), test_build_index_for_document_crash_leaves_only_temp_dir(), test_build_index_for_document_raises_on_no_nodes()

### Community 266 - "Global Constraints"
Cohesion: 0.20
Nodes (9): Global Constraints, Notes for the full-corpus release (not part of this plan's tasks), Phase 3 — P3 Summary-Index Build Implementation Plan, Task 1: Add `llama-index-llms-groq` dependency, Task 2: Node-to-TextNode conversion, Task 3: Build-and-persist core logic (atomic cache, mocked in tests), Task 4: Cost logging, Task 5: Sequential orchestrator (`main()`) (+1 more)

### Community 267 - "group_sections"
Cohesion: 0.44
Nodes (7): group_sections(), Groups Phase 2 nodes into per-section chunks for the Phase 4 Generator.  A "sect, _node(), test_excludes_null_and_empty_headers(), test_groups_nodes_by_document_and_header(), test_keeps_documents_separate(), test_normalizes_header_case_into_one_section()

### Community 268 - "Phase 3 — P3 Summary-Index Build: Design"
Cohesion: 0.29
Nodes (6): Components, Decision: Real LlamaIndex objects over a custom builder, Open technical verification (do first, before locking implementation), Out of scope (deferred to Phase 5), Phase 3 — P3 Summary-Index Build: Design, Testing

### Community 270 - "Deferred Items Log"
Cohesion: 0.33
Nodes (5): 1. P3 retrieval pipeline (`as_retriever(retriever_mode="embedding")`), 2. Full unthrottled ingestion (MSFT ×3, TSLA ×3 — 6 filings), 3. Full migration off `llama_cloud_services` to the raw `llama-cloud` SDK, Deferred Items Log, Format

### Community 271 - "Phase 5/7 Loop Executor: Retry-Queue Design (for future implementation)"
Cohesion: 0.40
Nodes (4): Design, Open question before implementation, Phase 5/7 Loop Executor: Retry-Queue Design (for future implementation), Problem it solves

## Knowledge Gaps
- **382 isolated node(s):** `$schema`, `.opencode/plugins/graphify.js`, `$schema`, `@ephemushroom/opencode-claude-mem`, `superpowers@git+https://github.com/obra/superpowers.git` (+377 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **139 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `_attempt_fill()` connect `run_dataset_generation.py` to `test_cross_check.py`, `async_critic.py`, `groq_client.py`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Why does `critique_query()` connect `async_critic.py` to `run_dataset_generation.py`?**
  _High betweenness centrality (0.008) - this node is a cross-community bridge._
- **Why does `diagnose_rejection()` connect `test_cross_check.py` to `run_dataset_generation.py`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `values_match()` (e.g. with `test_values_match_exact_after_normalization()` and `test_values_match_falls_back_to_text_equality_with_no_numbers()`) actually correct?**
  _`values_match()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `_attempt_fill()` (e.g. with `critique_query()` and `generate_query()`) actually correct?**
  _`_attempt_fill()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `.opencode/plugins/graphify.js`, `$schema` to the rest of the system?**
  _382 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Proposal Compliance and Benchmark Design` be split into smaller, more focused modules?**
  _Cohesion score 0.04931972789115646 - nodes in this community are weakly interconnected._