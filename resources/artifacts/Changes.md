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
- 2026-07-29: Swapped P3's summariser model from `llama-3.1-8b-instant` to
  `openai/gpt-oss-20b` (`config.MODEL_ROUTING["p3_index_build"]`). Reason:
  8B judged too small for reliable summary quality on dense financial
  filing sections -- a real quality concern, not a throughput one (8B was
  originally chosen purely for its high free-tier daily request ceiling,
  per `Budget.md`). Considered and rejected `Llama 3.3 70B` (would be the
  same model as the shared Answerer -- gives P3 alone an unfair "home
  advantage" reading its own writing style, a structural confound against
  P1/P2). Considered and rejected `Qwen3.6-27B` (viable but already reused
  for Critic and Judge -- more role overlap than necessary when a cleaner
  option exists). Considered switching provider entirely (Gemini,
  OpenRouter, SambaNova, Cerebras) -- rejected for now: Cerebras's "free
  tier" turned out to be a $5 trial credit, not perpetual free (corrected
  after an initial wrong claim); Gemini's per-minute request cap (~10 RPM)
  risks throttling this bursty per-filing build harder than Groq's TPD
  wall did; all three require a real client rewrite (`build_summary_index.py`
  calls `llama_index.llms.groq.Groq` directly, not a swappable wrapper) and
  a new live rate-limit verification pass, disproportionate to the problem
  being solved. `openai/gpt-oss-20b` needed no client change, no new
  Guardrails deviation beyond the model ID itself, and no role overlap.
  This requires a full 18-filing P3 rebuild (not just the 9 previously
  built on 8B) for cross-filing summarization consistency -- deleted the 9
  stale `storage/summary_index/` directories (already preserved in
  `project/backups/backup-20260729-100133/`) to force a clean rebuild.
  Also found and fixed a related gap while wiring this up:
  `data/filings_manifest.json` on this branch (`phase3-summary-index-build`)
  was still pinned to the original 9 filings; the JPM/JNJ/WMT entries only
  existed on the unmerged `corpus-expansion-3-companies` branch. Copied the
  18-filing manifest content directly rather than merging branches (per
  standing instruction not to merge/sync branches without being asked) --
  node data for all 18 filings was already present in `benchmark.db`
  regardless of git branch (it's gitignored, filesystem-level state).
