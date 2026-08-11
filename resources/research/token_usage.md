# Token Usage Log

Objective LLM token cost record, per operation. "Token usage" means Groq/
NVIDIA NIM LLM API tokens specifically -- not LlamaParse parsing credits,
not local compute.

## Phase 2 — Ingestion & Parsing (13 filings)

Input Token Cost: 0
Output Token Cost: 0
Reason: No LLM call occurs anywhere in this operation. Filing retrieval and parsing use SEC EDGAR's public APIs and LlamaParse, neither of which is an LLM; node splitting is local text processing with no model call involved.

## Phase 3 — Summary Tree Build, Per Filing (average)

Input Token Cost: 134K
Output Token Cost: 49K
Reason: Input tokens are set by a single 10-K filing's own node content sent as prompt text. Output tokens are set by the model's generated summary length for that content, which varies by model.

## Phase 3 — Summary Tree Build, Full Corpus (13 filings, one full run)

Input Token Cost: 1.73M
Output Token Cost: 0.97M
Reason: Input tokens scale linearly and predictably with the number and size of source filings. Output tokens do not have a single fixed value across models -- they depend on which model generates the summaries, so a range rather than a point estimate is given. Both figures are scaled down from the prior 18-filing estimate (2.4M in / 1.34M out) by 13/18, per the corpus reduction in `deviations.md` entry 20 -- the per-filing average above (134K in / 49K out) is unchanged, since dropping filings doesn't change the cost of summarizing the ones that remain.
