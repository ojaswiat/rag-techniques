# Budget.md

## COMP702 Dissertation — Cost & Resource Plan

This document reconciles the project's resource requirements with a **near-zero-spend** operating model. It is the authoritative budget reference and supersedes any earlier cost framing (e.g. the previous $300 Google Cloud / Vertex AI allocation, which is **no longer part of this project**).

**Headline figure: the project is designed to run at $0.00 in expected spend.** Every recurring component sits on a free tier or runs locally on CPU. **The binding constraint is not money — it is Groq's per-day token throughput (TPD), not request count (RPD).** The sections below show the math, the limits that actually bind, and the worst-case fallback if a free tier is exceeded.

> **What changed in this revision:** the project now benchmarks **three pipelines (P1 Vector, P2 BM25, P3 Structural)**, not two, producing **900 runs** (was 600). Two LLM workloads that the earlier budget omitted are now costed explicitly: the **pipeline answer-generation** calls (the model that turns retrieved context into the answers being judged) and the **one-time P3 summary-index build**. The earlier "$0, finishes in 1–2 days" claim was incorrect once these are included and is corrected below.

---

## 1. Cost Model at a Glance

| Component | Tool / Model | Where it runs | Expected cost |
|---|---|---|---|
| Document parsing | LlamaParse (Cost-effective tier) | Hosted API (free tier) | $0.00 |
| Embeddings | `BAAI/bge-small-en-v1.5` | Local CPU | $0.00 |
| Re-ranker (P1) | `BAAI/bge-reranker-base` | Local CPU | $0.00 |
| BM25 retrieval (P2) | `rank_bm25` | Local CPU | $0.00 |
| **P3 summary-index build (one-time)** | `llama-3.1-8b-instant` | Groq free tier | $0.00 |
| Query generation | `openai/gpt-oss-120b` | Groq free tier | $0.00 |
| Query critique | `Qwen3-32b` (+ search tool) | Groq free tier | $0.00 |
| **Pipeline answer generation (P1/P2/P3)** | `Llama 3.3 70B` | Groq free tier | $0.00 |
| LLM-as-a-Judge | `Qwen3-32b` | Groq free tier | $0.00 |
| State / results store | SQLite | Local disk | $0.00 |
| **Total** | | | **$0.00** |

The binding constraint is **Groq's token-per-day ceiling** on the heaviest workloads (answer generation and judging). The rest of this document is about staying inside that limit — primarily via prompt caching and spreading work across days.

---

## 2. Groq Free Tier — The LLM Workload

All LLM calls run on Groq's free tier: open-source models on Groq's LPU hardware, no credit card, rate-limited rather than billed.

### Published free-tier limits (verified mid-2026 — re-verify before runs)

| Model | Role | RPM | RPD | TPM | TPD |
|---|---|---|---|---|---|
| `openai/gpt-oss-120b` | Generator | ~30 | ~1,000 | ~8,000 | ~200,000 |
| `qwen/qwen3-32b` | Critic + Judge | ~60 | ~1,000 | ~6,000 | per Groq docs |
| `llama-3.3-70b-versatile` | Pipeline answerer | ~30 | ~1,000 | ~12,000 | ~100,000 |
| `llama-3.1-8b-instant` | P3 index build / debug | ~30 | ~14,400 | higher | higher |

> Limits apply **per organization**, not per API key — extra keys do not raise the ceiling. You hit whichever limit arrives first. **For the token-heavy phases the daily-token (TPD) ceiling binds before the daily-request (RPD) ceiling** — e.g. Llama 3.3 70B's ~100K TPD is reached long before its ~1,000 RPD. **Cached tokens do not count toward limits**, so a consistent system prompt / rubric prefix stretches the free tier substantially. For Qwen, the ~6K **TPM** is the tight axis. Re-verify all figures at `console.groq.com` before a large run.

### Total LLM call budget for the whole project

| Phase | Model | Calls (incl. ~30% regeneration/retry overhead) |
|---|---|---|
| P3 summary-index build (one-time) | `llama-3.1-8b-instant` | ~one per node (bulk, on the 14,400 RPD model) |
| Dataset generation | `openai/gpt-oss-120b` | ~180 |
| Dataset critique | `Qwen3-32b` | ~180 |
| Pipeline answer generation (900 + 60 validation) | `Llama 3.3 70B` | ~960 |
| Judge evaluation (900 + 60 validation) | `Qwen3-32b` | ~960 |
| **Total (excl. one-time index build)** | | **~2,280 calls** |

### The TPD reality (this corrects the old "1–2 days" claim)

The two heavy phases are token-bound, not request-bound:

* **Answer generation (`Llama 3.3 70B`, ~100K TPD).** ~960 calls, each ~1–3K tokens (query + K retrieved nodes; larger at K=10), averaging ~2K → on the order of **~2M tokens**. Against ~100K TPD that is **roughly two-to-three weeks** of free-tier days, *not* 1–2. This is the project's true bottleneck.
* **Judging (`Qwen3-32b`).** ~960 calls. With the rubric + 5 quadrant-matched few-shot exemplars **prompt-cached** (a static prefix that does not count toward limits), the uncached payload per call is small (~1K tokens), but Qwen's ~6K **TPM** still paces throughput. Spread across days, it fits comfortably.
* **Generation + critique.** ~180 calls each; minor relative to the above.

So the honest position: **at strict $0, the full 900-run benchmark spans ~2–3 weeks of intermittent free-tier running** (well inside the 10-week timeline), gated by Llama 3.3 70B's TPD. It does **not** finish in 1–2 days for free.

### Cost-control rules (in priority order)
1. **Run the throttle first.** Per `Guardrails.md §4`, run the full pipeline end-to-end with `LOCAL_TEST_THROTTLE = True` (3 items) before any full run, to catch bugs before they burn quota.
2. **Pass the judge gate before the full run.** Per `Guardrails.md`, validate the Judge on the 60 Phase-2 outputs (>80% human agreement) *before* launching the 900-run matrix — never grade 900 outputs with an unvalidated judge.
3. **Cache the static prefix.** Cache the Judge rubric + the 5 per-quadrant few-shot exemplars (four cacheable prefixes, one per quadrant). Cached tokens do not count toward limits — this is the single biggest free lever on the judging phase.
4. **Resume, never restart.** The SQLite `results` table is checked on startup so a crash resumes from the last written row instead of re-spending calls.
5. **Build the P3 summary index once.** Persist it to disk/SQLite; never rebuild. Use `llama-3.1-8b-instant` (14,400 RPD) so this bulk job does not touch the 70B's tight daily budget.
6. **Use the 8B model for throwaway debugging**, reserving the 70B and gpt-oss daily caps for real generation, answering, and judging.

### Headroom levers if the TPD bottleneck bites
* **Prompt caching (free):** as above — apply it to the Judge and to any repeated system prompt in answer generation.
* **Spread across days (free):** the resume logic makes multi-day running painless; this keeps the project at strict $0.
* **Alternate answerer (free):** if Llama 3.3 70B's ~100K TPD is too tight, `openai/gpt-oss-120b` offers ~200K TPD (double) and is still a *different family* from the Qwen judge, so the no-self-judging rule holds. Trade-off: gpt-oss then doubles as Generator and Answerer (different phases, no circularity, but less role separation).
* **Developer tier (small spend):** adding a credit card unlocks ~10x rate limits with a ~25% token discount. This is the fastest way to compress the run to a day or two — see fallback below.

### Worst-case paid fallback (only if you opt out of the free tier for speed)
The whole LLM workload is on the order of **~4M tokens** (mostly input). At Llama 3.3 70B's paid rate (~$0.59 / 1M input, ~$0.79 / 1M output), even a generous estimate lands at **a worst-case ceiling of a few US dollars (~$3–5)**, not hundreds — and gpt-oss-120b is cheaper still ($0.15 / $0.60). The Batch API (50% off) and the Developer-tier 25% discount lower this further. The strict-$0 path remains the default; paid is purely an optional time-saver inside a trivial ceiling.

---

## 3. LlamaParse — The Ingestion Workload

LlamaParse stays as the parser, justified by its atomic-table-to-Markdown quality on financial filings. It is hosted, but the free tier covers the project. **The addition of P3 does not change parsing** — all three pipelines consume the same parsed nodes; only P3 adds a downstream summary-index build (costed in §2).

- **Free allotment:** ~10,000 credits/month for new users.
- **Cost-effective tier:** ~3 credits/page → ~3,300 pages/month free.
- **Caching is free:** re-parsing the same file within 48 hours costs 0 credits.

### Page budget
A typical SEC 10-K runs ~100–200 pages. Even at 200 pages × 3 credits (600 credits), the monthly free allotment covers **~16 full filings/month** — far more than this study requires.

### Cost-control rules
1. **Parse once, cache aggressively.** Persist parsed Markdown + node metadata (with `node_id`) to SQLite immediately so a filing is never parsed twice.
2. **Stay on Cost-effective, not Agentic/Premium** (higher tiers cost 15–30× more and are unnecessary here).
3. **Avoid the Fast tier for tables** — it does not emit Markdown, breaking atomic-table preservation.

### Worst-case paid fallback
Overflow credits bill at ~$1.25 / 1,000 credits. Re-parsing ~16 full filings beyond the free tier would cost on the order of **~$12**, and only if caching and the free allotment were both ignored.

---

## 4. Local Compute — $0, but Not Free of Constraints

Embeddings, re-ranking, and BM25 run locally on CPU, so they cost nothing in dollars. The trade-off is **machine time and RAM**, not money.

- `bge-small-en-v1.5` (embeddings) and `bge-reranker-base` (P1 re-ranker) run on CPU without a GPU.
- BM25 (`rank_bm25`) is pure-Python and trivially cheap; its custom regex tokenizer (Guardrails §2) adds negligible cost.
- One-time **local** index builds (vector index for P1; BM25 index for P2) are a fixed setup cost in minutes, captured under Pillar 3 (Efficiency) as a research metric. **P3's summary-index build is the exception that uses an LLM** (free-tier `llama-3.1-8b-instant`) — see §2; it is one-time and cached.

If local CPU runs prove too slow during development, a free Google Colab / Kaggle session is a $0 fallback for the embedding/index-build step — available, not required.

---

## 5. What Changed From the Original Budget

| Original plan | Revised plan | Effect |
|---|---|---|
| $300 Vertex AI credit allocation | $0 — Groq free tier + local CPU | Removes all cloud spend exposure |
| Gemini 1.5 Pro / Flash (decommissioned) | gpt-oss-120b + Qwen3-32b + Llama 3.3 70B (Groq) | Restores a working, free model stack |
| Generator = Llama 3.3 70B | **Generator = gpt-oss-120b** | Cleaner family separation from the Qwen critic |
| Judge = Llama 3.3 70B | **Judge = Qwen3-32b** | Judge ≠ answerer family; no model grades its own output |
| Answerer **unspecified / uncosted** | **Answerer = Llama 3.3 70B, explicitly costed** | Closes the biggest gap in the old budget |
| (no structural pipeline) | **P3 Structural RAG + one-time llama-3.1-8b summary build** | New, but kept at $0 on the high-RPD model |
| Cohere Rerank (paid) | `bge-reranker-base` (local, $0) | Removes an unbudgeted paid surface |
| Paid embedding APIs | `bge-small-en-v1.5` (local, $0) | Removes embedding API spend |
| 2 pipelines × 3 K × 100 = 600 runs | **3 pipelines × 3 K × 100 = 900 runs** | +50% LLM volume, still $0 on free tier |
| "$0, finishes in 1–2 days" | **$0, ~2–3 weeks (TPD-bound) or ~1–2 days on paid Developer tier** | Corrects a false timeline claim |
| Binding constraint framed as RPD | **Binding constraint is TPD** | Accurate model of what actually gates throughput |

---

## 6. Single Hard Rule

> **No component in this project may bill per-hour or scale-to-non-zero.** All retrieval and indexing run locally or on a free tier; all LLM calls run on a free tier with request/token-rate limits, not spend. P3's summary-index build uses a free-tier LLM (`llama-3.1-8b-instant`), one-time and cached — it introduces no per-hour or persistent charge. If any design change would introduce a persistent or per-hour cloud charge (e.g. a managed vector DB endpoint, a hosted reranker, a premium parse tier), it must be re-scoped back to a local or free-tier equivalent before implementation — consistent with the absolute infrastructure ban in `Guardrails.md`.

*Free-tier limits and per-token prices rotate frequently. Re-verify Groq and LlamaParse figures against their live pricing/limits pages before any large batch run.*