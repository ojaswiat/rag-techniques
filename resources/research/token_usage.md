# Token Usage Log

Objective LLM token cost record, per operation. "Token usage" means Groq/
NVIDIA NIM LLM API tokens specifically -- not LlamaParse parsing credits,
not local compute.

## Phase 2 — Ingestion & Parsing (13 filings)

Input Token Cost: 0
Output Token Cost: 0
Reason: No LLM call occurs anywhere in this operation. Filing retrieval and parsing use SEC EDGAR's public APIs and LlamaParse, neither of which is an LLM; node splitting is local text processing with no model call involved.

## Phase 3 — Summary Tree Build, Per Filing (average)

Input Token Cost: 146K (measured)
Output Token Cost: 81K (measured)
Wall Clock: ~36 min per filing
Reason: Superseded the earlier 134K in / 49K out *estimate* with measured values from `project/logs/index_build_costs.json` (2026-08-19). The average is taken over the 11 filings that logged real token counts, using one full build per filing and discarding repeat builds. Input tokens are set by a single 10-K filing's own node content sent as prompt text, and the measured input average lands close to the original estimate (146K vs 134K), confirming that input scales predictably with filing size. Output tokens ran about 1.65x the estimate (81K vs 49K), because the summariser model changed twice after the estimate was written (`deviations.md` entries 15 and 7 moved P3 from `llama-3.1-8b-instant` to `openai/gpt-oss-20b` and then to `nvidia/nemotron-3-super-120b-a12b`), and the larger models write longer summaries for the same input. Wall clock is not CPU-bound: it is set by the 40 RPM throttle enforced in `nim_client.py`, so a filing takes roughly the same time regardless of local hardware.

## Phase 3 — Summary Tree Build, Full Corpus (13 filings, one full run)

Input Token Cost: 1.89M (measured basis)
Output Token Cost: 1.05M (measured basis)
Wall Clock: ~7.7 hours
Reason: The measured per-filing average above, multiplied by 13. This is the cost of building the corpus once, with repeat builds excluded, and it is the figure to quote for "what does the P3 index cost". Two filings (JPM_2023, JPM_2024) recorded 0 input and 0 output tokens despite 2.1 and 1.9 hours of wall clock respectively -- this is the zero-cost logging defect in `bugs.md` entry 10, which was fixed after those builds ran, so their real token spend was never captured. Their contribution is therefore imputed from the 11-filing average rather than read from the log. The earlier estimate of 1.73M in / 0.97M out proved accurate on input and low on output, for the model-change reason given above.

## Phase 3 — Summary Tree Build, Actual Logged Spend (all runs to date)

Input Token Cost: 1,783,711 (measured, exact)
Output Token Cost: 958,129 (measured, exact)
Wall Clock: 15.5 hours
Reason: The exact sum of all 24 successful build runs recorded in `index_build_costs.json`, as distinct from the one-pass cost above. It is higher in wall clock and lower in tokens than the one-pass figure for two different reasons. Higher wall clock: AAPL_2023, AAPL_2024 and AAPL_2025 were built more than once, and every filing has additional resumed runs that re-walked already-persisted work and logged 0 tokens while still consuming time. Lower tokens: the two JPM builds contributed 0 to this sum because of the logging defect noted above. This is the honest "what was actually spent" number, and the gap between it and the one-pass estimate is the cost of resumability and rebuilds, which is a real cost of the $0 free-tier constraint rather than an accounting error.

## Phase 3 — Summary Tree Build, 18-Filing Projection (not built)

Input Token Cost: ~2.62M (projected)
Output Token Cost: ~1.46M (projected)
Wall Clock: ~10.7 hours
Reason: The measured per-filing average (146K in / 81K out / 36 min) multiplied by 18, giving what the originally-scoped corpus would have cost had it not been trimmed to 13 (`deviations.md` entry 20). Recorded here so the scope cut can be quantified rather than asserted: dropping five filings saved roughly 0.73M input tokens, 0.41M output tokens and 3 hours of throttled wall clock, and bought no additional research signal, since the benchmark's statistical unit is the query and not the filing. This supersedes the earlier 2.4M in / 1.34M out projection, which was written before any build had run and used the low output estimate.
