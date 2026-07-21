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

- 2026-07-21: `ingest/parse_filing.py`'s `LlamaParse(...)` call used the
  `parsing_instruction` parameter (as drafted in the Phase 2 plan), which
  triggers a deprecation warning in the installed `llama-parse==0.6.94`.
  First swapped to `system_prompt`, then corrected to `system_prompt_append`
  after task review caught that `system_prompt` fully replaces LlamaParse's
  tuned default prompt (the library's own docs warn this "may impact
  accuracy"), while `system_prompt_append` preserves the default and adds
  to it — the correct replacement for what was previously an additive
  instruction. Re-verified with the mocked unit tests and a live LlamaParse
  smoke test using real tabular content (a 2-row financial table); the
  table came back intact with no truncation or column loss.

  Bigger, unresolved finding surfaced during that live smoke test: the
  entire `llama-parse` PyPI package is itself deprecated in favour of a new
  unified SDK (`llama-cloud`, currently v2.11.0). Its own printed
  deprecation notice says it will be "maintained until May 1, 2026" —
  already past as of today (2026-07-21). The package is still installable
  and fully functional (confirmed live), so Task 3 was not blocked on this,
  but a full migration to `llama-cloud`'s API is a non-trivial rewrite
  (different client shape, not a drop-in replacement) and was judged out of
  scope for a mid-task fix. Flagged for a human decision in
  `temp/phase2-human-actions.md` rather than silently deferred or silently
  migrated.

- 2026-07-21: Amended the Phase 2 plan's Task 6 (End-to-end verification) to
  add a new **Step 3b**, inserted right after the throttled ingestion run.
  Reason: Task 4's reviewer confirmed two real risks in
  `ingest/node_builder.py` — the section-header regex and the table/text
  classifier both assume a blank line separates a header (or a table's
  first row) from surrounding content, an assumption never tested against
  real LlamaParse output. Neither risk breaks the "a table is never
  bisected" hard invariant, but both can silently corrupt
  `parent_item_header` attribution or `node_type` tagging, which Task 5's
  audit and Phase 4's dataset generation depend on. Step 3b makes Task 6
  explicitly print and eyeball a sample of real nodes for these two
  specific failure signs, rather than only checking node counts, so the
  gap the reviewer identified doesn't fall through unchecked.

- 2026-07-21: Task 6's Step 3b ran against the real AAPL_2025 filing (682
  nodes). Result: all 22 real "Item N." section headers were attributed
  correctly (no false negatives observed) -- Concern #1 did not manifest on
  this filing. Concern #2 DID manifest once: one exhibit-index table (a
  caption line "Incorporated by Reference" directly above the table rows,
  no blank line between them) was misclassified as node_type: text instead
  of table. Per the plan's own Step 3b instruction (fix it immediately if
  either failure mode shows up, since Task 5's audit and Phase 4 build on
  top of this corpus), fixed ingest/node_builder.py's _is_table_block()
  right away: it now checks for at least 2 pipe-led lines anywhere in the
  block (a real table's header + at least one data row), not just the
  block's first line. Added a regression test
  (test_build_nodes_classifies_captioned_table_as_table) reproducing the
  exact real-world shape found. Re-ran the throttled ingestion (hit the 48h
  parse cache, no LlamaParse credits re-spent) and confirmed 0 remaining
  misclassified nodes and the exhibit table now correctly tagged table.
  Also observed (not fixed, logged as cosmetic): 174 of 682 nodes have a
  raw # character leaked into content -- these are all front-matter/
  cover-page headings (e.g. "# FORM 10-K", "# Apple Inc.") that the header
  regex correctly does NOT treat as an Item-section header (they aren't
  one), but the raw markdown syntax isn't stripped from the resulting text
  node either. Does not corrupt Item-header attribution or table
  atomicity -- the two things this check specifically guards -- so left as
  a known cosmetic gap rather than an urgent fix.
