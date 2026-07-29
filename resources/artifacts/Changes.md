# Changes

Simple running list of changes made to the project after the proposal was submitted.

- 2026-07-21: Swapped Critic/Judge model from `Qwen3-32b` to `qwen/qwen3.6-27b`.
  Reason: Groq's free tier no longer hosts `qwen/qwen3-32b` (confirmed via live
  `models.list()` call and a 404 on all Critic/Judge routes). `qwen/qwen3.6-27b`
  is the closest available Qwen model on the account. Updated everywhere:
  `project/config.py`, `CLAUDE.md`, `resources/specs/Guardrails.md`,
  `resources/specs/Architecture.md`, `resources/specs/Budget.md`,
  `resources/specs/Project Idea.md`, `resources/specs/Phase Plan.md`,
  `openwiki/benchmark-design.md`, `openwiki/system-architecture.md`,
  `temp/directory-structure.md`. Role-separation invariants unaffected
  (Critic/Judge still a different model family from Generator/Answerer).
- 2026-07-22: Phase 3's index build calls `llama_index.llms.groq.Groq`
  directly instead of routing through `groq_client.call_groq()`. Reason:
  Phase 5's P3 pipeline needs `TreeIndex.as_retriever()`, which only exists
  on a real LlamaIndex index object -- a custom-built tree would force a
  second, larger deviation in Phase 5. Risk: LlamaIndex's own Groq client
  has no tuned 429 backoff/semaphore, and one filing's build fires dozens of
  summarization calls in a burst (TPM/RPM risk, not just daily volume).
  Could cost real time/money if unmitigated: a corrupted cache forcing a
  manual re-run, or repeated rate-limit failures pushing an earlier-than-
  planned move to Groq's paid Developer tier. Mitigated: builds run
  sequentially (never concurrent across filings), persisted via
  temp-dir-then-atomic-rename (a crash never leaves a false-positive cache
  hit), and token/wall-clock cost is logged per filing via
  `TokenCountingHandler`. Scoped to this one build step only -- Phase 4/6/7
  Groq calls remain on `call_groq()` unconditionally. Full reasoning in
  `docs/superpowers/specs/2026-07-22-phase3-summary-index-design.md`.
- 2026-07-26: Data integrity audit of the full 9-filing corpus (post P3 build)
  found a LlamaParse extraction defect: 31 tables across 5 of 9 filings
  (`MSFT_2023/2024/2025`, `TSLA_2023`, `TSLA_2025`) have a misaligned header
  row where a units caption (e.g. `(in millions)`) merges into the table's
  first cell instead of sitting on its own line, shifting the header/
  separator rows down by one. `AAPL_2023/2024/2025` and `TSLA_2024` are
  clean. Underlying figures are intact -- only header/column labeling is
  affected, not the data itself. Storage-file validity (45/45), TreeIndex
  tree-structure consistency (9/9), and DB sanity (8,543 nodes, 0 empty/
  duplicate rows) all passed clean. Root cause is upstream in LlamaParse's
  handling of caption-prefixed tables, not this project's own parsing or
  chunking code. No fix applied -- read-only audit, documented for the
  dissertation's data-quality/limitations discussion. Full report:
  `monitor/reports/2026-07-26-data-integrity-audit-full-corpus.html`.
- 2026-07-28: Two fixes to Phase 4's dataset-generation cross-check, per
  discussion recorded in the final whole-branch review's Doubts #3/#4.
  (1) **Generator retry no longer identical.** All LLM calls run at
  `temperature=0` (deterministic) per spec, so retrying a rejected candidate
  query with the exact same input was guaranteed to reproduce the exact same
  rejected output -- wasted attempts and Groq quota for no chance of success.
  Fixed by feeding the retry what specifically failed (citation mismatch vs.
  value mismatch, and what the Critic found instead) and nudging toward a
  different node/angle within the same section, so each retry is a genuine
  second attempt.
  (2) **Cross-check numeric matching was too strict.** `values_match()`
  required the Generator's and Critic's answers to contain the exact same
  *count* of numbers, so a correct answer like "$100 million" failed against
  an equally correct "$100 million in 2025" purely because of an unrelated
  extra number (the year). Fixed by requiring only that every number in the
  Generator's answer appear (within tolerance) in the Critic's answer --
  extra numbers are permitted, not penalised. Considered and rejected an
  LLM-based semantic-similarity check as an alternative/addition (a third
  Groq call per attempt, ~50% more spend/latency, reintroduces
  non-determinism, and duplicates the Critic's own independent re-derivation
  -- the exact reasoning the spec already used to keep the Citation Audit
  code-only rather than Judge-graded). Instead added a third, complementary,
  still-deterministic gate: `bge-small-en-v1.5` embedding cosine similarity
  between the two answer texts (same model already used for P1/P3
  retrieval, local, free, no Groq call) above a threshold, to catch a
  Critic answer whose numbers happen to match by coincidence but whose
  surrounding text is otherwise unrelated. Numeric-subset matching was kept
  alongside embedding similarity (not replaced by it) because embeddings
  are unreliable at penalising a single wrong figure in an otherwise
  similarly-worded sentence (e.g. "$100 million" vs. "$150 million" score
  as highly similar) -- the three gates (citation overlap, numeric subset,
  embedding similarity) each catch a distinct failure mode none of the
  others cover.
- 2026-07-28: Embedding library substitution for the Doubt #4 cross-check
  fix above. `Architecture.md`'s Phase 5 package list names
  `sentence-transformers`/`FlagEmbedding` as the project's embedding path
  for `bge-small-en-v1.5`. Neither could be installed on this development
  machine: `torch` (a hard dependency of both) publishes no wheel for
  macOS x86_64 + Python 3.13 at any version -- confirmed live via
  `uv pip install torch --dry-run`, which fails on this exact venv
  (verified independently during code review, not just claimed by the
  implementer). Used `fastembed` (Qdrant's ONNX Runtime-based embedding
  library) instead, pinned with `onnxruntime==1.23.2`, loading the
  identical `BAAI/bge-small-en-v1.5` model weights -- same model, different
  loading library, verified via live reproduction of similarity scores
  during review. Lighter install footprint than `torch`+`sentence-transformers`
  would have been (~25MB of wheels vs. torch's much larger footprint).
  This only affects Phase 4's cross-check embedding use; Phase 5's actual
  P1 vector-store embedding path (not yet built) should re-evaluate this
  same platform constraint when it's implemented, since `Architecture.md`
  still names `sentence-transformers` there too.
- 2026-07-29: Added `tiktoken` as a new Phase 4 dependency, not listed in
  `Architecture.md`'s Phase 4 package line ("`groq`, `rank_bm25`
  (already introduced)"). Reason: fixed a real correctness gap (Doubt #8) --
  the Generator receives an entire filing section's concatenated content in
  one prompt, and a few real sections run large. The DB's existing
  `nodes.token_count` column is a plain whitespace word count
  (`len(stripped.split())` in `ingest/node_builder.py`), not a real
  tokenizer count, so it can't be trusted to guard against exceeding the
  Generator model's request limit. `tiktoken` gives an accurate local count
  (no Groq call) to check section size before sending, and to drive
  `chunk_section()`'s node-boundary splitting when a section exceeds
  `_MAX_SECTION_TOKENS` (60,000, chosen with headroom under `gpt-oss-120b`'s
  128K window). Live-verified the corpus's actual largest section is
  ~29,478 tokens -- comfortably under both the model's real limit and the
  new threshold, so this fix is precautionary today, not an active
  blocker, but a real gap worth closing since corpus size may grow.
  Pinned as a floor (`tiktoken>=0.12.0`), matching the project's dominant
  dependency-pinning style. Operational note: `cl100k_base`'s encoding
  table downloads over the network on first use (cached locally after) --
  not an issue in this environment, but would need pre-warming or a
  documented fallback in a fully offline/CI run.
