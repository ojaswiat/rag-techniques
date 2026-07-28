Summary: P3 summarization-model suitability discussion

Trigger: clarified llama-3.1-8b-instant is Phase 3's P3 tree-index summarizer (not LlamaParse, a separate unrelated parsing service). This is the model that hit Groq's daily TPD cap while building indices for the new JPM/JNJ/WMT filings.

Critical concern raised: P3's retrieval works entirely off stored summary text (embedding similarity, no raw-text fallback), so summarizer fidelity is a hard ceiling on P3's whole retrieval quality. An 8B model is the smallest in the entire pipeline (vs. Generator 120B, Answerer 70B, Critic/Judge 27B) doing arguably one of the more fidelity-sensitive jobs — permanent, one-time, no-fallback compression of dense financial/numeric content. Real risk: if P3 underperforms on table-heavy quadrants, that could be an 8B-summarizer artifact rather than evidence about the summary-tree retrieval paradigm itself — muddying the dissertation's core causal claim.

Why 8B was chosen anyway (legitimate): Guardrails.md's $0/free-tier constraint — small models get much higher Groq free-tier throughput, needed since this step fires dozens of calls per filing in a burst.

Given you're open to spending extra days, three candidate replacements considered (all already-vetted on this Groq account):
1. Llama 3.3 70B — strongest fidelity upgrade, but rejected: it's also the shared Answerer model across P1/P2/P3. Making it the P3 summarizer too would mean the Answerer reads P3's summaries in its own writing style, but reads P1/P2's raw text with no such advantage — a one-sided structural bias favoring P3 in the very three-way comparison this dissertation depends on. (I initially framed this as a minor, unprovable "alignment bonus" — corrected after your pushback; it's a real, one-sided confound, not neutral.)
2. Qwen3.6-27B — current leading candidate: meaningfully better fidelity than 8B, avoids the Answerer-alignment confound (different model family), doesn't touch the anti-self-grading invariant (Judge≠Answerer stays intact), already proven accessible via Critic/Judge use.
3. gpt-oss-120b — likely best fidelity, but probably the tightest free-tier quota, could take even longer than the 8B route already has.

Status: not decided. Also unresolved: whether switching models for the 6 new filings only (leaving the original 9 on 8B) creates a cross-filing consistency problem worth documenting or avoiding. Parked, to resume later.

✻ Worked for 21s

❯ Also add: 1. Currently which models are being used for what purpose. How llama parse, groq, and models are working together to build the dataset for different pipelines. Mention why we choose a different model as compared to the answerer model.

Addendum: current model routing, end-to-end

LlamaParse (Phase 2, not Groq — separate document-parsing service): converts each raw SEC 10-K filing into structured markdown, then into nodes rows in the DB (node_type = text/table). This step is complete for all 18 filings; unrelated to any Groq model.

Groq-hosted models, by role and phase:

┌───────────────┬────────────────────────────┬────────────────────┬───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┐
│     Role      │           Model            │       Phase        │                                                            Purpose                                                            │
├───────────────┼────────────────────────────┼────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ P3 index      │ llama-3.1-8b-instant       │ 3 (once per        │ Summarizes a filing's nodes into a hierarchical TreeIndex, stored permanently at storage/summary_index/{document_id}/         │
│ build         │                            │ filing)            │                                                                                                                               │
├───────────────┼────────────────────────────┼────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Generator     │ gpt-oss-120b               │ 4                  │ Writes candidate benchmark questions + ground-truth answers from filing sections                                              │
├───────────────┼────────────────────────────┼────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Critic        │ Qwen3.6-27B (+ search      │ 4                  │ Independently re-derives an answer, blind, to verify the Generator's candidate before it's accepted into the dataset          │
│               │ tool)                      │                    │                                                                                                                               │
├───────────────┼────────────────────────────┼────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Answerer      │ Llama 3.3 70B              │ 5/7                │ Shared across all three pipelines (P1/P2/P3) — takes whatever context each pipeline retrieves and writes the actual benchmark │
│               │                            │                    │  answer                                                                                                                       │
├───────────────┼────────────────────────────┼────────────────────┼───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┤
│ Judge         │ Qwen3.6-27B                │ 6                  │ Grades the Answerer's output against ground truth, using GQ few-shot exemplars                                                │
└───────────────┴────────────────────────────┴────────────────────┴───────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────┘

How they connect: LlamaParse's nodes feed both Phase 3 (P3's one-time tree build) and Phase 4 (Generator/Critic dataset creation) independently — same source nodes, two separate uses. At benchmark time (Phase 5/7), each pipeline retrieves its own context (P1 vector similarity, P2 BM25, P3 the tree built in Phase 3) and hands it to the one shared Answerer. Phase 6's Judge then scores those Answerer outputs.

Why P3's summarizer is currently a different model from the Answerer: two reasons, one budget-driven, one now identified as a correctness issue.
1. Budget/throughput (the original reason): the index build fires many calls per filing in a fast burst — a small model (8B) gets much higher Groq free-tier throughput than the 70B Answerer, keeping the one-time build feasible within Guardrails.md's $0 constraint.
2. Fairness across pipelines (identified just now, in this conversation): even setting budget aside, the summarizer must not be the same model as the Answerer, because the Answerer serves P1/P2/P3 identically — if it also wrote P3's summaries, P3 alone would get a stylistic "home advantage" the other two pipelines structurally can't have. This is why the replacement candidate under discussion is Qwen3.6-27B (deliberately still a different model from the 70B Answerer), not Llama 3.3 70B — the fidelity upgrade must come from a model outside the Answerer's family, not from reusing it.