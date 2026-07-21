# Directory Structure — rag-techniques

```
rag-techniques/                       # ROOT: assignment workspace — humans + AI agents, whole COMP702 assignment
├── .gitignore
├── CLAUDE.md                         # agent instructions for this repo
├── .claude/                          # Claude Code project config, skills
├── resources/                        # steering layer — specs, deliverables, assets (read-only reference)
│   ├── specs/                        # Project Idea, Architecture, Phase Plan, Guardrails, Budget
│   ├── artifacts/                    # proposals, papers, sheets (.docx/.pdf/.xlsx/.md)
│   ├── assets/                       # design palette, typography, diagrams, data samples
│   └── docs/                         # university brief, proposal template (read-only)
├── temp/                             # scratch outputs — reports, exports; never authoritative
├── monitor/                          # ops logging / reporting plugin
├── openwiki/                         # generated documentation wiki
├── graphify-out/                     # knowledge graph (god nodes, community structure)
│
└── project/                          # THE PROJECT ITSELF — A-Z, everything a from-scratch build needs
    ├── .venv/                        # uv-managed virtual environment (project-local, gitignored)
    ├── .env                          # Groq + LlamaParse API keys (gitignored)
    ├── pyproject.toml                # pinned dependency manifest (uv)
    ├── config.py                     # shared config (model routing, K values, throttle flag)
    ├── database_manager.py           # SQLite access layer (5-table schema, WAL mode)
    ├── groq_client.py                # resilient Groq wrapper (tenacity backoff + semaphore)
    ├── groq_limits.md                # verified Groq rate limits + check date
    ├── benchmark.db                  # nodes, queries, golden_queries, judge_validation, results
    │
    ├── data/
    │   ├── filings_manifest.json     # chosen companies/years, source URLs
    │   ├── raw/                      # downloaded SEC 10-K filings
    │   └── parsed/                   # LlamaParse output (cached Markdown + node metadata)
    │
    ├── storage/
    │   ├── chroma/                   # P1 local vector index
    │   ├── bm25/                     # P2 local BM25 index
    │   └── summary_index/            # P3 cached summary tree (one-time build)
    │
    ├── logs/
    │   └── index_build_costs.json    # wall-clock + token cost per index build
    │
    ├── ingest/                       # Phase 2 — ingestion & parsing
    │   ├── fetch_filings.py          # pull filings from SEC EDGAR
    │   ├── parse_filing.py           # LlamaParse atomic-table mode
    │   ├── node_builder.py           # node_id assignment + metadata enrichment
    │   └── parsing_audit.py          # 20-section validation audit
    │
    ├── dataset_gen/                  # Phase 4 — dataset generation & verification
    │   ├── async_generator.py        # Generator (gpt-oss-120b): per-section Q&A + citations
    │   ├── search_tool.py            # search-over-all-nodes tool for the Critic
    │   ├── async_critic.py           # Critic (Qwen3.6-27B): blind independent verification
    │   ├── cross_check.py            # deterministic node-ID + value cross-check
    │   ├── split_and_label.py        # split into PQ / GQ / JEQ (disjoint)
    │   └── label_gq.py               # human-labelling helper for the 20 GQ
    │
    ├── pipelines/                    # Phase 5 — P1 / P2 / P3 implementation
    │   ├── base.py                   # shared pipeline interface
    │   ├── answerer.py               # shared answerer (Llama 3.3 70B, temp 0)
    │   ├── vector/
    │   │   └── p1_vector.py          # bge embeddings + bge reranker
    │   ├── keyword/
    │   │   ├── tokenizer.py          # custom regex tokenizer (numbers, %, currency)
    │   │   └── p2_bm25.py            # rank_bm25 retrieval
    │   └── structural/
    │       ├── build_summary_index.py  # Phase 3 — one-time P3 index build
    │       └── p3_structural.py      # summary-tree traversal retrieval
    │
    ├── loop_executor.py              # shared async worker loop (throttle + resume)
    │
    ├── judge/                        # Phase 6 — judge build & validation gate
    │   ├── async_judge.py            # Qwen3.6-27B, dynamic per-quadrant few-shot
    │   ├── metrics.py                # Precision@K, Recall@K, Evidence Hit Rate, Citation Audit
    │   ├── numeric_normalizer.py     # numeric normalisation for Exact Match
    │   ├── score_gate_outputs.py     # scores the 60 JEQ gate outputs
    │   └── validation_gate.py        # human-vs-judge agreement rate, >80% gate check
    │
    ├── run_benchmark.py              # Phase 7 — 900-run matrix orchestration
    │
    ├── analysis/                     # Phase 8 — results consolidation
    │   ├── aggregate.py              # tri-pillar aggregation, per-quadrant breakdown
    │   ├── plots.py                  # comparison charts
    │   └── tables.py                 # comparison tables
    │
    └── tests/
        ├── test_groq_client_backoff.py   # 429 retry/backoff behaviour
        ├── test_tokenizer_consistency.py # tokenizer identical at index vs query time
        └── test_no_leakage.py            # pipelines receive nothing beyond query + own nodes
```
