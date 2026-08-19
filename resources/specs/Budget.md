# Budget.md

## COMP702 Dissertation — Cost & Resource Plan

This document reconciles the project's resource requirements with a **near-zero-spend** operating model. It is the authoritative budget reference and supersedes any earlier cost framing (e.g. the previous $300 Google Cloud / Vertex AI allocation, which is **no longer part of this project**).

**Headline figure: the project runs at $10.00 in total spend — a single one-time OpenRouter credit top-up — with $0.00 recurring.** Every recurring component sits on a free tier or runs locally on CPU. The $10 buys request headroom, not tokens: OpenRouter raises the free-model daily request cap from 50/day to 1,000/day once an account has purchased $10 in lifetime credit, and the `:free` model ids stay $0 per token either way. **The binding constraint is still not money — it is per-day throughput: token-based (TPD) on Groq, request-based (RPD) on NIM and OpenRouter.** The sections below show the math, the limits that actually bind, and the worst-case fallback if a free tier is exceeded.

> **What changed in this revision:** the project now benchmarks **three pipelines (P1 Vector, P2 BM25, P3 Structural)**, not two, producing **900 runs** (was 600). Two LLM workloads that the earlier budget omitted are now costed explicitly: the **pipeline answer-generation** calls (the model that turns retrieved context into the answers being judged) and the **one-time P3 tree-index build**. The earlier "$0, finishes in 1–2 days" claim was incorrect once these are included and is corrected below.

---

## 1. Cost Model at a Glance

| Component | Tool / Model | Where it runs | Expected cost |
|---|---|---|---|
| Document parsing | LlamaParse (Cost-effective tier) | Hosted API (free tier) | $0.00 |
| Embeddings | `BAAI/bge-small-en-v1.5` | Local CPU | $0.00 |
| Re-ranker (P1) | `BAAI/bge-reranker-base` | Local CPU | $0.00 |
| BM25 retrieval (P2) | `rank_bm25` | Local CPU | $0.00 |
| Vector store (P1) | ChromaDB | Local disk | $0.00 |
| **P3 tree-index build (one-time)** | `nvidia/nemotron-3-super-120b-a12b` | NVIDIA NIM free tier | $0.00 |
| Query generation | `nvidia/nemotron-3-super-120b-a12b:free` | OpenRouter free tier | $0.00 |
| Query critique | `openai/gpt-oss-20b:free` (+ search tool) | OpenRouter free tier | $0.00 |
| **Pipeline answer generation (P1/P2/P3)** | `llama-3.3-70b-versatile` | Groq free tier | $0.00 |
| LLM-as-a-Judge | `qwen/qwen3.6-27b` | Groq free tier | $0.00 |
| State / results store | SQLite | Local disk | $0.00 |
| **OpenRouter credit top-up (one-time)** | — | OpenRouter account | **$10.00** |
| **Total** | | | **$10.00 one-time, $0.00 recurring** |

The binding constraint is **Groq's token-per-day ceiling** on the heaviest remaining workloads (answer generation and judging). Dataset generation and critique no longer touch Groq at all — both moved to OpenRouter, which is request-limited rather than token-limited. The rest of this document is about staying inside these limits, primarily via prompt caching and spreading work across days.

---

## 2. Provider Free Tiers — The LLM Workload

LLM calls are spread across three free tiers, because no single one has the headroom for every stage:

| Provider | Stages | Limit shape |
|---|---|---|
| **Groq** | Answerer, Judge, debug | Token-bound (TPM and TPD) |
| **NVIDIA NIM** | P3 tree-index build | Request-bound (~40 RPM), no published token ceiling |
| **OpenRouter** | Generator, Critic | Request-bound (~20 RPM, 1,000 requests/day at the funded tier) |

Groq's per-day token ceilings were the reason for the split: the Generator could not fit an oversized filing section inside an ~8,000 TPM window, and the Critic alone exhausted a 200,000 token/day cap.

### Published free-tier limits (verified mid-2026 — re-verify before runs)

| Model | Role | RPM | RPD | TPM | TPD |
|---|---|---|---|---|---|
| `qwen/qwen3.6-27b` | Judge | ~1,000 (per `project/groq_limits.md`, live-verified 2026-07-21) | unverified — needs console.groq.com/settings/limits | ~8,000 (per `project/groq_limits.md`, live-verified 2026-07-21) | unverified — needs console.groq.com/settings/limits |
| `llama-3.3-70b-versatile` | Pipeline answerer | ~30 | ~1,000 | ~12,000 | ~100,000 |
| `llama-3.1-8b-instant` | Throwaway debugging | ~30 | ~14,400 | higher | higher |

> Limits apply **per organization**, not per API key — extra keys do not raise the ceiling. You hit whichever limit arrives first. **For the token-heavy phases the daily-token (TPD) ceiling binds before the daily-request (RPD) ceiling** — e.g. Llama 3.3 70B's ~100K TPD is reached long before its ~1,000 RPD. **Cached tokens do not count toward limits**, so a consistent system prompt / rubric prefix stretches the free tier substantially. For Qwen, the ~8K **TPM** (per `project/groq_limits.md`, live-verified 2026-07-21) is the tight axis. Re-verify all figures at `console.groq.com` before a large run.

### Total LLM call budget for the whole project

| Phase | Model | Calls (incl. ~30% regeneration/retry overhead) |
|---|---|---|
| P3 tree-index build (one-time) | `nvidia/nemotron-3-super-120b-a12b` (NIM) | ~one per node, bulk |
| Dataset generation | `nvidia/nemotron-3-super-120b-a12b:free` (OpenRouter) | ~180 |
| Dataset critique | `openai/gpt-oss-20b:free` (OpenRouter) | ~180 |
| Pipeline answer generation (900 + 60 validation) | `llama-3.3-70b-versatile` (Groq) | ~960 |
| Judge evaluation (900 + 60 validation) | `qwen/qwen3.6-27b` (Groq) | ~960 |
| **Total (excl. one-time index build)** | | **~2,280 calls** |

### The TPD reality (this corrects the old "1–2 days" claim)

The two heavy phases are token-bound, not request-bound:

* **Answer generation (`Llama 3.3 70B`, ~100K TPD).** ~960 calls, each ~1–3K tokens (query + K retrieved nodes; larger at K=10), averaging ~2K → on the order of **~2M tokens**. Against ~100K TPD that is **roughly two-to-three weeks** of free-tier days, *not* 1–2. This is the project's true bottleneck.
* **Judging (`qwen/qwen3.6-27b`).** ~960 calls. With the rubric + 5 quadrant-matched few-shot exemplars **prompt-cached** (a static prefix that does not count toward limits), the uncached payload per call is small (~1K tokens), but Qwen's ~8K **TPM** (per `project/groq_limits.md`) still paces throughput. Spread across days, it fits comfortably.
* **Generation + critique.** ~180 calls each, and both now run on OpenRouter, so they consume no Groq tokens at all. They are paced by OpenRouter's 1,000 requests/day cap instead, which ~360 calls sits comfortably inside. Dataset generation is complete: 100 PQ, 20 GQ and 20 JEQ are in the database.

So the honest position: **on the free tiers, the full 900-run benchmark spans ~2–3 weeks of intermittent running** (well inside the 10-week timeline), gated by `llama-3.3-70b-versatile`'s TPD. It does **not** finish in 1–2 days for free.

### Cost-control rules (in priority order)
1. **Run the throttle first.** Per `Guardrails.md` §7, run the full pipeline end-to-end with `LOCAL_TEST_THROTTLE = True` (3 items) before any full run, to catch bugs before they burn quota.
2. **Pass the judge gate before the full run.** Per `Guardrails.md`, validate the Judge on the 60 Phase-2 outputs (>80% human agreement) *before* launching the 900-run matrix — never grade 900 outputs with an unvalidated judge.
3. **Cache the static prefix.** Cache the Judge rubric + the 5 per-quadrant few-shot exemplars (four cacheable prefixes, one per quadrant). Cached tokens do not count toward limits — this is the single biggest free lever on the judging phase.
4. **Resume, never restart.** The SQLite `results` table is checked on startup so a crash resumes from the last written row instead of re-spending calls.
5. **Build the P3 tree index once.** Persist it to disk; never rebuild. It runs on NIM (`nvidia/nemotron-3-super-120b-a12b`), so this bulk job does not touch Groq's daily token budget at all.
6. **Use `llama-3.1-8b-instant` for throwaway debugging**, reserving the 70B's daily cap for real answering and judging.

### Headroom levers if the TPD bottleneck bites
* **Prompt caching (free):** as above — apply it to the Judge and to any repeated system prompt in answer generation.
* **Spread across days (free):** the resume logic makes multi-day running painless; this adds no spend.
* **Alternate answerer (free):** if `llama-3.3-70b-versatile`'s ~100K TPD is too tight, moving the answerer to a free OpenRouter model trades Groq's token ceiling for OpenRouter's request ceiling. Any replacement must stay a *different family* from the Qwen judge so the no-self-judging rule holds, and must be shared identically across P1/P2/P3.
* **Developer tier (small spend):** adding a credit card unlocks ~10x rate limits with a ~25% token discount. This is the fastest way to compress the run to a day or two — see fallback below.

### Worst-case paid fallback (only if you opt out of the free tier for speed)
The whole LLM workload is on the order of **~4M tokens** (mostly input). At Llama 3.3 70B's paid rate (~$0.59 / 1M input, ~$0.79 / 1M output), even a generous estimate lands at **a worst-case ceiling of a few US dollars (~$3–5)**, not hundreds — and gpt-oss-120b is cheaper still ($0.15 / $0.60). The Batch API (50% off) and the Developer-tier 25% discount lower this further. The free-tier path remains the default; paid is purely an optional time-saver inside a trivial ceiling.

---

## 3. LlamaParse — The Ingestion Workload

LlamaParse stays as the parser, justified by its atomic-table-to-Markdown quality on financial filings. It is hosted, but the free tier covers the project. **The addition of P3 does not change parsing** — all three pipelines consume the same parsed nodes; only P3 adds a downstream tree-index build (costed in §2).

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
- One-time **local** index builds (vector index for P1; BM25 index for P2) are a fixed setup cost in minutes, captured under Pillar 3 (Efficiency) as a research metric. **P3's tree-index build is the exception that uses an LLM** (free-tier `nvidia/nemotron-3-super-120b-a12b` on NIM) — see §2; it is one-time and cached to disk.

If local CPU runs prove too slow during development, a free Google Colab / Kaggle session is a $0 fallback for the embedding/index-build step — available, not required.

---

## 5. What Changed From the Original Budget

| Original plan | Revised plan | Effect |
|---|---|---|
| $300 Vertex AI credit allocation | $0 recurring — three free tiers + local CPU | Removes all cloud spend exposure |
| Gemini 1.5 Pro / Flash (decommissioned) | Nemotron + gpt-oss-20b (OpenRouter), Llama 3.3 70B + Qwen3.6-27B (Groq) | Restores a working, free model stack |
| Generator = Llama 3.3 70B | **Generator = `nvidia/nemotron-3-super-120b-a12b:free` on OpenRouter** | Cleaner family separation from the critic, and escapes Groq's per-minute token wall |
| Judge = Llama 3.3 70B | **Judge = `qwen/qwen3.6-27b`** | Judge ≠ answerer family; no model grades its own output |
| Answerer **unspecified / uncosted** | **Answerer = `llama-3.3-70b-versatile`, explicitly costed** | Closes the biggest gap in the old budget |
| (no structural pipeline) | **P3 Structural RAG + one-time Nemotron tree build on NIM** | New, and kept at $0 on a request-limited tier |
| Single provider (Groq) | **Three providers: Groq, NVIDIA NIM, OpenRouter** | No single free tier had headroom for every stage |
| Cohere Rerank (paid) | `bge-reranker-base` (local, $0) | Removes an unbudgeted paid surface |
| Paid embedding APIs | `bge-small-en-v1.5` (local, $0) | Removes embedding API spend |
| 2 pipelines × 3 K × 100 = 600 runs | **3 pipelines × 3 K × 100 = 900 runs** | +50% LLM volume, still $0 per token |
| "$0, finishes in 1–2 days" | **~2–3 weeks (TPD-bound) or ~1–2 days on a paid tier** | Corrects a false timeline claim |
| $0.00 total | **$10.00 one-time OpenRouter top-up, $0.00 recurring** | Buys a 20x free-model request cap; no per-token or per-hour charge |
| Binding constraint framed as RPD | **Binding constraint is TPD** | Accurate model of what actually gates throughput |

---

## 6. Single Hard Rule

> **No component in this project may bill per-hour or scale-to-non-zero.** All retrieval and indexing run locally or on a free tier; all LLM calls run on a free tier with request/token-rate limits, not per-token spend. The one-time $10 OpenRouter top-up buys request headroom on those free tiers and is neither recurring nor per-hour, so it does not breach this rule. P3's tree-index build uses a free-tier LLM (`nvidia/nemotron-3-super-120b-a12b` on NIM), one-time and cached — it introduces no per-hour or persistent charge. If any design change would introduce a persistent or per-hour cloud charge (e.g. a managed vector DB endpoint, a hosted reranker, a premium parse tier), it must be re-scoped back to a local or free-tier equivalent before implementation — consistent with the absolute infrastructure ban in `Guardrails.md`.

*Free-tier limits and per-token prices rotate frequently. Re-verify Groq and LlamaParse figures against their live pricing/limits pages before any large batch run.*