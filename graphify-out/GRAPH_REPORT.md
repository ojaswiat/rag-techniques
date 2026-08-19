# Graph Report - rag-techniques  (2026-08-19)

## Corpus Check
- 226 files · ~2,932,444 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1665 nodes · 2023 edges · 253 communities (98 shown, 155 thin omitted)
- Extraction: 87% EXTRACTED · 13% INFERRED · 0% AMBIGUOUS · INFERRED: 255 edges (avg confidence: 0.78)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `209127dc`
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
- test_config.py
- Guardrails.md
- profile.py
- logger.py
- RAG Techniques — COMP702 M.Sc. Dissertation
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
- LLMFactory
- test_groq_client_backoff.py
- search_filing_nodes
- Benchmark design
- config.py
- test_node_builder.py
- Working in this repo
- JPM_2025.md
- 4. Implementation Guardrails (Binding)
- Quickstart
- fetch_filings.py
- Guardrails are binding, not advisory
- JPM_2023.md
- JPM_2023.md
- Monitor Skill
- quickstart.md
- MSFT_2023.md
- dependencies
- Note 7 – Interest income and interest expense
- __init__.py
- prompt.md
- MSFT_2023.md
- MSFT_2025.md
- MSFT_2025.md
- TSLA_2024.md
- TSLA_2024.md
- TSLA_2023.md
- JNJ_2024.md
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
- Phase 3 — P3 Summary-Index Build: Design
- Note 7 – Interest income and interest expense
- Deferred Items Log
- Monitor Skill
- Phase 2 — Human Action Report
- Challenges Encountered
- Research Issues Log
- _round_robin_interleave
- opencode.json
- opencode.json
- dependencies
- conftest.py
- groq_limits.md
- backup_data.sh
- reload_backup.sh
- snippets.md
- directory-structure.md
- Path
- Decimal
- Decimal
- AsyncOpenAI
- Namespace
- OpenAILike
- Namespace

## God Nodes (most connected - your core abstractions)
1. `Deviations from Original Proposed Idea` - 28 edges
2. `Ingestion Corpus Sample Reference` - 22 edges
3. `exact_match()` - 19 edges
4. `10-Min Project Video — Shooting Checklist` - 18 edges
5. `normalize_numeric()` - 17 edges
6. `P3StructuralRetriever` - 15 edges
7. `StubRetriever` - 15 edges
8. `StubAnswerer` - 15 edges
9. `AGENTS.md — OpenCode Agent Instructions for rag-techniques` - 15 edges
10. `Bugs Found During Development` - 14 edges

## Surprising Connections (you probably didn't know these)
- `_attempt_fill()` --calls--> `critique_query()`  [INFERRED]
  project/dataset_generation/run_dataset_generation.py → project/dataset_generation/async_critic.py
- `_attempt_fill()` --calls--> `generate_query()`  [INFERRED]
  project/dataset_generation/run_dataset_generation.py → project/dataset_generation/async_generator.py
- `test_citations_overlap_false_on_disjoint_sets()` --calls--> `citations_overlap()`  [INFERRED]
  project/tests/test_cross_check.py → project/dataset_generation/cross_check.py
- `test_citations_overlap_true_on_any_shared_node()` --calls--> `citations_overlap()`  [INFERRED]
  project/tests/test_cross_check.py → project/dataset_generation/cross_check.py
- `test_values_match_exact_after_normalization()` --calls--> `values_match()`  [INFERRED]
  project/tests/test_cross_check.py → project/dataset_generation/cross_check.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Three retrieval paradigms share one answerer and one judge** — resources_artifacts_proposal_v1_0_0_p1_vector_pipeline, resources_artifacts_proposal_v1_0_0_p2_bm25_pipeline, resources_artifacts_proposal_v1_0_0_p3_structural_pipeline, resources_artifacts_proposal_v1_0_0_shared_answerer, resources_artifacts_proposal_v1_0_0_llm_judge [EXTRACTED 1.00]
- **Zero-spend quota safety pattern (throttle, WAL resume, disjoint sets, Groq free tier)** — resources_artifacts_proposal_v1_0_0_groq_free_tier, resources_artifacts_proposal_v1_0_0_local_throttle, resources_artifacts_proposal_v1_0_0_sqlite_wal_store, resources_artifacts_proposal_v1_0_0_risk_management_plan [INFERRED 0.85]
- **Guidelines and template constrain the submitted proposal** — resources_docs_proposalguidelines_required_structure, resources_docs_proposaltemplate_section_skeleton, resources_artifacts_proposal_v1_0_0_document, resources_artifacts_projectproposal_document [INFERRED 0.85]

## Communities (253 total, 155 thin omitted)

### Community 2 - "Proposal Compliance and Benchmark Design"
Cohesion: 0.05
Nodes (49): ProjectProposal (earlier draft of the COMP702 proposal), Draft Development and Implementation Summary (§4), BCS Project Criteria Mapping, 140-Query Human-Anchored Benchmark, Chen et al. (2021) FinQA Numerical Reasoning over Financial Data, Citation Audit (detects coincidentally-correct answers), Disjoint Query Sets PQ/GQ/JEQ (100/20/20), Design and Specification Proposal v1.0.0 (COMP702) (+41 more)

### Community 4 - "Research Question and Literature Base"
Cohesion: 0.18
Nodes (13): Encoding, chunk_section(), _get_encoding(), _log_oversized_node_skipped(), Mirrors _log_attempt_outcome's structured-logging style     (module logger, one, Splits a group_sections() section into one or more Generator-sized     chunks, e, `n` single-token words: tiktoken's cl100k_base encoding tokenizes     the bare w, Naive greedy packing would close the chunk right before n2 (the     6-token text (+5 more)

### Community 5 - "Guardrails and Model Routing"
Cohesion: 0.50
Nodes (7): _download_bytes(), fetch_filing(), _find_10k(), _get_json(), _headers(), Downloads SEC 10-K filings, resolving real URLs from SEC EDGAR's public JSON API, resolve_cik()

### Community 8 - "Filing HTML and XBRL Markup"
Cohesion: 0.28
Nodes (9): dei:EntityPublicFloat Fact, Inline Style and Entity Noise in Filing HTML, Inline XBRL (ix:nonFraction) Tagging, Apple 10-K Paragraph HTML Sample, Colspan Spacer-Cell Table Layout, Interest Rate Sensitivity Disclosure, SEC 10-K Filing Source Format, Apple 10-K Interest Rate Sensitivity Table HTML Sample (+1 more)

### Community 9 - "Interest Rate Sensitivity Table"
Cohesion: 0.38
Nodes (7): Apple 10-K Interest Rate Sensitivity Table Sample, Hypothetical 100 Basis Point Rate Increase, All Tenors, Interest Rate Sensitivity Disclosure, Investment Portfolio (Decline in Fair Value), SEC 10-K Tabular Financial Data, Table Retrieval Challenge for RAG Pipelines, Term Debt (Increase in Annual Interest Expense)

### Community 10 - "Spec Document Set"
Cohesion: 0.39
Nodes (6): _is_cache_fresh(), parse_filing(), Parses raw filings into clean Markdown via LlamaParse (Cost-effective tier, atom, test_parse_filing_calls_llamaparse_and_caches(), test_parse_filing_reparses_if_cache_older_than_48h(), test_parse_filing_skips_reparse_within_48h()

### Community 24 - "Guardrails.md"
Cohesion: 0.14
Nodes (12): 1. Absolute Infrastructure Ban: No Per-Hour or Scale-to-Non-Zero Infrastructure, 2. Model Routing Matrix and Local Compute (per-stage LLM assignment), 3. Anti-Leakage: What Each Model May and May Not See, 4. Judge Few-Shot Filtering and the Mandatory Validation Gate, 4a. Dynamic few-shot filtering, 4b. The judge-validation gate (hard prerequisite for the full run), 5. Concurrency and Rate-Limiting Enforcement, 6. Relational Data Management and State Persistence (+4 more)

### Community 28 - "logger.py"
Cohesion: 0.13
Nodes (14): 10. P3 build logged zero token cost despite generating real summaries (2026-08-04), 11. LLM temperature silently fell back to 0.1, not the mandated 0 (2026-08-04), 12. Empty filing-list argument was indistinguishable from "not provided" (2026-08-04), 13. No duplicate-question check let near-identical questions into the benchmark set (2026-08-04), 1. Reasoning-tuned models could return `content=None`, crashing `json.loads()` in Generator and Critic (2026-08-12), 2. Dataset-generation orchestrator only ever saw 9 of the 13 in-scope filings (2026-08-11), 3. Real Groq API failures crashed the whole dataset-generation run instead of being retried (2026-08-11), 4. LLMFactory's retry/backoff wrapper was silently never applied (2026-08-11) (+6 more)

### Community 29 - "RAG Techniques — COMP702 M.Sc. Dissertation"
Cohesion: 0.20
Nodes (13): classify_section(), _node(), If accepted counts never actually rise from the DB's point of view     (e.g. get, End-to-end content-aware routing check: a document with one text     section and, A single table node among mostly-text nodes is still enough material     for a Q, The overwhelmingly common case: a section under _MAX_SECTION_TOKENS     must pro, _section(), test_chunk_section_under_limit_returns_itself_unchanged() (+5 more)

### Community 191 - "LLMFactory"
Cohesion: 0.05
Nodes (52): CallbackManager, generate_query(), Generator: proposes a query + ground truth + citations for one filing section., LLMFactory, Any, Convenience: fetch client using config.MODEL_ROUTING for a stage., Static factory that returns LlamaIndex-compatible LLM client objects., Return a LlamaIndex LLM instance for the given provider and model.          Para (+44 more)

### Community 192 - "test_groq_client_backoff.py"
Cohesion: 0.08
Nodes (29): BaseException, call_groq(), get_groq_client(), Any, AsyncOpenAI, Groq client provider.  Returns a ready-to-use AsyncOpenAI instance configured fo, Return an AsyncOpenAI client configured for Groq with retries and concurrency li, Drop‑in replacement for the original groq_client.call_groq. (+21 more)

### Community 195 - "search_filing_nodes"
Cohesion: 0.09
Nodes (40): BaseModel, FunctionTool, _build_search_tool(), critique_query(), Critic: independently re-derives an answer using a local search tool.  Uses qwen, Wrap search_filing_nodes as a LlamaIndex tool bound to one filing.      The fili, Run the Critic's search-then-answer loop and return the parsed final     answer, Local, dependency-free keyword search the Critic uses to find evidence.  Not a r (+32 more)

### Community 196 - "Benchmark design"
Cohesion: 0.05
Nodes (40): next_target(), First still-unfilled (table, quadrant) slot, searched quadrant-major     then ta, _empty_counts(), _isolate_progress_log(), Attempt 1 is rejected via a citation mismatch (Critic cites an     unrelated nod, main() calls _configure_logging() on every entry; a process that (in     theory), Simulates process A having already committed 2 accepted queries into     (querie, document_ids=() means 'restrict to zero filings' -- a distinct intent     from d (+32 more)

### Community 197 - "config.py"
Cohesion: 0.08
Nodes (39): build_prefix(), _build_target_message(), compute_deterministic_metrics(), _format_exemplar(), Judge, judge_jeq_rows(), parse_judge_score(), LLM Judge for the validation gate (Guardrails.md §4, Architecture.md §4.5b).  Fo (+31 more)

### Community 198 - "test_node_builder.py"
Cohesion: 0.11
Nodes (33): Answerer, build_prompt(), parse_citations(), NodeWithScore, Shared Answerer: turns (query, retrieved nodes) into a cited answer.  One Answer, Node ids cited in `raw_text`, deduplicated, first-appearance order., The user-role message: retrieved sources, then the question.      Each node cont, _fake_llm_client() (+25 more)

### Community 200 - "Working in this repo"
Cohesion: 0.06
Nodes (34): Deliverables, Deliverables, Deliverables, Deliverables, Deliverables, Deliverables, Deliverables, Deliverables (+26 more)

### Community 201 - "JPM_2025.md"
Cohesion: 0.06
Nodes (33): 0. Decisions Carried Over From the Scoping Discussion, 10. Consolidated Dependency Manifest, 11. Open Items / Recommendations, 1. Design Review: Issues Found and Resolved, 2.1 Component View, 2.2 Deployment View, 2.3 Data-Flow Summary, 2. High-Level Design (HLD) (+25 more)

### Community 202 - "4. Implementation Guardrails (Binding)"
Cohesion: 0.24
Nodes (6): build_nodes(), _is_table_block(), Splits parsed Markdown into atomic TextNode-shaped dicts.  A Markdown table is o, ingest_one(), main(), Orchestrates fetch -> parse -> node_builder -> database_manager.insert_node for

### Community 203 - "Quickstart"
Cohesion: 0.15
Nodes (24): AnswerResult, _query(), loop_executor: cell construction, resume-skip, throttle, row shape.  Uses a stub, P2 drives its DB read with asyncio.run() inside sync retrieve(), which     raise, Default the suite to unthrottled; the throttle tests opt back in., golden_queries is the Judge's exemplar set and must stay unreachable     from an, _seed(), StubAnswerer (+16 more)

### Community 204 - "fetch_filings.py"
Cohesion: 0.07
Nodes (29): 10. Academic Rigor and Methodological Principles, 1. Research Overview and Core Objectives, 2. Data Strategy and Ingestion Parsing Architecture, 3. The 140-Query Benchmark Dataset: Three Disjoint Sets, 4. Open-Model Generation and Adversarial Verification Architecture, 5. The Human Anchor: Two Roles, Two Sets, 6. Multi-Pipeline Architectural Registry, 7. Tri-Pillar Evaluation, the Judge-Validation Gate, and the Full Benchmark (+21 more)

### Community 205 - "Guardrails are binding, not advisory"
Cohesion: 0.08
Nodes (26): Connection, _dumps(), get_all_query_texts(), get_golden_queries(), get_golden_queries_by_quadrant(), get_jeq_judging_rows(), get_queries(), get_results() (+18 more)

### Community 206 - "JPM_2023.md"
Cohesion: 0.13
Nodes (23): _accept_query(), append_failure_log(), _attempt_fill(), _configure_logging(), format_underfill_summary(), _get_all_filings(), __getattr__(), _load_all_filings() (+15 more)

### Community 207 - "JPM_2023.md"
Cohesion: 0.06
Nodes (53): citation_audit(), _contains_subsequence(), exact_match(), precision_at_k(), Deterministic scoring metrics for a single results row (Architecture.md §4.1)., Relative comparison so notation-equal figures match within epsilon.      The gap, True when `needle` appears as a contiguous run of tokens in `haystack`., Whether the ground-truth answer can be found inside the model output.      Retur (+45 more)

### Community 208 - "Monitor Skill"
Cohesion: 0.09
Nodes (22): AAPL_2023_n0019 (text), AAPL_2023_n0073 (text), AAPL_2023_n0417 (text), AAPL_2023_n0568 (text), AAPL_2023_n0611 (table), AAPL_2024_n0108 (text), AAPL_2024_n0165 (text), AAPL_2024_n0197 (text) (+14 more)

### Community 211 - "quickstart.md"
Cohesion: 0.10
Nodes (19): author, bugs, url, dependencies, claude-mem, description, directories, doc (+11 more)

### Community 212 - "MSFT_2023.md"
Cohesion: 0.09
Nodes (27): build_index_for_document(), index_path(), is_document_indexed(), main(), Path, Builds the per-document P2 BM25 index (Phase 5) -- one pickled BM25Okapi corpus, NodeWithScore, Custom BM25 tokenizer (Project Idea.md §6): preserves numbers, decimals, percent (+19 more)

### Community 213 - "dependencies"
Cohesion: 0.11
Nodes (18): 10-Min Project Video — Shooting Checklist, 10. Timeline — done, now, blockers, slowest operations (6:25 – 7:05, 40s), 11. Expected results and when (7:05 – 7:30, 25s), 12. Next steps, future scope, close (7:30 – 7:50, 20s), 13. FAQ (7:50 – 9:20, 90s) — pick 3 or 4 while filming, ~25s each, 1. Research question and why 10-Ks are hard (0:00 – 0:30, 30s), 2. System overview and end-to-end data flow (0:30 – 1:10, 40s), 3. Corpus and ingestion (1:10 – 1:40, 30s) (+10 more)

### Community 214 - "Note 7 – Interest income and interest expense"
Cohesion: 0.11
Nodes (17): AGENTS.md — OpenCode Agent Instructions for rag-techniques, Binding Constraints (from `resources/specs/Guardrails.md`), Critical Architecture Facts, Critical Execution & Problem-Solving Rules, Development Commands, Document/Styling Rules (for deliverables), Environment, Execution Restrictions (+9 more)

### Community 215 - "__init__.py"
Cohesion: 0.11
Nodes (16): 1. Cost Model at a Glance, 2. Groq Free Tier — The LLM Workload, 3. LlamaParse — The Ingestion Workload, 4. Local Compute — $0, but Not Free of Constraints, 5. What Changed From the Original Budget, 6. Single Hard Rule, COMP702 Dissertation — Cost & Resource Plan, Cost-control rules (+8 more)

### Community 216 - "prompt.md"
Cohesion: 0.15
Nodes (20): normalize_numeric(), Reduce a financial figure written as free text to a single Decimal.  Architectur, Return (numeric core, power-of-ten exponent) after peeling one suffix.      Word, _split_multiplier(), normalize_numeric: currency/separator stripping and suffix expansion.  The point, The §4.3 equivalence: the two spellings collapse to one value., test_case_insensitive_suffix(), test_dollar_billions_equals_word_millions() (+12 more)

### Community 217 - "MSFT_2023.md"
Cohesion: 0.19
Nodes (12): _jv(), score_gate_outputs: human scoring and the Agreement-Rate gate.  Two jobs (Archit, _rows(), _seed_row(), test_agreement_rate_all_agree_passes(), test_agreement_rate_eighty_percent_fails_strict_gate(), test_agreement_rate_just_above_threshold_passes(), test_compute_agreement_rate_requires_both_scores() (+4 more)

### Community 218 - "MSFT_2025.md"
Cohesion: 0.18
Nodes (14): main(), Writes golden_queries_to_label.md so the researcher can hand-write the 'why this, render_label_markdown(), main(), parse_label_markdown(), Reads the filled-in golden_queries_to_label.md back into golden_queries., An entry from an older-format golden_queries_to_label.md (exported     before th, test_parse_label_markdown_handles_entry_missing_good_example_line() (+6 more)

### Community 219 - "MSFT_2025.md"
Cohesion: 0.12
Nodes (8): A document_id with zero ingested nodes must fail loudly, not silently     build/, The CallbackManager (holding the TokenCountingHandler)     built in build_index_, A crash between persist() and the atomic rename must never leave a     false-pos, A leftover temp dir from a prior crashed build must not break the next attempt., test_build_index_for_document_cleans_stale_temp_dir_before_retry(), test_build_index_for_document_crash_leaves_only_temp_dir(), test_build_index_for_document_raises_on_no_nodes(), test_build_index_for_document_shares_callback_manager_with_llm_and_tree()

### Community 220 - "TSLA_2024.md"
Cohesion: 0.12
Nodes (16): 1.1 Primary Blue, 1.2 Neutral (blue-gray), 1.3 Gold accent — reserved, 1.4 Auxiliary evaluation colors, 1. Core scales, 2.1 Categorical (5+ series), 2.2 Sequential (ordinal data, heatmaps), 2.3 Diverging (delta / baseline-relative data) (+8 more)

### Community 221 - "TSLA_2024.md"
Cohesion: 0.12
Nodes (15): 1. Project Overview, 2. The `resources/` Folder — User Files and Steering Layer, 3. Styling and Document Rules, CLAUDE.md — Agent Instructions, Diagramming & Testing Guidelines, Draw.io Diagrams, graphify, monitor — operations log + reports (+7 more)

### Community 223 - "TSLA_2023.md"
Cohesion: 0.17
Nodes (14): compute_agreement_rate(), prompt_human_scores(), Human scoring and the Judge validation gate (Architecture.md §4.5b).  The final, Prompt for any missing human scores, then compute and report the gate., True when the two 1-10 scores agree within the tolerance band on 0-100., Agreement Rate and gate verdict over rows carrying both scores.      Every row m, What the researcher sees before scoring one row -- no judge_score., Read a 1-10 integer, re-prompting until the input is valid. (+6 more)

### Community 224 - "JNJ_2024.md"
Cohesion: 0.13
Nodes (14): 1. The Idea, 2.1 Data — CORRECTED THIS SESSION, 2.2 Code — what actually exists right now, 2.3 Tests — VERIFIED LIVE THIS SESSION, 2.4 API usage, models, providers, 2.5 Dataset generation progress — NOT empty, NOT finished, 2.6 Rate limits (live-verified figures, per spec docs), 2.7 Bugs found and fixed (13 logged in `bugs.md`, all resolved except one open item) (+6 more)

### Community 225 - "JNJ_2024.md"
Cohesion: 0.28
Nodes (12): _golden(), _jeq(), Phase 6 read/update helpers on database_manager.  These are additive: `upsert_re, _result_row(), test_get_golden_queries_by_quadrant_filters(), test_get_jeq_judging_rows_excludes_pq(), test_get_jeq_judging_rows_joins_ground_truth(), test_update_result_human_score() (+4 more)

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
Nodes (7): group_sections(), Groups Phase 2 nodes into per-section chunks for the Phase 4 Generator.  A "sect, _node(), test_excludes_null_and_empty_headers(), test_groups_nodes_by_document_and_header(), test_keeps_documents_separate(), test_normalizes_header_case_into_one_section()

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
Cohesion: 0.05
Nodes (43): ABC, MockLLM, build_cells(), build_retrievers(), main(), _parse_args(), Namespace, Benchmark cell orchestrator (Architecture.md §4.5a).  One "cell" is a single (so (+35 more)

### Community 245 - "Deviations from Original Proposed Idea"
Cohesion: 0.07
Nodes (28): 10. P3 index build bypasses the shared Groq client wrapper (2026-07-22), 11. LlamaParse table-header extraction defect (2026-07-26), 12. Dataset-generation retry and grading were too rigid (2026-07-28), 13. Embedding library unavailable on this platform (2026-07-28), 14. No token-size guard on Generator prompts (2026-07-29), 15. P3 summariser model judged too weak (2026-07-29), 16. GQ hand-labelling scale had no validation (2026-07-29), 17. Query ID format was long and quadrant-label-ambiguous (2026-07-29) (+20 more)

### Community 246 - "FastEmbedReranker"
Cohesion: 0.10
Nodes (19): BaseNodePostprocessor, FastEmbedReranker, NodeWithScore, Cross-encoder reranker for P1, backed by fastembed's ONNX TextCrossEncoder.  No, P1VectorRetriever, NodeWithScore, Path, P1: semantic vector retrieval (Architecture.md §6 Phase 5).  Filters to the quer (+11 more)

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
Cohesion: 0.29
Nodes (6): Benchmark Design, RAG Techniques — COMP702 M.Sc. Dissertation, Repository Layout, Research Question, Status, The Three Pipelines

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

### Community 278 - "_round_robin_interleave"
Cohesion: 0.20
Nodes (10): build_pools(), _company_of(), First underscore-delimited token of a document_id (e.g. 'AAPL_2023' ->     'AAPL, Flattens per-company section lists into one list by taking one     section from, Builds the two content pools upfront, across ALL filings.      `documents` is a, _round_robin_interleave(), Two companies, each with one text section and one table section.     Pools must, test_build_pools_routes_by_content_type_and_interleaves_companies() (+2 more)

## Knowledge Gaps
- **533 isolated node(s):** `@playwright/mcp`, `@drawio/mcp`, `$schema`, `plugin`, `@opencode-ai/plugin` (+528 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **155 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `compute_deterministic_metrics()` connect `config.py` to `JPM_2023.md`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **Why does `build_retrievers()` connect `P1VectorRetriever` to `FastEmbedReranker`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Why does `exact_match()` connect `JPM_2023.md` to `prompt.md`, `config.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Are the 14 inferred relationships involving `exact_match()` (e.g. with `compute_deterministic_metrics()` and `normalize_numeric()`) actually correct?**
  _`exact_match()` has 14 INFERRED edges - model-reasoned connections that need verification._
- **Are the 15 inferred relationships involving `normalize_numeric()` (e.g. with `exact_match()` and `test_case_insensitive_suffix()`) actually correct?**
  _`normalize_numeric()` has 15 INFERRED edges - model-reasoned connections that need verification._
- **What connects `@playwright/mcp`, `@drawio/mcp`, `$schema` to the rest of the system?**
  _759 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Proposal Compliance and Benchmark Design` be split into smaller, more focused modules?**
  _Cohesion score 0.04931972789115646 - nodes in this community are weakly interconnected._