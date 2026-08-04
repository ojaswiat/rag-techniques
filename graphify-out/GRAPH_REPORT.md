# Graph Report - rag-techniques  (2026-08-04)

## Corpus Check
- 178 files · ~7,314,443 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 8253 nodes · 8281 edges · 231 communities (86 shown, 145 thin omitted)
- Extraction: 99% EXTRACTED · 1% INFERRED · 0% AMBIGUOUS · INFERRED: 108 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b26b78f1`
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
- Human Intervention Ledger (read this before starting)
- Working in this repo
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
- MSFT_2025.md
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
- TODO.md
- TSLA_2023.md
- Human Intervention Ledger (read this before starting)
- run_ingestion.py
- JNJ_2024.md
- groq_client.py
- JNJ_2023.md
- JNJ_2025.md
- TSLA_2025.md
- WMT_2023.md
- WMT_2024.md
- WMT_2025.md
- Phase 1 — Human Action Report
- Phase 2 — Human Action Report
- quickstart.md
- AAPL_2023.md
- AAPL_2024.md
- AAPL_2025.md
- Proposal_v1.0.0_8228ebe1.md
- package.json
- groq_client.py
- LLMFactory
- test_groq_client_backoff.py
- database_manager.py
- llm_factory.py
- search_filing_nodes
- Benchmark design
- config.py
- test_node_builder.py
- test_parsing_audit.py
- Working in this repo
- 4. Implementation Guardrails (Binding)
- Quickstart
- fetch_filings.py
- Guardrails are binding, not advisory
- Monitor Skill
- gq_label_export.py
- _migrate_golden_queries_schema
- dependencies
- Note 7 – Interest income and interest expense
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
5. `search_filing_nodes()` - 11 edges
6. `_node()` - 11 edges
7. `critique_query()` - 10 edges
8. `check_query()` - 10 edges
9. `diagnose_rejection()` - 10 edges
10. `System architecture` - 10 edges

## Surprising Connections (you probably didn't know these)
- `test_format_underfill_summary_marks_only_below_target_quadrants()` --calls--> `format_underfill_summary()`  [INFERRED]
  project/tests/test_run_dataset_generation.py → project/dataset_generation/run_dataset_generation.py
- `_attempt_fill()` --calls--> `critique_query()`  [INFERRED]
  project/dataset_generation/run_dataset_generation.py → project/dataset_generation/async_critic.py
- `test_critique_query_default_return_shape_is_unchanged()` --calls--> `critique_query()`  [INFERRED]
  project/tests/test_async_critic.py → project/dataset_generation/async_critic.py
- `test_critique_query_raises_after_max_rounds_without_final_answer()` --calls--> `critique_query()`  [INFERRED]
  project/tests/test_async_critic.py → project/dataset_generation/async_critic.py
- `test_critique_query_return_messages_includes_full_history()` --calls--> `critique_query()`  [INFERRED]
  project/tests/test_async_critic.py → project/dataset_generation/async_critic.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three retrieval paradigms share one answerer and one judge** — resources_artifacts_proposal_v1_0_0_p1_vector_pipeline, resources_artifacts_proposal_v1_0_0_p2_bm25_pipeline, resources_artifacts_proposal_v1_0_0_p3_structural_pipeline, resources_artifacts_proposal_v1_0_0_shared_answerer, resources_artifacts_proposal_v1_0_0_llm_judge [EXTRACTED 1.00]
- **Zero-spend quota safety pattern (throttle, WAL resume, disjoint sets, Groq free tier)** — resources_artifacts_proposal_v1_0_0_groq_free_tier, resources_artifacts_proposal_v1_0_0_local_throttle, resources_artifacts_proposal_v1_0_0_sqlite_wal_store, resources_artifacts_proposal_v1_0_0_risk_management_plan [INFERRED 0.85]
- **Guidelines and template constrain the submitted proposal** — resources_docs_proposalguidelines_required_structure, resources_docs_proposaltemplate_section_skeleton, resources_artifacts_proposal_v1_0_0_document, resources_artifacts_projectproposal_document [INFERRED 0.85]

## Communities (231 total, 145 thin omitted)

### Community 2 - "Proposal Compliance and Benchmark Design"
Cohesion: 0.05
Nodes (49): ProjectProposal (earlier draft of the COMP702 proposal), Draft Development and Implementation Summary (§4), BCS Project Criteria Mapping, 140-Query Human-Anchored Benchmark, Chen et al. (2021) FinQA Numerical Reasoning over Financial Data, Citation Audit (detects coincidentally-correct answers), Disjoint Query Sets PQ/GQ/JEQ (100/20/20), Design and Specification Proposal v1.0.0 (COMP702) (+41 more)

### Community 4 - "Research Question and Literature Base"
Cohesion: 0.00
Nodes (843): 101.CAL XBRL Taxonomy Extension Calculation Linkbase Document.(b), 101.DEF XBRL Taxonomy Extension Definition Linkbase Document.(b), 101.INS The instance document does not appear in the interactive data file because its XBRL tags are embedded within the Inline XBRL document.(d), 101.LAB XBRL Taxonomy Extension Label Linkbase Document.(b), 101.PRE XBRL Taxonomy Extension Presentation Linkbase Document.(b), 101.SCH XBRL Taxonomy Extension Schema Document.(b), 10.1, 10.10 (+835 more)

### Community 5 - "Guardrails and Model Routing"
Cohesion: 0.15
Nodes (12): 1. Project Overview, 2. The `resources/` Folder — User Files and Steering Layer, 3. Styling and Document Rules, CLAUDE.md — Agent Instructions, graphify, monitor — operations log + reports, OpenWiki, PDF Verification (+4 more)

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
Cohesion: 0.11
Nodes (22): classify_section(), _node(), A single table node among mostly-text nodes is still enough material     for a Q, Two companies, each with one text section and one table section.     Pools must, `n` single-token words: tiktoken's cl100k_base encoding tokenizes     the bare w, The overwhelmingly common case: a section under _MAX_SECTION_TOKENS     must pro, Naive greedy packing would close the chunk right before n2 (the     6-token text, A single node (almost always one huge table) that alone exceeds     _MAX_SECTION (+14 more)

### Community 15 - "monitor_lib.py"
Cohesion: 0.00
Nodes (833): 10.10, 10.11, 10.12, 10.13, 10.14, 10.15, 10.15, 10.16 (+825 more)

### Community 16 - "Benchmark design"
Cohesion: 0.00
Nodes (783): 101.CAL XBRL Taxonomy Extension Calculation Linkbase Document.(b), 101.DEF XBRL Taxonomy Extension Definition Linkbase Document.(b), 101.INS The instance document does not appear in the interactive data file because its XBRL tags are embedded within the Inline XBRL document.(d), 101.LAB XBRL Taxonomy Extension Label Linkbase Document.(b), 101.PRE XBRL Taxonomy Extension Presentation Linkbase Document.(b), 101.SCH XBRL Taxonomy Extension Schema Document.(b), 104 Cover Page Interactive Data File (embedded within the Inline XBRL document and included in Exhibit 101)., 10.1 (+775 more)

### Community 17 - "Proposal_v1.0.0_8228ebe1.md"
Cohesion: 0.00
Nodes (517): 10. Environmental Risks, 1. Economic Conditions, 2. Competition, 3. Regulatory Risks, 4. Technology Risks, 5. Supply Chain Risks, 6. Financial Risks, 7. Legal Risks (+509 more)

### Community 18 - "Budget.md"
Cohesion: 0.11
Nodes (16): 1. Cost Model at a Glance, 2. Groq Free Tier — The LLM Workload, 3. LlamaParse — The Ingestion Workload, 4. Local Compute — $0, but Not Free of Constraints, 5. What Changed From the Original Budget, 6. Single Hard Rule, COMP702 Dissertation — Cost & Resource Plan, Cost-control rules (+8 more)

### Community 19 - "1. Core scales"
Cohesion: 0.12
Nodes (16): 1.1 Primary Blue, 1.2 Neutral (blue-gray), 1.3 Gold accent — reserved, 1.4 Auxiliary evaluation colors, 1. Core scales, 2.1 Categorical (5+ series), 2.2 Sequential (ordinal data, heatmaps), 2.3 Diverging (delta / baseline-relative data) (+8 more)

### Community 22 - "Human Intervention Ledger (read this before starting)"
Cohesion: 0.15
Nodes (12): Execution Handoff, Global Constraints, Human Intervention Ledger (read this before starting), Phase 1 — Environment, Infrastructure & Cost Guardrails Implementation Plan, Self-Review Notes, Task 1: Repo skeleton and pinned dependency manifest, Task 2: `database_manager.py` — five-table SQLite schema in WAL mode, Task 3: `groq_client.py` — resilient async Groq wrapper (backoff + semaphore) (+4 more)

### Community 23 - "Working in this repo"
Cohesion: 0.33
Nodes (5): Code blast radius (critical analysis), Current state (fact, not fix), Doubt #11 Impact Assessment: `query_id` Naming Format, Recommendation, Verdict

### Community 25 - "System architecture"
Cohesion: 0.15
Nodes (13): Citation markers, Key interfaces, Model routing, Numeric normalisation, Retrieval scope: per document, not cross-corpus, Shape of the system, System architecture, The central loop (+5 more)

### Community 28 - "logger.py"
Cohesion: 0.09
Nodes (22): AAPL_2023_n0019 (text), AAPL_2023_n0073 (text), AAPL_2023_n0417 (text), AAPL_2023_n0568 (text), AAPL_2023_n0611 (table), AAPL_2024_n0108 (text), AAPL_2024_n0165 (text), AAPL_2024_n0197 (text) (+14 more)

### Community 29 - "RAG Techniques — COMP702 M.Sc. Dissertation"
Cohesion: 0.29
Nodes (6): Benchmark Design, RAG Techniques — COMP702 M.Sc. Dissertation, Repository Layout, Research Question, Status, The Three Pipelines

### Community 30 - "Typography — COMP702 Proposal / Dissertation / Slides"
Cohesion: 0.33
Nodes (5): Fonts, Paragraph and layout rules, Sizes (Word / PDF, A4, 2.5cm margins), Slide deck (PowerPoint), Typography — COMP702 Proposal / Dissertation / Slides

### Community 31 - "monitor — companion skills in this project"
Cohesion: 0.00
Nodes (453): Accounting Principles, Activity for All Stock Plans, Addressing Racial Injustice and Inequity, Assets Recognized from Costs to Obtain a Contract with a Customer, AVAILABLE INFORMATION, BALANCE SHEETS, Basis for Opinion, Basis for Opinion (+445 more)

### Community 65 - "MSFT_2025.md"
Cohesion: 0.00
Nodes (429): Accounting Principles, Activity for All Stock Plans, Advertising, professional, marketplace, and gaming platform abuses, Assets Recognized from Costs to Obtain a Contract with a Customer, AVAILABLE INFORMATION, BALANCE SHEETS, Basis for Opinion, Basis for Opinion (+421 more)

### Community 167 - "todo.md"
Cohesion: 0.20
Nodes (9): Daily Cap Limit, Doubts, Final Run, Organise information, Plan a code base search, Planning Research, Research, Using information (+1 more)

### Community 168 - "TODO.md"
Cohesion: 0.01
Nodes (330): 2024 compared to 2023, 2024 compared to 2023, 2024 Notes, Accounts Receivable and Allowance for Doubtful Accounts, ANNUAL REPORT ON FORM 10-K FOR THE YEAR ENDED DECEMBER 31, 2024, Apprenticeships, As of December 31, 2024, the maturities of our operating and finance lease liabilities (excluding short-term leases) are as follows (in millions):, Automobile Manufacturer and Dealer Regulation (+322 more)

### Community 169 - "TSLA_2023.md"
Cohesion: 0.01
Nodes (326): 2018 CEO Performance Award, 2023 compared to 2022, 2023 compared to 2022, 2023 compared to 2022, 2024 Notes, Accounts Receivable and Allowance for Doubtful Accounts, ANNUAL REPORT ON FORM 10-K FOR THE YEAR ENDED DECEMBER 31, 2023, ANNUAL REPORT PURSUANT TO SECTION 13 OR 15(d) OF THE SECURITIES EXCHANGE ACT OF 1934 (+318 more)

### Community 170 - "Human Intervention Ledger (read this before starting)"
Cohesion: 0.15
Nodes (12): Execution Handoff, Global Constraints, Human Intervention Ledger (read this before starting), Phase 2 — Ingestion & Parsing Pipeline Implementation Plan, Self-Review Notes, Task 1: Filings manifest + Phase 2 dependencies, Task 2: `ingest/fetch_filings.py` — download filings from SEC EDGAR, Task 3: `ingest/parse_filing.py` — LlamaParse atomic-table parsing (+4 more)

### Community 171 - "run_ingestion.py"
Cohesion: 0.15
Nodes (12): build_nodes(), _is_table_block(), Splits parsed Markdown into atomic TextNode-shaped dicts.  A Markdown table is o, _is_cache_fresh(), parse_filing(), Parses raw filings into clean Markdown via LlamaParse (Cost-effective tier, atom, ingest_one(), main() (+4 more)

### Community 172 - "JNJ_2024.md"
Cohesion: 0.01
Nodes (321): 108 Jhonson&#x26;Jhonson, 10 Directors, executive officers and corporate governance, 10. Pensions and other benefit plans, 10 Year Shareholder Return Performance J&#x26;J vs. Indices, 11 Executive compensation, 11. Savings plan, 12. Capital and treasury stock, 12 Security ownership of certain beneficial owners and management and related stockholder matters (+313 more)

### Community 173 - "groq_client.py"
Cohesion: 0.26
Nodes (11): append_cost_log(), build_index_for_document(), _final_dir(), is_built(), main(), Path, Builds and persists one hierarchical TreeIndex per filing (Phase 3, Guardrails.m, _temp_dir() (+3 more)

### Community 174 - "JNJ_2023.md"
Cohesion: 0.01
Nodes (320): 108 Jhonson&#x26;Jhonson, 10. Directors, executive officers and corporate governance, 10-year CAGR, 10 Year Shareholder Return Performance J&#x26;J vs. Indices, 11. Executive compensation, 11. Savings plan, 12. Capital and treasury stock, 12. Security ownership of certain beneficial owners and management and related stockholder matters (+312 more)

### Community 175 - "JNJ_2025.md"
Cohesion: 0.01
Nodes (317): 10 Directors, executive officers and corporate governance, 10. Pensions and other benefit plans, 10 Year Shareholder Return Performance J&#x26;J vs. Indices, 11 Executive compensation, 11. Savings plan, 12. Capital and treasury stock, 12 Security ownership of certain beneficial owners and management and related stockholder matters, 13. Accumulated other comprehensive income (loss) (+309 more)

### Community 176 - "TSLA_2025.md"
Cohesion: 0.01
Nodes (311): 2025 CEO Interim Award, 2025 CEO Performance Award, 2025 CEO Performance Award, 2025 compared to 2024, 2025 compared to 2024, 2025 compared to 2024, 2025 compared to 2024, Accounts Receivable and Allowance for Doubtful Accounts (+303 more)

### Community 177 - "WMT_2023.md"
Cohesion: 0.01
Nodes (279): 10.1, 10.10, 10.11, 10.12, 10.13, 10.14, 10.15, 10.16 (+271 more)

### Community 178 - "WMT_2024.md"
Cohesion: 0.01
Nodes (279): 101.CAL, 101.DEF, 101.INS, 101.LAB, 101.PRE, 101.SCH, 104, 10.1 (+271 more)

### Community 179 - "WMT_2025.md"
Cohesion: 0.01
Nodes (244): 10. Exhibits, A reconciliation of gross unrecognized tax benefits from continuing operations is as follows:, Accumulated Other Comprehensive Income (Loss), Advertising Costs, Annual maturities of long-term debt during the next five years and thereafter are as follows:, ANNUAL REPORT ON FORM 10-K, As of January 31,, As of January 31, (+236 more)

### Community 180 - "Phase 1 — Human Action Report"
Cohesion: 0.33
Nodes (5): Active — needs your input before Phase 1 is fully closed out, Known cosmetic gaps (logged, not blocking), Not yet needed (deferred to their own phase), Passive — already handled, no action needed unless you want to change it, Phase 1 — Human Action Report

### Community 181 - "Phase 2 — Human Action Report"
Cohesion: 0.40
Nodes (4): Active — needs your input before Phase 2 is fully closed out, Not yet needed (deferred to their own phase), Passive — already handled, no action needed unless you want to change it, Phase 2 — Human Action Report

### Community 182 - "quickstart.md"
Cohesion: 0.11
Nodes (17): AGENTS.md — OpenCode Agent Instructions for rag-techniques, Binding Constraints (from `resources/specs/Guardrails.md`), Critical Architecture Facts, Critical Execution & Problem-Solving Rules, Development Commands, Document/Styling Rules (for deliverables), Environment, Execution Restrictions (+9 more)

### Community 185 - "AAPL_2023.md"
Cohesion: 0.01
Nodes (216): 2014 Employee Stock Plan, 2022, 2022 Employee Stock Plan, 2023, A reconciliation of the Company’s segment operating income to the Consolidated Statements of Operations for 2023, 2022 and 2021 is as follows (in millions):, Accounts Receivable, Advertising, Americas (+208 more)

### Community 186 - "AAPL_2024.md"
Cohesion: 0.01
Nodes (213): 15,115,823,000 shares of common stock were issued and outstanding as of October 18, 2024., 2014 Employee Stock Plan, 2022 Employee Stock Plan, Accounts Receivable, Advertising, Americas, Apple Inc., AppleCare (+205 more)

### Community 187 - "AAPL_2025.md"
Cohesion: 0.01
Nodes (202): 2022 Employee Stock Plan, 2023, 2024, 2024, 2025, 2025, Accounts Receivable, Advertising (+194 more)

### Community 188 - "Proposal_v1.0.0_8228ebe1.md"
Cohesion: 0.10
Nodes (19): 10. Project Plan, 11. Risks and Contingency Plans, 12. References, 1. Project Description, 2.1 Aims, 2.2 Requirements: Essential, 2.3 Requirements: Desirable, 2. Aims and Requirements (+11 more)

### Community 189 - "package.json"
Cohesion: 0.10
Nodes (19): author, bugs, url, dependencies, claude-mem, description, directories, doc (+11 more)

### Community 190 - "groq_client.py"
Cohesion: 0.18
Nodes (11): BaseException, Groq client provider.  Returns a ready-to-use AsyncOpenAI instance configured fo, get_nim_client(), AsyncOpenAI, NVIDIA NIM client provider.  Returns a ready-to-use AsyncOpenAI instance pointed, Return an AsyncOpenAI client configured for NIM endpoint.      The returned obje, _is_rate_limit_error(), Shared utilities for LLM clients. (+3 more)

### Community 191 - "LLMFactory"
Cohesion: 0.16
Nodes (13): LLMFactory, Any, Static factory that returns LlamaIndex-compatible LLM client objects., Return a LlamaIndex LLM instance for the given provider and model.          Para, Convenience: fetch client using config.MODEL_ROUTING for a stage., _FakeChoice, _FakeCompletion, Tests for the LLM client abstraction (NIM provider). (+5 more)

### Community 192 - "test_groq_client_backoff.py"
Cohesion: 0.17
Nodes (15): call_groq(), get_groq_client(), Any, AsyncOpenAI, Return an AsyncOpenAI client configured for Groq with retries and concurrency li, Drop‑in replacement for the original groq_client.call_groq., _FakeResponse, _FakeResult (+7 more)

### Community 193 - "database_manager.py"
Cohesion: 0.20
Nodes (8): _dumps(), get_golden_queries(), insert_golden_query(), insert_judge_validation(), insert_query(), _loads(), SQLite access layer: five isolated tables, WAL mode, JSON-in-TEXT convention.  S, upsert_result()

### Community 194 - "llm_factory.py"
Cohesion: 0.18
Nodes (10): generate_query(), Generator: proposes a query + ground truth + citations for one filing section., _DummyClient, _fake_response(), _FakeChoice, _FakeResponse, Async client with a configurable return value for create., test_generate_query_first_attempt_has_no_feedback_in_prompt() (+2 more)

### Community 195 - "search_filing_nodes"
Cohesion: 0.26
Nodes (12): Critic: independently re-derives an answer using a local search tool.  Uses qwen, Local, dependency-free keyword search the Critic uses to find evidence.  Not a r, search_filing_nodes(), _tokenize(), _node(), test_degenerate_tiny_node_does_not_outrank_real_node(), test_empty_content_node_skipped_without_zero_division(), test_excludes_zero_overlap_nodes() (+4 more)

### Community 196 - "Benchmark design"
Cohesion: 0.18
Nodes (11): Benchmark design, Evaluation: three pillars, How queries get made: generator versus critic, Scale and honesty, The 140-query dataset, The coincidental-correctness trap, The four quadrants, The judge-validation gate (+3 more)

### Community 200 - "Working in this repo"
Cohesion: 0.25
Nodes (8): Document and styling rules, Known stale or unresolved content, Rebuilding a `.docx` on macOS, The knowledge graph, The two-layer split, Verifying a PDF, Version drift, Working in this repo

### Community 202 - "4. Implementation Guardrails (Binding)"
Cohesion: 0.29
Nodes (7): 4. Implementation Guardrails (Binding), Fixed Model Routing, Infrastructure, Judge Gate, Loop Safety, Pipeline Constraints, Storage

### Community 203 - "Quickstart"
Cohesion: 0.29
Nodes (7): Current state and open items, Quickstart, Reading order for the specs, Repository layout, The one thing to know first, The shape of the project in one paragraph, Where to go next

### Community 204 - "fetch_filings.py"
Cohesion: 0.23
Nodes (6): _download_bytes(), fetch_filing(), _get_json(), _headers(), Downloads SEC 10-K filings, resolving real URLs from SEC EDGAR's public JSON API, resolve_cik()

### Community 205 - "Guardrails are binding, not advisory"
Cohesion: 0.33
Nodes (6): Anti-leakage, Determinism and state, Guardrails are binding, not advisory, Loop safety, The judge gate, The single hard rule

### Community 208 - "Monitor Skill"
Cohesion: 0.40
Nodes (4): Commands, Monitor Skill, Notes, Usage

### Community 209 - "gq_label_export.py"
Cohesion: 0.50
Nodes (4): main(), Writes golden_queries_to_label.md so the researcher can hand-write the 'why this, render_label_markdown(), test_render_label_markdown_includes_query_and_blank_fields()

### Community 210 - "_migrate_golden_queries_schema"
Cohesion: 0.50
Nodes (4): Connection, init_db(), _migrate_golden_queries_schema(), CREATE TABLE IF NOT EXISTS never alters an already-existing table, so     a gold

### Community 257 - "test_run_dataset_generation.py"
Cohesion: 0.06
Nodes (35): next_target(), First still-unfilled (table, quadrant) slot, searched quadrant-major     then ta, Flattens per-company section lists into one list by taking one     section from, _round_robin_interleave(), _empty_counts(), _isolate_progress_log(), main() calls _configure_logging() on every entry; a process that (in     theory), Simulates process A having already committed 2 accepted queries into     (querie (+27 more)

### Community 258 - "test_cross_check.py"
Cohesion: 0.10
Nodes (36): check_query(), citations_overlap(), diagnose_rejection(), embedding_similarity(), embedding_similarity_ok(), extract_numbers(), _get_embedding_model(), Deterministic accept/reject logic for the Generator/Critic adversarial loop.  Pl (+28 more)

### Community 259 - "run_dataset_generation.py"
Cohesion: 0.11
Nodes (29): Encoding, _accept_query(), append_failure_log(), _attempt_fill(), build_pools(), chunk_section(), _company_of(), _configure_logging() (+21 more)

### Community 260 - "async_critic.py"
Cohesion: 0.19
Nodes (9): critique_query(), Run the Critic's search-then-answer loop and return the parsed final     answer, ONE live, throttled smoke test proving async_critic.critique_query() actually sp, Exercises the REAL Groq function-calling protocol end to end -- no mocking     o, test_critique_query_live_round_trip_against_real_groq_api(), test_critique_query_default_return_shape_is_unchanged(), test_critique_query_raises_after_max_rounds_without_final_answer(), test_critique_query_return_messages_includes_full_history() (+1 more)

### Community 261 - "test_gq_labeling.py"
Cohesion: 0.27
Nodes (10): main(), parse_label_markdown(), Reads the filled-in golden_queries_to_label.md back into golden_queries., An entry from an older-format golden_queries_to_label.md (exported     before th, test_parse_label_markdown_handles_entry_missing_good_example_line(), test_parse_label_markdown_handles_multiple_entries_without_bleeding(), test_parse_label_markdown_raises_on_non_integer_score(), test_parse_label_markdown_raises_on_unrecognized_is_good_value() (+2 more)

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
- **7622 isolated node(s):** `$schema`, `plugin`, `@opencode-ai/plugin`, `$schema`, `plugin` (+7617 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **145 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `next_target()` connect `test_run_dataset_generation.py` to `run_dataset_generation.py`?**
  _High betweenness centrality (0.000) - this node is a cross-community bridge._
- **Are the 7 inferred relationships involving `values_match()` (e.g. with `test_values_match_exact_after_normalization()` and `test_values_match_falls_back_to_text_equality_with_no_numbers()`) actually correct?**
  _`values_match()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **Are the 4 inferred relationships involving `_attempt_fill()` (e.g. with `critique_query()` and `generate_query()`) actually correct?**
  _`_attempt_fill()` has 4 INFERRED edges - model-reasoned connections that need verification._
- **Are the 7 inferred relationships involving `search_filing_nodes()` (e.g. with `test_degenerate_tiny_node_does_not_outrank_real_node()` and `test_empty_content_node_skipped_without_zero_division()`) actually correct?**
  _`search_filing_nodes()` has 7 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `plugin`, `@opencode-ai/plugin` to the rest of the system?**
  _7753 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Proposal Compliance and Benchmark Design` be split into smaller, more focused modules?**
  _Cohesion score 0.04931972789115646 - nodes in this community are weakly interconnected._
- **Should `Research Question and Literature Base` be split into smaller, more focused modules?**
  _Cohesion score 0.002369668246445498 - nodes in this community are weakly interconnected._