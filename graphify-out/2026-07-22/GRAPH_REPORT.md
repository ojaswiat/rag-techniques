# Graph Report - rag-techniques  (2026-07-21)

## Corpus Check
- 47 files · ~77,379 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 586 nodes · 487 edges · 170 communities (33 shown, 137 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 21 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `387930f6`
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
- TODO.md Active Task List (empty)

## God Nodes (most connected - your core abstractions)
1. `System architecture` - 10 edges
2. `6. Phase-by-Phase Architecture` - 9 edges
3. `render_all()` - 8 edges
4. `CLAUDE.md — Agent Instructions` - 8 edges
5. `4. Implementation Guardrails (Binding)` - 7 edges
6. `Human Intervention Ledger (read this before starting)` - 7 edges
7. `Benchmark design` - 7 edges
8. `Working in this repo` - 7 edges
9. `2. Groq Free Tier — The LLM Workload` - 7 edges
10. `9. Limitations and Caveats` - 7 edges

## Surprising Connections (you probably didn't know these)
- `ProjectProposal (earlier draft of the COMP702 proposal)` --semantically_similar_to--> `Design and Specification Proposal v1.0.0 (COMP702)`  [INFERRED] [semantically similar]
  resources/artifacts/ProjectProposal.pdf → resources/artifacts/Proposal_v1.0.0.pdf
- `Template Section Skeleton (13 numbered sections)` --implements--> `Required Proposal Structure (title page through references)`  [INFERRED]
  resources/docs/ProposalTemplate.pdf → resources/docs/ProposalGuidelines.pdf
- `Design and Specification Proposal v1.0.0 (COMP702)` --implements--> `Required Proposal Structure (title page through references)`  [INFERRED]
  resources/artifacts/Proposal_v1.0.0.pdf → resources/docs/ProposalGuidelines.pdf
- `Design and Specification Proposal v1.0.0 (COMP702)` --implements--> `Title Page Layout (title, submitted by, supervisor, school)`  [INFERRED]
  resources/artifacts/Proposal_v1.0.0.pdf → resources/docs/ProposalTemplate.pdf
- `Draft Development and Implementation Summary (§4)` --conceptually_related_to--> `LlamaIndex as Shared Retriever Backbone`  [INFERRED]
  resources/artifacts/ProjectProposal.pdf → resources/artifacts/Proposal_v1.0.0.pdf

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three retrieval paradigms share one answerer and one judge** — resources_artifacts_proposal_v1_0_0_p1_vector_pipeline, resources_artifacts_proposal_v1_0_0_p2_bm25_pipeline, resources_artifacts_proposal_v1_0_0_p3_structural_pipeline, resources_artifacts_proposal_v1_0_0_shared_answerer, resources_artifacts_proposal_v1_0_0_llm_judge [EXTRACTED 1.00]
- **Zero-spend quota safety pattern (throttle, WAL resume, disjoint sets, Groq free tier)** — resources_artifacts_proposal_v1_0_0_groq_free_tier, resources_artifacts_proposal_v1_0_0_local_throttle, resources_artifacts_proposal_v1_0_0_sqlite_wal_store, resources_artifacts_proposal_v1_0_0_risk_management_plan [INFERRED 0.85]
- **Guidelines and template constrain the submitted proposal** — resources_docs_proposalguidelines_required_structure, resources_docs_proposaltemplate_section_skeleton, resources_artifacts_proposal_v1_0_0_document, resources_artifacts_projectproposal_document [INFERRED 0.85]

## Communities (170 total, 137 thin omitted)

### Community 2 - "Proposal Compliance and Benchmark Design"
Cohesion: 0.08
Nodes (30): ProjectProposal (earlier draft of the COMP702 proposal), Draft Development and Implementation Summary (§4), BCS Project Criteria Mapping, 140-Query Human-Anchored Benchmark, Chen et al. (2021) FinQA Numerical Reasoning over Financial Data, Disjoint Query Sets PQ/GQ/JEQ (100/20/20), Design and Specification Proposal v1.0.0 (COMP702), Statement of Ethical Compliance A0 (+22 more)

### Community 4 - "Research Question and Literature Base"
Cohesion: 0.13
Nodes (19): Citation Audit (detects coincidentally-correct answers), Three Evaluation Pillars (retrieval, answer-quality, efficiency), Judge Validation Gate (>80% human agreement), Karpukhin et al. (2020) Dense Passage Retrieval, Lewis et al. (2020) Retrieval-Augmented Generation, Liu et al. (2024) Lost in the Middle, LLM Judge (Qwen3-32b), Nogueira and Cho (2019) Passage Re-ranking with BERT (+11 more)

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
Cohesion: 0.08
Nodes (6): BaseException, Model routing, throttle flag, and env loading for the whole benchmark build., _is_rate_limit_error(), Resilient async Groq wrapper: tenacity backoff on 429 + bounded concurrency.  Se, Reusable LOCAL_TEST_THROTTLE pattern for every Phase 2-7 loop script.  Guardrail, _FakeResponse

### Community 15 - "monitor_lib.py"
Cohesion: 0.14
Nodes (22): ArgumentParser, add_root_arg(), branch_chip(), esc(), git_branch(), load_json(), load_profile(), monitor_dir() (+14 more)

### Community 16 - "Benchmark design"
Cohesion: 0.10
Nodes (18): Benchmark design, Evaluation: three pillars, How queries get made: generator versus critic, Scale and honesty, The 140-query dataset, The coincidental-correctness trap, The four quadrants, The judge-validation gate (+10 more)

### Community 17 - "Proposal_v1.0.0_8228ebe1.md"
Cohesion: 0.10
Nodes (19): 10. Project Plan, 11. Risks and Contingency Plans, 12. References, 1. Project Description, 2.1 Aims, 2.2 Requirements: Essential, 2.3 Requirements: Desirable, 2. Aims and Requirements (+11 more)

### Community 18 - "Budget.md"
Cohesion: 0.11
Nodes (16): 1. Cost Model at a Glance, 2. Groq Free Tier — The LLM Workload, 3. LlamaParse — The Ingestion Workload, 4. Local Compute — $0, but Not Free of Constraints, 5. What Changed From the Original Budget, 6. Single Hard Rule, COMP702 Dissertation — Cost & Resource Plan, Cost-control rules (+8 more)

### Community 19 - "1. Core scales"
Cohesion: 0.12
Nodes (16): 1.1 Primary Blue, 1.2 Neutral (blue-gray), 1.3 Gold accent — reserved, 1.4 Auxiliary evaluation colors, 1. Core scales, 2.1 Categorical (5+ series), 2.2 Sequential (ordinal data, heatmaps), 2.3 Diverging (delta / baseline-relative data) (+8 more)

### Community 20 - "render_logs.py"
Cohesion: 0.20
Nodes (14): clean_logs(), clean_reports(), main(), Path, build_html(), _card(), _extract_tool(), _frag_card() (+6 more)

### Community 21 - "database_manager.py"
Cohesion: 0.13
Nodes (3): _dumps(), SQLite access layer: five isolated tables, WAL mode, JSON-in-TEXT convention.  S, upsert_result()

### Community 22 - "Human Intervention Ledger (read this before starting)"
Cohesion: 0.13
Nodes (14): Active — needs your input before Phase 1 is fully closed out, Global Constraints, Human Intervention Ledger (read this before starting), If uv.lock changed:, Not yet needed (deferred to their own phase), Passive — already handled, no action needed unless you want to change it, Phase 1 — Environment, Infrastructure & Cost Guardrails Implementation Plan, Phase 1 — Human Action Report (+6 more)

### Community 23 - "Working in this repo"
Cohesion: 0.14
Nodes (14): Anti-leakage, Determinism and state, Document and styling rules, Guardrails are binding, not advisory, Known stale or unresolved content, Loop safety, Rebuilding a `.docx` on macOS, The judge gate (+6 more)

### Community 24 - "Guardrails.md"
Cohesion: 0.14
Nodes (12): 1. Absolute Infrastructure Ban: No Per-Hour or Scale-to-Non-Zero Infrastructure, 2. Model Routing Matrix and Local Compute (per-stage LLM assignment), 3. Anti-Leakage: What Each Model May and May Not See, 4. Judge Few-Shot Filtering and the Mandatory Validation Gate, 4a. Dynamic few-shot filtering, 4b. The judge-validation gate (hard prerequisite for the full run), 5. Concurrency and Rate-Limiting Enforcement, 6. Relational Data Management and State Persistence (+4 more)

### Community 25 - "System architecture"
Cohesion: 0.15
Nodes (13): Citation markers, Key interfaces, Model routing, Numeric normalisation, Retrieval scope: per document, not cross-corpus, Shape of the system, System architecture, The central loop (+5 more)

### Community 26 - "render_report.py"
Cohesion: 0.42
Nodes (9): build_schema(), main(), Path, Build reports/manifest.json from an existing index if none exists.      Manifest, render_all(), render_dashboard(), render_reports_index(), render_template() (+1 more)

### Community 27 - "profile.py"
Cohesion: 0.36
Nodes (7): detect(), main(), _merge_list(), Path, Best-effort project detection. Language + build/test commands., Merge default field/kpi entries into existing by 'key', additively., reconcile()

### Community 28 - "logger.py"
Cohesion: 0.52
Nodes (6): load_schema(), log_operation(), main(), Path, render_entry(), validate()

### Community 29 - "RAG Techniques — COMP702 M.Sc. Dissertation"
Cohesion: 0.29
Nodes (6): Benchmark Design, RAG Techniques — COMP702 M.Sc. Dissertation, Repository Layout, Research Question, Status, The Three Pipelines

### Community 30 - "Typography — COMP702 Proposal / Dissertation / Slides"
Cohesion: 0.33
Nodes (5): Fonts, Paragraph and layout rules, Sizes (Word / PDF, A4, 2.5cm margins), Slide deck (PowerPoint), Typography — COMP702 Proposal / Dissertation / Slides

## Knowledge Gaps
- **302 isolated node(s):** `rag-techniques-benchmark`, `_FakeResponse`, `Repository Layout`, ``resources/` Subdirectory Reference`, `Reading Order for `resources/specs/`` (+297 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **137 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Working in this repo` connect `Working in this repo` to `Benchmark design`?**
  _High betweenness centrality (0.005) - this node is a cross-community bridge._
- **Why does `System architecture` connect `System architecture` to `Benchmark design`?**
  _High betweenness centrality (0.004) - this node is a cross-community bridge._
- **What connects `Return the project root that contains monitor/.`, `Fail fast if monitor is not initialised (no profile.json). Only     profile.py (`, `Current git branch name, or "" when unavailable.      Returns "" (never raises)` to the rest of the system?**
  _367 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Proposal Compliance and Benchmark Design` be split into smaller, more focused modules?**
  _Cohesion score 0.07586206896551724 - nodes in this community are weakly interconnected._
- **Should `Research Question and Literature Base` be split into smaller, more focused modules?**
  _Cohesion score 0.1286549707602339 - nodes in this community are weakly interconnected._
- **Should `Guardrails and Model Routing` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._
- **Should `Spec Document Set` be split into smaller, more focused modules?**
  _Cohesion score 0.05714285714285714 - nodes in this community are weakly interconnected._