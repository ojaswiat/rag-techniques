# Graph Report - .  (2026-07-21)

## Corpus Check
- Corpus is ~43,297 words - fits in a single context window. You may not need a graph.

## Summary
- 204 nodes · 256 edges · 12 communities (11 shown, 1 thin omitted)
- Extraction: 85% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 37 edges (avg confidence: 0.85)
- Token cost: 260,221 input · 0 output

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

## God Nodes (most connected - your core abstractions)
1. `CLAUDE.md Agent Instructions` - 9 edges
2. `Five-Table SQLite Schema (DDL)` - 7 edges
3. `Research Question: Semantic vs Statistical vs Structural Retrieval over SEC 10-K` - 7 edges
4. `Required Proposal Structure (title page through references)` - 7 edges
5. `Specs Reading Order` - 6 edges
6. `Fixed Model Routing Table` - 6 edges
7. `Oxford Ink Brand Palette` - 6 edges
8. `COMP702 Typography System` - 6 edges
9. `results table (960 rows, PQ + JEQ)` - 6 edges
10. `loop_executor.py` - 6 edges

## Surprising Connections (you probably didn't know these)
- `British English and Simple Punctuation Rule` --semantically_similar_to--> `Paragraph and Layout Rules`  [INFERRED] [semantically similar]
  CLAUDE.md → resources/assets/design/typography.md
- `SQLite aiosqlite WAL Storage` --shares_data_with--> `900-Run Full Benchmark`  [INFERRED]
  CLAUDE.md → README.md
- `README — RAG Techniques Project` --references--> `COMP702 M.Sc. Dissertation Project`  [EXTRACTED]
  README.md → CLAUDE.md
- `README — RAG Techniques Project` --references--> `resources/specs/Phase Plan.md`  [EXTRACTED]
  README.md → CLAUDE.md
- `P3 — Structural Summary-Tree Pipeline (LlamaIndex SummaryIndex)` --references--> `P3 Index Build Model (llama-3.1-8b-instant)`  [INFERRED]
  README.md → CLAUDE.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three-Paradigm RAG Comparative Benchmark** — readme_p1_semantic_pipeline, readme_p2_statistical_pipeline, readme_p3_structural_pipeline, readme_benchmark_140_queries, readme_research_question [EXTRACTED 1.00]
- **Anti-Self-Grading Model Routing Flow** — claude_role_generator, claude_role_critic, claude_role_answerer, claude_role_judge, claude_anti_self_grading_invariant, claude_judge_agreement_gate [EXTRACTED 1.00]
- **Oxford Ink Deliverable Style System** — resources_assets_design_palette_oxford_ink, resources_assets_design_typography_system, resources_assets_design_palette_component_mapping, resources_assets_design_typography_paragraph_rules, claude_native_office_elements_rule [INFERRED 0.85]
- **One Benchmark Cell Execution Flow** — resources_specs_architecture_loop_executor, resources_specs_architecture_retriever_interface, resources_specs_architecture_answerer, resources_specs_architecture_results_table, resources_specs_architecture_resume_unique_key [EXTRACTED 1.00]
- **Judge Validation Gate (60 outputs, >80% agreement)** — resources_specs_guardrails_judge_validation_gate, resources_specs_architecture_judge_validation_table, resources_specs_architecture_golden_queries_table, resources_specs_guardrails_dynamic_few_shot, resources_specs_phase_plan_phase_6 [EXTRACTED 1.00]
- **Zero-Spend Enforcement Pattern** — resources_specs_budget_zero_spend_model, resources_specs_guardrails_infrastructure_ban, resources_specs_budget_tpd_binding_constraint, resources_specs_budget_local_cpu_compute, resources_specs_guardrails_local_test_throttle [EXTRACTED 1.00]
- **Three retrieval paradigms share one answerer and one judge** — resources_artifacts_proposal_v1_0_0_p1_vector_pipeline, resources_artifacts_proposal_v1_0_0_p2_bm25_pipeline, resources_artifacts_proposal_v1_0_0_p3_structural_pipeline, resources_artifacts_proposal_v1_0_0_shared_answerer, resources_artifacts_proposal_v1_0_0_llm_judge [EXTRACTED 1.00]
- **Zero-spend quota safety pattern (throttle, WAL resume, disjoint sets, Groq free tier)** — resources_artifacts_proposal_v1_0_0_groq_free_tier, resources_artifacts_proposal_v1_0_0_local_throttle, resources_artifacts_proposal_v1_0_0_sqlite_wal_store, resources_artifacts_proposal_v1_0_0_risk_management_plan [INFERRED 0.85]
- **Guidelines and template constrain the submitted proposal** — resources_docs_proposalguidelines_required_structure, resources_docs_proposaltemplate_section_skeleton, resources_artifacts_proposal_v1_0_0_document, resources_artifacts_projectproposal_document [INFERRED 0.85]

## Communities (12 total, 1 thin omitted)

### Community 0 - "Schema, Quota and Judge Gating"
Cohesion: 0.07
Nodes (31): Context-Mass Standardisation Open Item, database_manager.py, golden_queries table (20 GQ), groq_client.py, JSON-in-SQLite List Column Convention, judge_validation table (20 JEQ), LlamaIndex as Common Backbone, Per-Document Retrieval Scope (+23 more)

### Community 1 - "Agent Steering and Document Style"
Cohesion: 0.09
Nodes (30): CLAUDE.md Agent Instructions, British English and Simple Punctuation Rule, COMP702 M.Sc. Dissertation Project, Post-build .docx Quarantine Clearing, graphify Knowledge Graph Workflow, Native Word/PowerPoint Elements Only, PDF Verification via LibreOffice and PyMuPDF, src/ Project Code Folder (+22 more)

### Community 2 - "Proposal Compliance and Benchmark Design"
Cohesion: 0.09
Nodes (26): BCS Project Criteria Mapping, 140-Query Human-Anchored Benchmark, Chen et al. (2021) FinQA Numerical Reasoning over Financial Data, Disjoint Query Sets PQ/GQ/JEQ (100/20/20), Statement of Ethical Compliance A0, Cross-Family Generator/Critic Adversarial Verification, Groq Free-Tier Serving ($0.00 spend model), LlamaParse Ingestion to Metadata-Enriched Nodes (+18 more)

### Community 3 - "Pipeline Build Phases and Metrics"
Cohesion: 0.09
Nodes (26): ChromaDB as P1 Vector Store, nodes table, judge/numeric_normalizer.py, LlamaParse Free Tier (Cost-effective), Local CPU Compute (bge models, rank_bm25), Zero-Spend Operating Model ($0.00), Absolute Infrastructure Ban (no per-hour / scale-to-non-zero), KeywordTableIndex Ban (P2 must stay statistical) (+18 more)

### Community 4 - "Research Question and Literature Base"
Cohesion: 0.11
Nodes (23): ProjectProposal (earlier draft of the COMP702 proposal), Draft Development and Implementation Summary (§4), Citation Audit (detects coincidentally-correct answers), Design and Specification Proposal v1.0.0 (COMP702), Three Evaluation Pillars (retrieval, answer-quality, efficiency), Judge Validation Gate (>80% human agreement), Karpukhin et al. (2020) Dense Passage Retrieval, Lewis et al. (2020) Retrieval-Augmented Generation (+15 more)

### Community 5 - "Guardrails and Model Routing"
Cohesion: 0.13
Nodes (19): Anti-Leakage Disjoint Query Sets, Anti-Self-Grading Invariant, Fixed Model Routing Table, Judge >80% Human-Agreement Gate, P2 Statistical Purity Constraint, P3 Index Build Model (llama-3.1-8b-instant), Pipeline Answerer Role (Llama 3.3 70B), Critic Role (Qwen3-32b with search) (+11 more)

### Community 6 - "Benchmark Execution and Citation Audit"
Cohesion: 0.17
Nodes (15): Shared Answerer (pipelines/answerer.py), [[node:<node_id>]] Citation Marker Convention, loop_executor.py, results table (960 rows, PQ + JEQ), UNIQUE(source_set, query_id, pipeline, k_value) Resume Key, source_set Discriminator Column, Anti-Leakage Rules (disjoint sets, no exemplars to pipelines), Crash-Resume State Persistence (+7 more)

### Community 7 - "Zero-Cost Storage and Specs Index"
Cohesion: 0.22
Nodes (11): Groq Free Tier LLM Hosting, LOCAL_TEST_THROTTLE Loop Safety Flag, resources/ Steering Layer, Resumable results UNIQUE Constraint, resources/specs/Architecture.md, resources/specs/Budget.md, resources/specs/Guardrails.md, resources/specs/Project Idea.md (+3 more)

### Community 8 - "Filing HTML and XBRL Markup"
Cohesion: 0.28
Nodes (9): dei:EntityPublicFloat Fact, Inline Style and Entity Noise in Filing HTML, Inline XBRL (ix:nonFraction) Tagging, Apple 10-K Paragraph HTML Sample, Colspan Spacer-Cell Table Layout, Interest Rate Sensitivity Disclosure, SEC 10-K Filing Source Format, Apple 10-K Interest Rate Sensitivity Table HTML Sample (+1 more)

### Community 9 - "Interest Rate Sensitivity Table"
Cohesion: 0.38
Nodes (7): Apple 10-K Interest Rate Sensitivity Table Sample, Hypothetical 100 Basis Point Rate Increase, All Tenors, Interest Rate Sensitivity Disclosure, Investment Portfolio (Decline in Fair Value), SEC 10-K Tabular Financial Data, Table Retrieval Challenge for RAG Pipelines, Term Debt (Increase in Annual Interest Expense)

### Community 10 - "Spec Document Set"
Cohesion: 1.00
Nodes (5): Architecture.md — Technical Architecture v2, Budget.md — Cost & Resource Plan, Guardrails.md — Architectural Constraints, Phase Plan — COMP702 RAG Benchmark Build, Project Idea — Research Concept & Benchmarking Framework

## Ambiguous Edges - Review These
- `Context-Mass Standardisation Open Item` → `Academic Rigor & Methodological Principles`  [AMBIGUOUS]
  resources/specs/Architecture.md · relation: references

## Knowledge Gaps
- **35 isolated node(s):** `src/ Project Code Folder`, `resources/specs/Project Idea.md`, `Generator Role (openai/gpt-oss-120b)`, `Critic Role (Qwen3-32b with search)`, `LOCAL_TEST_THROTTLE Loop Safety Flag` (+30 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `Context-Mass Standardisation Open Item` and `Academic Rigor & Methodological Principles`?**
  _Edge tagged AMBIGUOUS (relation: references) - confidence is low._
- **Why does `Five-Table SQLite Schema (DDL)` connect `Schema, Quota and Judge Gating` to `Spec Document Set`, `Pipeline Build Phases and Metrics`, `Benchmark Execution and Citation Audit`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `CLAUDE.md Agent Instructions` connect `Agent Steering and Document Style` to `Zero-Cost Storage and Specs Index`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `results table (960 rows, PQ + JEQ)` connect `Benchmark Execution and Citation Audit` to `Schema, Quota and Judge Gating`, `Pipeline Build Phases and Metrics`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Are the 2 inferred relationships involving `Required Proposal Structure (title page through references)` (e.g. with `Design and Specification Proposal v1.0.0 (COMP702)` and `Template Section Skeleton (13 numbered sections)`) actually correct?**
  _`Required Proposal Structure (title page through references)` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `src/ Project Code Folder`, `resources/specs/Project Idea.md`, `Generator Role (openai/gpt-oss-120b)` to the rest of the system?**
  _35 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Schema, Quota and Judge Gating` be split into smaller, more focused modules?**
  _Cohesion score 0.07311827956989247 - nodes in this community are weakly interconnected._