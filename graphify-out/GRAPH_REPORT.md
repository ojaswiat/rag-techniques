# Graph Report - rag-techniques  (2026-09-11)

## Corpus Check
- 298 files · ~3,394,825 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 3715 nodes · 5806 edges · 330 communities (178 shown, 152 thin omitted)
- Extraction: 82% EXTRACTED · 18% INFERRED · 0% AMBIGUOUS · INFERRED: 1026 edges (avg confidence: 0.75)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `cf4f3147`
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
- check_docstrings_only.py
- opencode.json
- opencode.json
- dependencies
- build_report.py
- index_build_cost.py
- conftest.py
- LLMFactory
- groq_limits.md
- backup_data.sh
- reload_backup.sh
- snippets.md
- directory-structure.md
- score_gate_outputs.py
- async_judge.py
- build_prefix
- Judge Scoring Criteria (1 to 5)
- Judge Validation and Execution Methodology
- test_llm_client_nim.py
- _loads
- test_async_generator.py
- gate_reference_scores.py
- P1VectorRetriever
- test_gq_calibration.py
- model_cache.py
- build_summary_index.py
- report.py
- repair_answer_keys.py
- init_db
- TextNode
- gq_label_export.py
- _seed_all_pipelines
- write_gq_labels.py
- fast_backoff
- test_adjacent_bands_do_not_agree
- test_tolerance_is_narrower_than_one_band

## God Nodes (most connected - your core abstractions)
1. `o()` - 60 edges
2. `o()` - 60 edges
3. `t()` - 57 edges
4. `t()` - 57 edges
5. `l()` - 50 edges
6. `l()` - 50 edges
7. `e()` - 40 edges
8. `e()` - 40 edges
9. `Deviations from Original Proposed Idea` - 39 edges
10. `f()` - 27 edges

## Surprising Connections (you probably didn't know these)
- `test_format_underfill_summary_marks_only_below_target_quadrants()` --calls--> `format_underfill_summary()`  [INFERRED]
  project/tests/test_run_dataset_generation.py → project/dataset_generation/run_dataset_generation.py
- `152328()` --indirect_call--> `o()`  [INFERRED]
  resources/assignments/2nd Assessment_ Project Video and Q&A Sessions (15%)_ 202526-COMP702 - MSc Project_files/main-entry-1df6e4f76b61ffdd.js → resources/assignments/2nd Assessment_ Project Video and Q&A Sessions (15%)_ 202526-COMP702 - MSc Project_files/ally.b2f86d8b36422ca86a9f.js
- `199099()` --indirect_call--> `o()`  [INFERRED]
  resources/assignments/2nd Assessment_ Project Video and Q&A Sessions (15%)_ 202526-COMP702 - MSc Project_files/main-entry-1df6e4f76b61ffdd.js → resources/assignments/2nd Assessment_ Project Video and Q&A Sessions (15%)_ 202526-COMP702 - MSc Project_files/ally.b2f86d8b36422ca86a9f.js
- `300251()` --indirect_call--> `o()`  [INFERRED]
  resources/assignments/2nd Assessment_ Project Video and Q&A Sessions (15%)_ 202526-COMP702 - MSc Project_files/main-entry-1df6e4f76b61ffdd.js → resources/assignments/2nd Assessment_ Project Video and Q&A Sessions (15%)_ 202526-COMP702 - MSc Project_files/ally.b2f86d8b36422ca86a9f.js
- `42176()` --indirect_call--> `o()`  [INFERRED]
  resources/assignments/2nd Assessment_ Project Video and Q&A Sessions (15%)_ 202526-COMP702 - MSc Project_files/main-entry-1df6e4f76b61ffdd.js → resources/assignments/2nd Assessment_ Project Video and Q&A Sessions (15%)_ 202526-COMP702 - MSc Project_files/ally.b2f86d8b36422ca86a9f.js

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three retrieval paradigms share one answerer and one judge** — resources_artifacts_proposal_v1_0_0_p1_vector_pipeline, resources_artifacts_proposal_v1_0_0_p2_bm25_pipeline, resources_artifacts_proposal_v1_0_0_p3_structural_pipeline, resources_artifacts_proposal_v1_0_0_shared_answerer, resources_artifacts_proposal_v1_0_0_llm_judge [EXTRACTED 1.00]
- **Zero-spend quota safety pattern (throttle, WAL resume, disjoint sets, Groq free tier)** — resources_artifacts_proposal_v1_0_0_groq_free_tier, resources_artifacts_proposal_v1_0_0_local_throttle, resources_artifacts_proposal_v1_0_0_sqlite_wal_store, resources_artifacts_proposal_v1_0_0_risk_management_plan [INFERRED 0.85]
- **Guidelines and template constrain the submitted proposal** — resources_docs_proposalguidelines_required_structure, resources_docs_proposaltemplate_section_skeleton, resources_artifacts_proposal_v1_0_0_document, resources_artifacts_projectproposal_document [INFERRED 0.85]

## Communities (330 total, 152 thin omitted)

### Community 2 - "Proposal Compliance and Benchmark Design"
Cohesion: 0.05
Nodes (49): ProjectProposal (earlier draft of the COMP702 proposal), Draft Development and Implementation Summary (§4), BCS Project Criteria Mapping, 140-Query Human-Anchored Benchmark, Chen et al. (2021) FinQA Numerical Reasoning over Financial Data, Citation Audit (detects coincidentally-correct answers), Disjoint Query Sets PQ/GQ/JEQ (100/20/20), Design and Specification Proposal v1.0.0 (COMP702) (+41 more)

### Community 4 - "Research Question and Literature Base"
Cohesion: 0.18
Nodes (13): Encoding, chunk_section(), _get_encoding(), _log_oversized_node_skipped(), Logs the rare case where a single node, almost always one enormous     table, ex, Splits a group_sections() section into one or more Generator-sized     chunks, e, `n` single-token words. tiktoken's cl100k_base encoding tokenizes the bare     w, Naive greedy packing would close the chunk right before n2 (the     6-token text (+5 more)

### Community 5 - "Guardrails and Model Routing"
Cohesion: 0.06
Nodes (47): answer_ngrams(), apply_repairs(), contains_answer_literal(), _decimals(), explains_derived(), load_node_contents(), load_rows(), localise() (+39 more)

### Community 8 - "Filing HTML and XBRL Markup"
Cohesion: 0.28
Nodes (9): dei:EntityPublicFloat Fact, Inline Style and Entity Noise in Filing HTML, Inline XBRL (ix:nonFraction) Tagging, Apple 10-K Paragraph HTML Sample, Colspan Spacer-Cell Table Layout, Interest Rate Sensitivity Disclosure, SEC 10-K Filing Source Format, Apple 10-K Interest Rate Sensitivity Table HTML Sample (+1 more)

### Community 9 - "Interest Rate Sensitivity Table"
Cohesion: 0.38
Nodes (7): Apple 10-K Interest Rate Sensitivity Table Sample, Hypothetical 100 Basis Point Rate Increase, All Tenors, Interest Rate Sensitivity Disclosure, Investment Portfolio (Decline in Fair Value), SEC 10-K Tabular Financial Data, Table Retrieval Challenge for RAG Pipelines, Term Debt (Increase in Annual Interest Expense)

### Community 10 - "Spec Document Set"
Cohesion: 0.07
Nodes (33): _attempt(), _FakeBuilder, Path, index_build_cost: the one-off cost of building each pipeline's index.  The risks, Stands in for build_vector_index / build_bm25_index., Otherwise a skipped build would be published as a near-zero cost., A leftover index from an earlier measurement would be timed as a hit., Its wall clock includes provider queueing that a replay would not see. (+25 more)

### Community 12 - "Phase Plan.md"
Cohesion: 0.00
Nodes (43): 102657(), 122842(), 152328(), 155769(), 168396(), 199099(), 245339(), 247767() (+35 more)

### Community 13 - "Project Idea.md"
Cohesion: 0.09
Nodes (32): apply_house_style(), _bar_labels(), build_all(), figure_answer_quality(), figure_by_quadrant(), figure_effect_of_k(), figure_paired_comparisons(), figure_retrieval_quality() (+24 more)

### Community 14 - "test_config.py"
Cohesion: 0.00
Nodes (43): 102657(), 122842(), 152328(), 155769(), 168396(), 199099(), 245339(), 247767() (+35 more)

### Community 15 - "ally.b2f86d8b36422ca86a9f.js"
Cohesion: 0.07
Nodes (52): Ai(), an(), bn(), Bt(), ct(), dn(), ei(), et() (+44 more)

### Community 16 - "ally.b2f86d8b36422ca86a9f.js"
Cohesion: 0.08
Nodes (46): Ai(), an(), b(), bn(), Bt(), dn(), ei(), fn() (+38 more)

### Community 17 - "o"
Cohesion: 0.17
Nodes (45): A(), C(), D(), F(), H(), ii(), L(), m() (+37 more)

### Community 18 - "f"
Cohesion: 0.17
Nodes (42): A(), b(), C(), D(), F(), H(), ii(), j() (+34 more)

### Community 19 - "jQueryPrivate.js"
Cohesion: 0.07
Nodes (33): P(), A(), at(), b(), be(), ce(), e(), Ee() (+25 more)

### Community 20 - "test_run_dataset_generation.py"
Cohesion: 0.05
Nodes (42): next_target(), First still-unfilled (table, quadrant) slot, searched quadrant-major     then ta, _empty_counts(), _isolate_progress_log(), Attempt 1 is rejected via a citation mismatch (Critic cites an     unrelated nod, Simulates process A having already committed 2 accepted queries into     (querie, main() calls _configure_logging() on every entry; a process that (in     theory), Guards the unaffected case: document_ids=None (or omitted entirely)     must sti (+34 more)

### Community 21 - "jQueryPrivate.js"
Cohesion: 0.08
Nodes (32): P(), A(), at(), b(), be(), ce(), e(), Ee() (+24 more)

### Community 22 - "compare.py"
Cohesion: 0.13
Nodes (18): aggregate(), build_retrievers(), _gt_list(), load_demo_queries(), Runs one query through all three retrieval paradigms and scores the overlap.  On, One query per quadrant, lowest query_id first so the pick is stable., P1 is constructed last: it loads two ONNX models and is the slow one., gt_citations is a TEXT column holding a list literal.      Rows written by diffe (+10 more)

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
Cohesion: 0.13
Nodes (18): score_gate_outputs: reference scoring and the Concordance-Rate gate.  Two jobs:, Seed one JEQ gate row plus its judge_validation ground truth.      Self-containe, Independence is the only property the gate figure retains on this     path, so t, Two more leaks beyond judge_score: pipeline identity (both the     `pipeline` co, _rows(), _seed_row(), test_agreement_rate_all_agree_passes(), test_agreement_rate_eighty_percent_fails_strict_gate() (+10 more)

### Community 28 - "logger.py"
Cohesion: 0.13
Nodes (14): 10. P3 build logged zero token cost despite generating real summaries (2026-08-04), 11. LLM temperature silently fell back to 0.1, not the mandated 0 (2026-08-04), 12. Empty filing-list argument was indistinguishable from "not provided" (2026-08-04), 13. No duplicate-question check let near-identical questions into the benchmark set (2026-08-04), 1. Reasoning-tuned models could return `content=None`, crashing `json.loads()` in Generator and Critic (2026-08-12), 2. Dataset-generation orchestrator only ever saw 9 of the 13 in-scope filings (2026-08-11), 3. Real Groq API failures crashed the whole dataset-generation run instead of being retried (2026-08-11), 4. LLMFactory's retry/backoff wrapper was silently never applied (2026-08-11) (+6 more)

### Community 29 - "RAG Techniques — COMP702 M.Sc. Dissertation"
Cohesion: 0.06
Nodes (33): 0. Decisions Carried Over From the Scoping Discussion, 10. Consolidated Dependency Manifest, 11. Open Items / Recommendations, 1. Design Review: Issues Found and Resolved, 2.1 Component View, 2.2 Deployment View, 2.3 Data-Flow Summary, 2. High-Level Design (HLD) (+25 more)

### Community 30 - "t"
Cohesion: 0.19
Nodes (35): ae(), at(), be(), ce(), de(), e(), ee(), fe() (+27 more)

### Community 31 - "test_metrics.py"
Cohesion: 0.09
Nodes (31): citation_audit(), precision_at_k(), True when every cited node id is one of the ground-truth citations.      An empt, Ground-truth nodes among the top-k retrieved, divided by k.      The denominator, Fraction of ground-truth nodes that appear anywhere in retrieved.      No k argu, SQuAD-style token-overlap F1 between the answer and the ground truth.      Multi, recall_at_k(), token_f1() (+23 more)

### Community 32 - "The code demo, explained"
Cohesion: 0.07
Nodes (28): 10. Commands, 11. File map, 1. The short version, 2. The whole system, end to end, 3. What the demo does, step by step, 4. The three pipelines in plain terms, 5. How the scores are worked out, 6. Reading the output on screen (+20 more)

### Community 33 - "e"
Cohesion: 0.21
Nodes (33): ae(), at(), be(), ce(), de(), e(), ee(), fe() (+25 more)

### Community 34 - "loop_executor.py"
Cohesion: 0.10
Nodes (18): ABC, build_cells(), build_retrievers(), main(), _parse_args(), Namespace, Runs a single benchmark cell, one (source_set, query_id, pipeline, k_value) run,, Construct only the requested retrievers, importing each module     lazily so an (+10 more)

### Community 35 - "atomic_search_widget.js"
Cohesion: 0.25
Nodes (12): connectedCallback(), H(), k(), L(), O(), _onConnect(), p(), te() (+4 more)

### Community 64 - "test_async_judge.py"
Cohesion: 0.13
Nodes (22): compute_deterministic_metrics(), parse_judge_score(), Pull a 1-5 integer out of the Judge's reply, clamped into range.      Prefers th, Computes the code-computed metric columns for one gate row (no LLM).      eviden, async_judge: quadrant-filtered few-shot, no search tool, folded metrics.  The Ju, Guardrails 4b reserves citation matching for deterministic code.      citation_a, The rubric is calibrated against exemplars that show no citations, so     words, parse_judge_score() prefers the JSON object; the rubric must keep     asking for (+14 more)

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
Cohesion: 0.17
Nodes (10): _build_target_message(), Judge, judge_jeq_rows(), Wraps the Qwen judge client; enforces the fixed model and temperature.      The, Scores one row, retrying transient failures with exponential backoff.      The J, Scores the JEQ gate rows. Thin wrapper over judge_rows for the gate path., _score_with_retry(), test_judge_rejects_nonzero_temperature() (+2 more)

### Community 167 - "Docstring and Comment Simplification Implementation Plan"
Cohesion: 0.10
Nodes (20): Docstring and Comment Simplification Implementation Plan, Global Constraints, Phase 2: test files, Self-review, Steps, Task 0: Style contract and the AST equivalence checker, Task 10: Pipeline tests (11 files), Task 11: Dataset-generation tests (8 files) (+12 more)

### Community 168 - "_retry_decorator"
Cohesion: 0.07
Nodes (27): A cold session's first five commands, Autonomous Failure Policy, Autonomous Project Completion (Phases 6b–8) Implementation Plan, Failures that are hard stops, File Structure, Fix it yourself, Global Constraints, Interrupted runs are safe to re-run (+19 more)

### Community 169 - "Project Overview and FAQ"
Cohesion: 0.11
Nodes (17): How are the questions generated and checked?, How do the three pipelines differ architecturally?, How do we grade the pipeline answers?, How do we test them fairly?, Project Overview and FAQ, What are the four question types?, What are the three pipelines?, What does "cost" mean in this project? (+9 more)

### Community 170 - "t"
Cohesion: 0.17
Nodes (24): judge_rows(), Scores one source set: deterministic metrics plus judge_score, one write each., FakeJudge, _golden(), _query_row(), Generalised judging over any source set, with a rubric-aware resume.  The resume, The failure this whole mechanism exists to prevent., Records which rows it was asked to score and returns a fixed band. (+16 more)

### Community 171 - "atomic_search_widget.js"
Cohesion: 0.16
Nodes (23): connectedCallback(), E(), f(), G(), H(), k(), L(), O() (+15 more)

### Community 172 - "l"
Cohesion: 0.11
Nodes (26): _bootstrap_ci(), build_report(), compare(), _fmt(), group_by(), _hours(), load_rows(), main() (+18 more)

### Community 173 - "Answerer"
Cohesion: 0.10
Nodes (24): Model routing, throttle flag, and env loading for the whole benchmark build., Answerer, build_prompt(), parse_citations(), NodeWithScore, Turns a query plus its retrieved nodes into a cited answer.  All three pipelines, Node ids cited in `raw_text`, deduplicated, first-appearance order., Builds the user-role message: retrieved sources, then the question. (+16 more)

### Community 174 - "test_database_manager_judge.py"
Cohesion: 0.15
Nodes (22): _build_under_old_schema(), _golden(), _jeq(), Read/update helpers on database_manager for the Judge.  Additive: upsert_result, A results table carrying the retired 1-10 CHECK, with one real row., SQLite cannot alter a CHECK and CREATE TABLE IF NOT EXISTS never touches     an, DROP TABLE takes its indexes with it, and the crash-resume path queries     by q, A leftover 6-10 score predates the collapse. The rebuild would carry it     into (+14 more)

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
Cohesion: 0.09
Nodes (17): figures(), _png_bytes(), Path, build_report: assembling the standalone results page.  The report is a deliverab, The slug is the template's key; a filename change must not be silent., The key is the slug alone; one field too few leaves the number on it., 3 of 4 JEQ rows agree in the fixture, so the page must say 75.0%., 36000s structural against a 60s BM25 build is a factor of 600. (+9 more)

### Community 186 - "test_validation_gate.py"
Cohesion: 0.20
Nodes (4): validation_gate: run the 60 JEQ gate outputs, then judge them.  The gate runs th, _parse_args(), Namespace, Validation-gate orchestrator: runs the 20 JEQ questions through P1/P2/P3 at a si

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
Cohesion: 0.15
Nodes (19): CallbackManager, Any, Return a client for the model and provider routed to this stage., Return a LlamaIndex LLM instance for the given provider and model.          Args, Forwarded so events from llama_index's llm_chat_callback() decorator     (token-, test_get_client_wires_callback_manager_when_provided(), _fake_response(), Tests for LLMFactory's client construction.  Confirms the retry/semaphore-wrappe (+11 more)

### Community 192 - "test_groq_client_backoff.py"
Cohesion: 0.08
Nodes (30): BaseException, call_groq(), get_groq_client(), Any, AsyncOpenAI, Groq client provider.  Builds an AsyncOpenAI client for Groq's OpenAI-compatible, Return an AsyncOpenAI client configured for Groq with retries and concurrency li, Send a chat completion to Groq and return the raw response. (+22 more)

### Community 193 - "qe"
Cohesion: 0.17
Nodes (13): ct(), et(), it(), ni(), ot(), qe(), Qt(), rt() (+5 more)

### Community 195 - "search_filing_nodes"
Cohesion: 0.09
Nodes (40): BaseModel, FunctionTool, _build_search_tool(), critique_query(), Critic: independently re-derives an answer using a local search tool.  Uses qwen, Wraps search_filing_nodes as a LlamaIndex tool bound to one filing.      The nod, Runs the Critic's search-then-answer loop.      Returns {"cited_node_ids": [...], Local, dependency-free keyword search the Critic uses to find evidence.  Not a r (+32 more)

### Community 198 - "test_node_builder.py"
Cohesion: 0.32
Nodes (12): _fake_llm_client(), _node(), NodeWithScore, OpenAILike, The whole payload, both roles, carries only the question, node ids,     node tex, Markers stay in raw_text; only parse_citations strips them., _run_answer(), _sent_messages() (+4 more)

### Community 200 - "Working in this repo"
Cohesion: 0.06
Nodes (34): Deliverables, Deliverables, Deliverables, Deliverables, Deliverables, Deliverables, Deliverables, Deliverables (+26 more)

### Community 202 - "4. Implementation Guardrails (Binding)"
Cohesion: 0.06
Nodes (21): _download_bytes(), fetch_filing(), _find_10k(), _get_json(), _headers(), Downloads SEC 10-K filings, resolving filing URLs from SEC EDGAR's public JSON A, resolve_cik(), build_nodes() (+13 more)

### Community 203 - "Quickstart"
Cohesion: 0.15
Nodes (24): AnswerResult, _query(), loop_executor: cell construction, resume-skip, throttle, row shape.  Uses a stub, P2 drives its DB read with asyncio.run() inside sync retrieve(), which     raise, Default the suite to unthrottled; the throttle tests opt back in., golden_queries is the Judge's exemplar set and must stay unreachable     from an, _seed(), StubAnswerer (+16 more)

### Community 204 - "fetch_filings.py"
Cohesion: 0.07
Nodes (29): 10. Academic Rigor and Methodological Principles, 1. Research Overview and Core Objectives, 2. Data Strategy and Ingestion Parsing Architecture, 3. The 140-Query Benchmark Dataset: Three Disjoint Sets, 4. Open-Model Generation and Adversarial Verification Architecture, 5. The Human Anchor: Two Roles, Two Sets, 6. Multi-Pipeline Architectural Registry, 7. Tri-Pillar Evaluation, the Judge-Validation Gate, and the Full Benchmark (+21 more)

### Community 205 - "Guardrails are binding, not advisory"
Cohesion: 0.12
Nodes (14): _dumps(), get_all_query_texts(), insert_golden_query(), insert_judge_validation(), insert_query(), SQLite access layer: five isolated tables, WAL mode, JSON-in-TEXT convention.  T, (query_id, query_text) pairs from all three quadrant-fill tables     (queries, g, Replace one exemplar's candidate answer.      Separate from update_golden_query_ (+6 more)

### Community 208 - "Monitor Skill"
Cohesion: 0.09
Nodes (22): AAPL_2023_n0019 (text), AAPL_2023_n0073 (text), AAPL_2023_n0417 (text), AAPL_2023_n0568 (text), AAPL_2023_n0611 (table), AAPL_2024_n0108 (text), AAPL_2024_n0165 (text), AAPL_2024_n0197 (text) (+14 more)

### Community 211 - "quickstart.md"
Cohesion: 0.10
Nodes (19): author, bugs, url, dependencies, claude-mem, description, directories, doc (+11 more)

### Community 212 - "MSFT_2023.md"
Cohesion: 0.18
Nodes (16): build_index_for_document(), index_path(), is_document_indexed(), main(), Path, Builds the per-document P2 BM25 index: one pickled BM25Okapi corpus per filing u, Custom BM25 tokenizer: preserves numbers, decimals, percentages and currency amo, tokenize() (+8 more)

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
Cohesion: 0.27
Nodes (10): main(), parse_label_markdown(), Reads the filled-in golden_queries_to_label.md back into golden_queries.  write_, An entry missing only the Good Example line must still parse, not     silently v, test_parse_label_markdown_handles_entry_missing_good_example_line(), test_parse_label_markdown_handles_multiple_entries_without_bleeding(), test_parse_label_markdown_raises_on_non_integer_score(), test_parse_label_markdown_raises_on_unrecognized_is_good_value() (+2 more)

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

### Community 237 - "WMT_2025.md"
Cohesion: 0.11
Nodes (17): aggregate_results: tri-pillar aggregation and paired pipeline comparison.  The s, Ties padding the sample must not make a lopsided split look weaker., A large point estimate whose interval spans zero is not evidence., exact_match is NULL by design on Q2/Q4; that must not read as 0.0., _row(), test_a_cell_only_one_pipeline_answered_is_excluded_from_the_pairing(), test_a_coin_flip_difference_is_not_reported_as_significant(), test_a_column_that_is_null_everywhere_reports_none_not_zero() (+9 more)

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
Cohesion: 0.21
Nodes (14): MockLLM, P3StructuralRetriever, NodeWithScore, _ForbiddenLLM, Fails loudly if the query path ever calls an LLM., _seed_index(), test_retrieve_filters_to_given_document_id(), test_retrieve_makes_no_llm_call() (+6 more)

### Community 245 - "Deviations from Original Proposed Idea"
Cohesion: 0.05
Nodes (39): 10. P3 index build bypasses the shared Groq client wrapper (2026-07-22), 11. LlamaParse table-header extraction defect (2026-07-26), 12. Dataset-generation retry and grading were too rigid (2026-07-28), 13. Embedding library unavailable on this platform (2026-07-28), 14. No token-size guard on Generator prompts (2026-07-29), 15. P3 summariser model judged too weak (2026-07-29), 16. GQ hand-labelling scale had no validation (2026-07-29), 17. Query ID format was long and quadrant-label-ambiguous (2026-07-29) (+31 more)

### Community 246 - "FastEmbedReranker"
Cohesion: 0.12
Nodes (14): BaseNodePostprocessor, model_cache_dir(), The directory fastembed downloads and loads ONNX models from.      Overridable t, Path, FastEmbedReranker, NodeWithScore, Cross-encoder reranker for P1, backed by fastembed's ONNX TextCrossEncoder.  No, Path (+6 more)

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

### Community 260 - "config.py"
Cohesion: 0.17
Nodes (6): Both benchmark stages run on OpenRouter, pinned to one upstream host.      OpenR, Guardrails §2: no model may grade its own output., A reasoning-tuned model with no cap can emit an unbounded chain and hang     the, test_answerer_and_judge_remain_different_families(), test_answerer_and_judge_route_to_openrouter_with_pinned_provider(), test_every_openrouter_stage_caps_reasoning()

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
Cohesion: 0.29
Nodes (6): 1. P3 retrieval pipeline (`as_retriever(retriever_mode="embedding")`), 2. Full unthrottled ingestion (MSFT ×3, TSLA ×3 — 6 filings), 3. Full migration off `llama_cloud_services` to the raw `llama-cloud` SDK, 4. Index build cost measured for P3 only, and only into a git-ignored log, Deferred Items Log, Format

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
Cohesion: 0.29
Nodes (6): 1. LlamaParse table header misalignment, 2. Filing-to-markdown conversion artefacts in the node corpus, 3. Redundant questions and answer restatement within the 100-query set, 4. Construct concentration within the Q4_Implicit_Table quadrant, Format, Research Issues Log

### Community 279 - "check_docstrings_only.py"
Cohesion: 0.13
Nodes (19): AST, Exception, FileNotFoundAtRevision, git_show(), GitError, main(), normalise(), Verifies that a rewrite touched only docstrings, never executable code.  Compare (+11 more)

### Community 283 - "build_report.py"
Cohesion: 0.20
Nodes (18): build_cost_note(), build_cost_table(), build_html(), _bytes(), comparison_table(), _duration(), embed(), figure_block() (+10 more)

### Community 284 - "index_build_cost.py"
Cohesion: 0.18
Nodes (18): build_snapshot(), _builder(), _directory_bytes(), document_ids(), load_attempts(), load_snapshot(), _main(), measure_pipeline() (+10 more)

### Community 286 - "LLMFactory"
Cohesion: 0.13
Nodes (13): LLMFactory, Static factory that returns LlamaIndex-compatible LLM client objects., _FakeChoice, _FakeCompletion, Tests for the LLM client abstraction (OpenRouter provider)., asyncio.TimeoutError carries no message, so logging it with %s emitted     "erro, Transparent to kwargs despite the retry/semaphore/rate-limit wrapping., No caching, so client identity is not guaranteed and is not     asserted here; o (+5 more)

### Community 305 - "score_gate_outputs.py"
Cohesion: 0.16
Nodes (16): compute_agreement_rate(), _parse_args(), prompt_human_scores(), Namespace, Reference scoring and the Judge validation gate.  Collects a reference score for, Prompt for any missing human scores, then compute and report the gate., True when the two 1-5 scores agree within the tolerance band on 0-100., Agreement Rate and gate verdict over rows carrying both scores.      Every row m (+8 more)

### Community 307 - "async_judge.py"
Cohesion: 0.15
Nodes (13): _format_exemplar(), Scores each JEQ gate output 1-5 against its ground truth and writes the determin, A short digest of everything that determines a judge score.      The system prom, Rescales a 0-100 human score to the Judge's 1-5 scale, clamped., _rescale_to_1_5(), rubric_fingerprint(), Band edges are explicit, not round(score / 20): banker's rounding would     send, The 1-10 scale left bands 1, 3, 6, 7 and 8 with no exemplar, so the     Judge ne (+5 more)

### Community 308 - "build_prefix"
Cohesion: 0.18
Nodes (13): build_prefix(), Builds the cacheable system message for one quadrant: rubric plus exemplars., _exemplar(), _fake_judge_client(), ONE live, throttled smoke test proving Judge.score_row() speaks Groq's real chat, Exercises the real Qwen judge call end to end, with no client mocking.      Prov, test_judge_score_row_live_round_trip_against_real_groq_api(), OpenAILike (+5 more)

### Community 309 - "Judge Scoring Criteria (1 to 5)"
Cohesion: 0.14
Nodes (13): 1. How the scale is anchored, 2. The six factors, applied in this order, 3. The bands, 4. Explicit non-factors, 5. Tie-breaker, 6. Independence rules for the gate, 7. Known ground-truth defects, Judge Scoring Criteria (1 to 5) (+5 more)

### Community 310 - "Judge Validation and Execution Methodology"
Cohesion: 0.14
Nodes (13): 10. Cost model, measured rather than estimated, 1. Retrieval depth reduced to K ∈ {2, 3, 5}, 2. Provider migration and determinism controls, 3. Judge calibration set, 4. Rubric reconciled with the exemplars, 5. The blinding protocol for gate scoring, 6. Gate result, 7. Gate outputs at K = 5, all three pipelines (+5 more)

### Community 311 - "test_llm_client_nim.py"
Cohesion: 0.17
Nodes (10): _FakeChoice, _FakeCompletion, Tests for the LLM client abstraction (NIM provider)., callback_manager omitted defaults to None; construction still succeeds., Transparent to kwargs despite the retry/semaphore/rate-limit wrapping., No caching: each call builds a new client, so identity is not     asserted here,, test_get_client_omitting_callback_manager_still_constructs(), test_get_llm_client_returns_equivalent_client_nim() (+2 more)

### Community 312 - "_loads"
Cohesion: 0.17
Nodes (12): get_golden_queries(), get_golden_queries_by_quadrant(), get_jeq_judging_rows(), get_judging_rows(), get_queries(), get_results(), _loads(), Benchmark queries for one results.source_set value.      Only 'PQ' and 'JEQ' are (+4 more)

### Community 313 - "test_async_generator.py"
Cohesion: 0.30
Nodes (10): generate_query(), Generator: proposes a query, ground truth answer and citations for one filing se, _fake_llm_client(), OpenAILike, Pins generate_query()'s LLM call shape to LlamaIndex's real achat() interface, u, The user-role prompt text read back from the serialised     {"role", "content"}, _sent_user_content(), test_generate_query_first_attempt_has_no_feedback_in_prompt() (+2 more)

### Community 314 - "gate_reference_scores.py"
Cohesion: 0.24
Nodes (11): apply_scores(), Reference scores for the validation gate, written without the Judge's.  On this, Rebuilds the token -> result_id mapping render_rows_for_scoring used.      Re-ru, Write one reference score per token; returns the count written.      scores is k, An opaque stand-in for result_id, keyed by its position after shuffling.      De, rows, reordered with the fixed seed so pipeline never lines up with     token po, The gate rows, shuffled and reduced to the fields a scorer may see.      Each ro, render_rows_for_scoring() (+3 more)

### Community 315 - "P1VectorRetriever"
Cohesion: 0.27
Nodes (8): P1VectorRetriever, NodeWithScore, P1: semantic vector retrieval.  Filters to the query's own document_id, which is, _seed_collection(), test_retrieve_filters_to_given_document_id(), test_retrieve_respects_k(), test_retrieve_returns_empty_list_for_unindexed_document_id(), test_retrieve_returns_most_relevant_node_first()

### Community 316 - "test_gq_calibration.py"
Cohesion: 0.17
Nodes (7): Shape guards on the Judge's calibration set.  These assert properties of the liv, A set clustered at one end teaches the Judge only that end., build_prefix() shows only one quadrant's 5 exemplars, so each     quadrant must, A 'bad' exemplar whose output equals the ground truth is incoherent., test_bad_exemplars_differ_from_ground_truth(), test_every_quadrant_has_both_polarities(), test_scores_span_the_range()

### Community 317 - "model_cache.py"
Cohesion: 0.29
Nodes (8): Durable on-disk location for the fastembed ONNX models.  fastembed defaults to a, P3: structural summary-tree retrieval.  Loads the per-filing TreeIndex built by, build_index_for_document(), get_collection(), is_document_indexed(), main(), Path, Builds the shared P1 vector index: one Chroma collection, metadata-tagged by doc

### Community 318 - "build_summary_index.py"
Cohesion: 0.36
Nodes (10): append_cost_log(), build_index_for_document(), confirm_build(), _final_dir(), is_built(), main(), Path, Builds and persists one hierarchical TreeIndex per filing.  This is the only ind (+2 more)

### Community 319 - "report.py"
Cohesion: 0.29
Nodes (7): banner(), how_to_read(), query_block(), Terminal rendering for the demo. Presentation only, no logic., Strip the repeated document prefix so the ranked lists stay readable., short(), summary_block()

### Community 320 - "repair_answer_keys.py"
Cohesion: 0.29
Nodes (9): main(), plan(), Connection, Repairs the benchmark answer keys, then refreshes anything scored against them., The per-table citation repair plan, computed but not written., Recomputes the derived metric columns for one source set. Returns rows written., Prints the plan and returns the ids of any row that could not be verified., recompute_metrics() (+1 more)

### Community 321 - "init_db"
Cohesion: 0.32
Nodes (8): init_db(), _migrate_golden_queries_schema(), _migrate_results_add_judge_fingerprint(), _migrate_results_score_checks(), Connection, Adds results.judge_fingerprint to a database built before it existed.      Unlik, CREATE TABLE IF NOT EXISTS never alters an already-existing table, so a     gold, Tightens results' judge_score/human_score CHECKs from 1-10 to 1-5.      The scor

### Community 322 - "TextNode"
Cohesion: 0.25
Nodes (5): NodeWithScore, nodes_to_llama_nodes(), Converts nodes-table rows into LlamaIndex TextNode objects.  Kept separate from, NodeWithScore, TextNode

### Community 323 - "gq_label_export.py"
Cohesion: 0.50
Nodes (4): main(), Writes golden_queries_to_label.md so a researcher can hand-write the 'why this a, render_label_markdown(), test_render_label_markdown_includes_query_and_blank_fields()

### Community 324 - "_seed_all_pipelines"
Cohesion: 0.40
Nodes (5): _jv(), n_queries JEQ queries, each with a JEQ row for all three pipelines --     the na, The field whitelist alone is not enough: get_jeq_judging_rows orders     by resu, _seed_all_pipelines(), test_token_order_does_not_track_pipeline()

## Knowledge Gaps
- **652 isolated node(s):** `@playwright/mcp`, `@drawio/mcp`, `$schema`, `plugin`, `@opencode-ai/plugin` (+647 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **152 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `token_f1()` connect `test_metrics.py` to `test_async_judge.py`, `exact_match`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **Why does `compute_deterministic_metrics()` connect `test_async_judge.py` to `repair_answer_keys.py`, `exact_match`, `async_judge.py`, `test_metrics.py`?**
  _High betweenness centrality (0.007) - this node is a cross-community bridge._
- **Why does `t()` connect `e` to `atomic_search_widget.js`, `test_config.py`, `ally.b2f86d8b36422ca86a9f.js`, `o`, `f`, `jQueryPrivate.js`, `init`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **Are the 52 inferred relationships involving `o()` (e.g. with `A()` and `an()`) actually correct?**
  _`o()` has 52 INFERRED edges - model-reasoned connections that need verification._
- **Are the 52 inferred relationships involving `o()` (e.g. with `A()` and `an()`) actually correct?**
  _`o()` has 52 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `t()` (e.g. with `ae()` and `b()`) actually correct?**
  _`t()` has 54 INFERRED edges - model-reasoned connections that need verification._
- **Are the 54 inferred relationships involving `t()` (e.g. with `ae()` and `b()`) actually correct?**
  _`t()` has 54 INFERRED edges - model-reasoned connections that need verification._