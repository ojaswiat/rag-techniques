# Phase 4 Design Discussion — Doubts, Corrections, and Decisions

Working record of the reasoning that shaped Phase 4 (dataset generation) and
the corpus expansion, kept for the dissertation's methodology/limitations
discussion. Not a spec document — a record of what was debated and why the
final calls were made.

## 1. Judge design: reference-only vs. grounding-based scoring

**Question raised:** should the Judge (Phase 6) see the actual cited source
node content behind `gt_citations`, not just the pre-written
`ground_truth_answer` string, so it can verify pipeline answers against real
evidence rather than a single canned paraphrase?

**Assessment:** genuine technique (grounding-based/context-augmented judging
vs. pure reference-based judging), with real upside on Q2/Q4 (synthesis
quadrants, where a correct-but-differently-phrased answer could mismatch a
canned reference). Real costs against it:
- `ground_truth_answer` is already source-verified twice over by Phase 4's
  Generator/Critic adversarial loop — re-grounding the Judge in raw source
  text is largely re-proving something already guaranteed upstream.
- Token cost at scale: up to 900 Judge calls; adding full node content to
  every call multiplies free-tier spend.
- Breaks the prompt-caching design — the spec's "four cacheable prompt
  prefixes" (one per quadrant, from the 5 GQ exemplars) assumes a
  fixed-per-quadrant prefix; per-query source content would differ every
  call, killing the cache reuse.

**Decision:** kept reference-only Judge scoring as specified. Not revisited
as a blanket change; flagged as a possible targeted extension for Q2/Q4 only
if paraphrase-mismatch false negatives turn out to be a real problem once
live Judge output is seen (Phase 6).

## 2. Quadrant/issuer confound — corrected assessment

**Original finding (final whole-branch review of Phase 4):** flagged as
Critical — `next_target()`'s fill-order design (fill Q1 completely, then Q2,
etc., consuming filings in document order) means query quadrant ends up
correlated with filing issuer (e.g., Q1 mostly AAPL, Q4 mostly TSLA on the
original 9-filing corpus).

**Correction after discussion:** the primary analysis — comparing P1 vs P2
vs P3 per quadrant — is NOT confounded by this, because all three pipelines
are scored against the exact same query set per quadrant. Same-query,
cross-pipeline comparison holds regardless of which issuer a quadrant's
queries happen to be drawn from.

The real, smaller residual concern is `Project Idea.md`'s explicit hypothesis
that "P3 is expected to be weakest on table-heavy quadrants (Q3/Q4)" — a
within-pipeline, cross-quadrant claim (P3-on-Q4 vs P3-on-Q1). If Q4 skews
toward one issuer and Q1 toward another, "P3 does worse on Q4" could partly
reflect "P3 does worse on that issuer" rather than "P3 does worse on tables."
This is real but minor for an M.Sc. dissertation — a documented limitation,
not a blocker, and the spec already uses similarly hedged limitations
language elsewhere ("pragmatic reliability check... not strong statistical
proof").

**What's still being fixed regardless of the confound debate:** the
*content* mismatch — fill-order could hand the Generator a pure-prose
section and ask it to invent a table-extraction question anyway. That's a
data-quality problem independent of any statistical confound. Fix in
progress: content-aware routing (classify each section as table/text via
`node_type`, route table sections to Q3/Q4 and text sections to Q1/Q2),
interleaved across issuers as a secondary benefit, not the primary
justification.

## 3. Corpus expansion rationale

Added JPM, JNJ, WMT (financial services, healthcare, retail) alongside the
original AAPL/MSFT/TSLA (all tech/auto). Two purposes:
1. Directly gives the content-aware quadrant router (item 2 above) more
   issuers and more table-rich sections to draw from, reducing the residual
   issuer-clustering risk even for the secondary within-pipeline claims.
2. Broader sector coverage is defensible on its own terms for a benchmark
   that claims to generalize across "SEC 10-K financial filings," not just
   one industry vertical.

No formal selection criteria existed for the original three (a plain
`ticker`/`fiscal_year` manifest, no documented rationale found in
`resources/specs/`). The new three were chosen for sector diversity since
every 10-K legally contains both narrative (Item 1A Risk Factors, Item 7
MD&A) and tabular (Item 8 Financial Statements) content by SEC structure —
real differentiation comes from industry, not searching for special
"table-heavy" filers.

## 4. Fetch bug found during expansion (see also `Changes.md` entry)

SEC EDGAR's submissions API `recent` filings list is a fixed-size window
(~2,000 entries), not a fixed-time window. JPMorgan's filing volume (8-Ks,
debt shelf registrations, far more frequent than AAPL/MSFT/TSLA) had already
pushed its FY2023 and FY2024 10-Ks out of that window by the time of this
ingestion (2026-07-28) — confirmed live: `recent` held only the FY2025 10-K,
with the FY2023 filing 16 pages back in the paginated archive
(`CIK...-submissions-016.json`, `filingFrom: 2023-12-13`). Fixed with a
fallback that walks the paginated archive (newest page first) when no match
is found in `recent`. This wasn't a latent bug in the original 3-filing
corpus — AAPL/MSFT/TSLA simply never file often enough to hit it.
