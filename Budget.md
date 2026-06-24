# Budget.md

## COMP702 Dissertation — Cost & Resource Plan

This document reconciles the project's resource requirements with a **near-zero-spend** operating model. It is the authoritative budget reference and supersedes any earlier cost framing (e.g. the previous $300 Google Cloud / Vertex AI allocation, which is **no longer part of this project**).

**Headline figure: the project is designed to run at $0.00 in expected spend.** Every recurring component sits on a free tier or runs locally on CPU. The sections below show the math, the limits that actually bind, and the worst-case fallback cost if a free tier is exceeded.

---

## 1. Cost Model at a Glance

| Component | Tool | Where it runs | Expected cost |
|---|---|---|---|
| Document parsing | LlamaParse (Cost-effective tier) | Hosted API (free tier) | $0.00 |
| Embeddings | `BAAI/bge-small-en-v1.5` | Local CPU | $0.00 |
| Re-ranker (Pipeline 3) | `BAAI/bge-reranker-base` | Local CPU | $0.00 |
| BM25 retrieval (Pipeline 4) | `rank_bm25` | Local CPU | $0.00 |
| Query generation | Llama 3.3 70B | Groq free tier | $0.00 |
| Query critique | Qwen3 32B | Groq free tier | $0.00 |
| LLM-as-a-Judge | Llama 3.3 70B | Groq free tier | $0.00 |
| State / results store | SQLite | Local disk | $0.00 |
| **Total** | | | **$0.00** |

The binding constraint across this project is **not money — it is API request rate** (Groq's per-day request caps and LlamaParse's monthly free credits). The rest of this document is about staying inside those limits.

---

## 2. Groq Free Tier — The LLM Workload

All LLM calls (generation, critique, judging) run on Groq's free tier: open-source models on Groq's LPU hardware, no credit card, rate-limited rather than billed.

### Published free-tier limits (as of mid-2026, verify before runs)

| Model | RPM | RPD | TPM | TPD |
|---|---|---|---|---|
| `llama-3.3-70b-versatile` | ~30 | ~1,000 | ~12,000 | ~100,000 |
| `llama-3.1-8b-instant` | ~30 | ~14,400 | higher | higher |
| `qwen/qwen3-32b` | ~30 | ~1,000 | per Groq docs | per Groq docs |

> Limits apply **per organization**, not per API key — creating extra keys does not raise the ceiling. Limits rotate; check `console.groq.com` before a large run. Cached tokens (a consistent system prompt) do **not** count toward limits, which stretches the free tier further.

### Total LLM call budget for the whole project

| Phase | Model | Calls (incl. ~30% regeneration/retry overhead) |
|---|---|---|
| Dataset generation | Llama 3.3 70B | ~130 |
| Dataset critique | Qwen3 32B | ~130 |
| Judge evaluation | Llama 3.3 70B | ~780 (600 runs + re-runs during rubric tuning) |
| **Total** | | **~1,040 calls** |

At a ~1,000 requests/day cap on the 70B model, the Llama-based generation + judging workload spreads across **roughly 1–2 active days** of running; the Qwen critique runs in parallel on its own model bucket. With even light batching across days, the free tier absorbs the entire project comfortably.

### Cost-control rules (in priority order)
1. **Run the throttle first.** Per `Guardrails.md`, execute the full pipeline end-to-end with `LOCAL_TEST_THROTTLE = True` (3 items only) before any full run. This catches bugs before they burn request quota.
2. **Resume, never restart.** The SQLite `results` table must be checked on startup so a crash resumes from the last written row instead of re-spending calls.
3. **Tune the Judge on the 12 golden queries only** — not the full 100 — until the Agreement Rate is stable >80%. Rubric iteration is where judge calls silently multiply.
4. **Use the 8B model for any throwaway debugging**, reserving 70B's tighter daily cap for real generation and judging.

### Worst-case paid fallback (only if free tier is blown)
If daily caps become a bottleneck and you opt into the paid tier, Llama 3.3 70B is roughly **$0.59 / 1M input tokens and $0.79 / 1M output tokens**. The entire ~1,040-call workload, even at a generous ~4K tokens/call, is on the order of ~4M tokens total — i.e. **a worst-case ceiling of a few US dollars**, not hundreds. Adding a credit card also unlocks ~10x rate limits with a 25% token discount if you simply need more daily headroom rather than more spend.

---

## 3. LlamaParse — The Ingestion Workload

LlamaParse stays as the parser (your decision), justified by its atomic-table-to-Markdown quality on financial filings. It is hosted, but the free tier covers the project.

- **Free allotment:** ~10,000 credits/month for new users.
- **Cost-effective tier:** ~3 credits/page → the free tier covers **~3,300 pages/month**.
- **Caching is free:** re-parsing the same file within 48 hours costs 0 credits — so iterating on the pipeline does not re-spend credits on already-parsed filings.

### Page budget
A typical SEC 10-K runs ~100–200 pages. Even at 200 pages/filing and 3 credits/page (600 credits), the monthly free allotment covers **~16 full filings/month** — far more than this study requires.

### Cost-control rules
1. **Parse once, cache aggressively.** Persist parsed Markdown + node metadata to SQLite immediately so a filing is never parsed twice.
2. **Stay on Cost-effective, not Agentic/Premium.** Higher tiers cost 45–90 credits/page (15–30x more) and are unnecessary for this data.
3. **Avoid the Fast tier for tables** — it does not emit Markdown, which breaks atomic-table preservation.

### Worst-case paid fallback
Overflow credits bill at **$1.25 / 1,000 credits**. Re-parsing 16 full filings beyond the free tier would cost on the order of **~$12** — and only if caching and the free allotment were both ignored.

---

## 4. Local Compute — $0, but Not Free of Constraints

Embeddings, re-ranking, and BM25 all run locally on CPU, so they cost nothing in dollars. The trade-off is **your machine's time and RAM**, not money.

- `bge-small-en-v1.5` (embeddings) and `bge-reranker-base` are small enough to run on CPU without a GPU.
- BM25 (`rank_bm25`) is pure-Python and trivially cheap.
- One-time index build over the corpus is a fixed setup cost measured in minutes, captured under Pillar 3 (Efficiency) as a research metric rather than a financial one.

If local CPU runs prove too slow during development, a free Google Colab / Kaggle notebook session is a $0 fallback for the embedding/index-build step — not required, just available.

---

## 5. What Changed From the Original Budget

| Original plan | Revised plan | Effect |
|---|---|---|
| $300 Vertex AI credit allocation | $0 — Groq free tier + local CPU | Removes the entire cloud spend exposure |
| Gemini 1.5 Pro / Flash (decommissioned) | Llama 3.3 70B + Qwen3 32B (Groq) | Restores a working, free model stack |
| Cohere Rerank (paid, unbudgeted) | `bge-reranker-base` (local, $0) | Removes an unbudgeted paid surface |
| `text-embedding-004` / `3-small` (paid API) | `bge-small-en-v1.5` (local, $0) | Removes embedding API spend |
| 4,000 generations + 4,000 judge runs | 600 + 600 | ~85% fewer paid-surface calls |
| 400-query dataset | 100-query dataset | Lower generation + verification load |

---

## 6. Single Hard Rule

> **No component in this project may bill per-hour or scale-to-non-zero.** All retrieval and indexing run locally; all LLM calls run on a free tier with request-rate limits, not spend. If any design change would introduce a persistent or per-hour cloud charge (e.g. a managed vector DB endpoint, a hosted reranker, a premium parse tier), it must be re-scoped back to a local or free-tier equivalent before implementation — consistent with the absolute infrastructure ban in `Guardrails.md`.

*Free-tier limits and per-token prices rotate frequently. Re-verify Groq and LlamaParse figures against their live pricing/limits pages before any large batch run.*
