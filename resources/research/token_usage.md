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

## Phase 7 — Pipeline Answering, Full Benchmark (900 cells)

Input Token Cost: 550,193 (measured, exact)
Output Token Cost: 48,206 (measured, exact)
Wall Clock: 6.5 s average per cell
Reason: The exact sum of `results.input_tokens` and `results.output_tokens` over the 900 PQ rows, which the pipeline answerer records per cell as it runs. Split by pipeline: P1_vector 164,498 in / 16,139 out, P2_bm25 158,621 / 16,352, P3_structural 227,074 / 15,715. All three answer the same 100 questions at the same three depths through the same Groq model, so the input spread is a direct measure of how much text each paradigm puts in front of the answerer for the same question. P3 sends 43% more input than P2 for the same k because tree nodes carry their summaries, which are longer than the raw leaf nodes P1 and P2 return; it is the most expensive to query as well as the most expensive to build, while scoring lowest. Output tokens are near-identical across the three (15.7K to 16.4K) because the answer format is fixed by the prompt, not by the retrieval paradigm. Average latency is 6.18 s (P2), 6.40 s (P1) and 6.87 s (P3) per cell, dominated by the shared Groq call rather than by local retrieval.

## Phase 6 — Judge, Validation Gate (60 outputs)

Input Token Cost: 66,941 (measured, exact)
Output Token Cost: 4,122 (measured, exact)
Reason: The sum over the 60 JEQ rows, which is the answering spend for the 20 judge-validation questions across three pipelines. These are the outputs the gate then scored. Recorded the same way as the benchmark rows above, through the answerer's own usage accounting.

## Phase 6 — Judge Scoring, Full Benchmark (900 cells)

Input Token Cost: ~1.21M (estimated, not recorded)
Output Token Cost: ~2.7K (estimated, not recorded)
Reason: This is the one operation in the project whose token spend was never captured, and the honest entry is an estimate with its basis stated rather than a measured figure. `results.input_tokens` and `results.output_tokens` are written once, by the pipeline answerer during generation; judging updates only the metric columns and the rubric fingerprint (`_UPDATABLE_SCORE_COLUMNS` in `database_manager.py` contains no token column), so the judge's own calls pass through unaccounted. The estimate reconstructs the prompts deterministically instead of guessing: each row's prompt is its quadrant's cacheable system prefix (4,219 to 6,499 characters, being the rubric plus that quadrant's five graded exemplars) plus a target message carrying the question, the ground-truth answer and the candidate answer. Summed across all 900 rows that is 4,824,234 characters, which at roughly four characters per token gives about 1.21M input tokens. Output is small and bounded by construction: the judge returns a single integer per row, so 900 rows is on the order of 2,700 tokens. The real input figure is likely lower than 1.21M in wall-clock billing terms, because the per-quadrant prefix is identical for every row of that quadrant and is written to be cacheable, so a prompt-caching provider charges those exemplar tokens once per quadrant rather than 225 times. Treat 1.21M as the uncached upper bound and the measured answering spend as the only exact figure for Phase 7.
