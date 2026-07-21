# Architecture.md

## COMP702 Dissertation — Technical Architecture (v2)

This document maps `Phase Plan.md`'s eight build phases onto concrete code: packages, modules, an entity-relationship design with full table DDL, a high-level component view, a low-level interface/sequence view, and worked example rows. It is the **technical build only** — it does not cover the CA1 proposal or the dissertation write-up.

This is a methodology-chapter-appropriate level of design detail (an M.Sc. dissertation's system-design section), not a production software-design document. No container orchestration, CI/CD pipeline, microservice split, or formal test-coverage target is introduced — everything still runs as plain Python processes on one local machine, per `Guardrails.md`'s $0/local mandate.

**v2 changes from the first draft:** a self-critique (§1) surfaced one real schema defect (a row-cardinality mismatch in `judge_validation`) and several missing low-level specifications, all resolved below; the timeline is expanded from 8 to 10 weeks to give the now-larger multi-filing corpus realistic runway; and the document adds the ER/HLD/LLD layers and example data the first draft only gestured at.

---

## 0. Decisions Carried Over From the Scoping Discussion

1. **Corpus: ~6–9 filings (2–3 companies × 2–3 fiscal years)**, not one document. The fixed counts from `Project_Idea.md` (140 total queries, 100/20/20 split, 900 benchmark runs) are unchanged — only where queries are sourced from changes.
2. **Retrieval scope: per-document, not cross-corpus.** Every pipeline retrieves only within the one filing (`document_id`) a query is about. This is *not* the metadata pre-filter `Guardrails.md` §3 bans — that ban is about narrowing to a target *section* using answer-derived information; narrowing to the correct *filing* is a property of the query itself (every query already carries `document_id`), applied identically to all three pipelines.
3. **P1 vector store: ChromaDB** (local, embedded) — the third option `Guardrails.md` §1 leaves open.

---

## 1. Design Review: Issues Found and Resolved

Going from a phase-by-phase narrative to an actual table/interface design surfaced eight concrete issues. All are resolved in the sections referenced; none required adding scope beyond what `Project_Idea.md` / `Phase Plan.md` / `Guardrails.md` already specify.

| # | Issue | Resolution |
|---|---|---|
| 1 | **Schema cardinality defect.** `Guardrails.md` §6 described `judge_validation` being written in stages with *"the pipeline output... the human score and the judge score"* — singular, implying one output per row. But `Phase Plan.md` Phase 6 and `Project_Idea.md` §5/§7 require running the 20 JEQ through **three** pipelines (P1, P2, P3) at K=5, producing **60** outputs. A 20-row table cannot hold 60 (query, pipeline) outputs without either repeating columns three times or breaking 1NF. | §3.2/§3.3: pipeline outputs for *both* the 900 PQ runs and the 60 JEQ-gate runs now live in one unified `results` table, distinguished by a new `source_set ∈ {PQ, JEQ}` column, with a nullable `human_score` column added (populated only for `JEQ` rows). `judge_validation` keeps only its 20 rows of question/ground-truth fields. **Still exactly 5 tables** — no guardrail violation. `Guardrails.md` §6 has since been reworded to match this design exactly. |
| 2 | **No citation-marker convention.** The Citation Audit metric needs `cited_node_ids` parsed out of the answerer's free-text output, but nothing specified the format the model is told to cite in. | §4.2: fixed `[[node:<node_id>]]` inline marker, parsed by a regex in the shared `Answerer`. |
| 3 | **No numeric-normalization design.** `Project_Idea.md` §7 requires `$394.3B` ≡ `394,300 million` for Exact Match, but no normalizer existed. | §4.3: `judge/numeric_normalizer.py`. |
| 4 | **No storage convention for list-valued columns.** `gt_citations`, `retrieved_node_ids`, `cited_node_ids` are lists; SQLite has no array type. | §4.4: JSON-encoded `TEXT`, with (de)serializing helpers centralized in `database_manager.py` so no other module touches raw JSON. |
| 5 | **Missing indexes.** Every pipeline call does `WHERE document_id = ?` against `nodes`, repeated up to 960 times; unindexed, this degrades badly once the corpus is 6–9 filings instead of 1. | §3.2: `idx_nodes_document_id`, plus lookup indexes on `results`. |
| 6 | **No precise resume key.** `Guardrails.md` §6 mandates crash-resume, but "resume from the last written row" needs an exact uniqueness key to check against. | §3.2: `UNIQUE(source_set, query_id, pipeline, k_value)` on `results` — also exactly `get_completed_keys()`'s lookup shape (§4.1). |
| 7 | **`schemas/db_schema_example.jsonc` is stale**, still showing 2 pipelines / 600 rows / 12 JEQ. | Superseded by §3 below; recommend regenerating that file from this document rather than keeping both as separate sources of truth. |
| 8 | **Timeline was inherited unchanged from a single-filing, 8-week plan** even after the corpus grew to ~9 filings. | §8: expanded to 10 weeks, extra time allocated to ingestion/parsing and dataset generation (more filings, more sections), not to new scope. |

A ninth point is a flagged ambiguity rather than a fix — see §12, item 3 (context-mass standardization).

---

## 2. High-Level Design (HLD)

### 2.1 Component View

```text
                         +-------------------------------+
                         |   SEC EDGAR (external)        |
                         +---------------+---------------+
                                         | raw filings (HTML), per data/filings_manifest.json
                                         v
                         +-----------------------------+
                         |  Ingestion Component        |
                         |  ingest/*.py                |
                         |  external: LlamaParse API   |
                         +---------------+---------------+
                                         | TextNodes (node_id, document_id, ...)
                                         v
                         +-----------------------------+
                         |   nodes  (SQLite)           |
                         +-------+---------------+-----+
                                 |               |
                 +---------------+               +---------------+
                 v                                               v
   +-----------------------------+               +-------------------------------+
   |  Dataset Generation         |               |  Pipeline Index Builders      |
   |  dataset_gen/*.py           |               |  pipelines/*                  |
   |  external: Groq             |               |  P1: ChromaDB + bge embed     |
   |  (gpt-oss-120b, Qwen3-32b)  |               |  P2: rank_bm25 (per document) |
   +---------------+-----------------+           |  P3: SummaryIndex (1x build,  |
                   | queries / golden_queries /  |      llama-3.1-8b-instant)    |
                   | judge_validation            +---------------+---------------+
                   v                                             |
   +-------------------------------------------------------------------------------------+
   |                          Loop Executor  (loop_executor.py)                          |
   |   for each (source_set, query_id, pipeline, k) not yet in results:                  |
   |       retrieve (P1/P2/P3, scoped to query's document_id)  ->  answer (shared Llama  |
   |       3.3 70B answerer, temp 0)  ->  upsert into results                            |
   +-------------------------------------------+-----------------------------------------+
                                                 | results rows (PQ + JEQ-gate)
                                                 v
                         +-----------------------------+
                         |   Judge & Metrics           |
                         |   judge/*.py                |
                         |   external: Groq Qwen3-32b  |
                         +---------------+---------------+
                                         | scored results
                                         v
                         +-----------------------------+
                         |   Analysis  (analysis/*.py) |
                         |   pandas + matplotlib       |
                         +-----------------------------+
```

### 2.2 Deployment View

Everything runs as plain Python processes on the researcher's own machine — there is no server, container, or managed cloud component, per `Guardrails.md` §1/§8:

```text
  +---------------------------------------------------------------+
  |  Local machine                                                |
  |                                                               |
  |  Python process(es)  --  benchmark.db (SQLite, WAL)           |
  |       |        \                                              |
  |       |         \-- storage/chroma/   (P1, on disk)           |
  |       |         \-- storage/bm25/     (P2, pickled corpora)  |
  |       |         \-- storage/summary_index/ (P3, per filing)  |
  |       |         \-- HuggingFace model cache (bge models)      |
  |       v                                                       |
  +-------+----------------------------------------------------+
          | outbound HTTPS only
          v
  +----------------+   +----------------+   +----------------+
  |   Groq API      |   |  LlamaParse API |   |  SEC EDGAR      |
  |  (free tier)     |   |  (free tier)     |   |  (public files) |
  +----------------+   +----------------+   +----------------+
```

### 2.3 Data-Flow Summary

`nodes` is the single source for everything downstream. Two consumers read it independently: dataset generation (Phase 4, produces the three query tables) and the three pipeline index builders (Phase 3/5, produce on-disk indexes keyed by `document_id`). Both feed `loop_executor.py`, which is the only writer of `results`. `results` is the single input to both the Judge (Phase 6) and the analysis scripts (Phase 8).

---

## 3. Entity-Relationship Design

### 3.1 ER Diagram

```text
+-------------------+              +---------------------------+
|      nodes        |              |        queries  (PQ)       |
|-------------------|              |---------------------------|
| node_id       PK  |<----+        | query_id            PK     |
| document_id       |     |        | quadrant                    |
| parent_item_header|     |        | query_text                  |
| node_type         |     |        | ground_truth_answer         |
| source_page_num   |     |        | gt_citations  (JSON, soft FK to node_id) --+
| content           |     |        | document_id                 |             |
| token_count       |     |        | verified                     |             |
+-------------------+     |        +---------------------------+             |
                          |                       ^                          |
                          |                       | query_id (source_set='PQ')|
                          |                       |                          |
+-------------------+     |        +---------------------------+             |
|  golden_queries    |     |        |          results            |             |
|  (GQ, teaching;     |     |        |---------------------------|             |
|   never joined to   |     |        | result_id           PK     |             |
|   results)           |     |        | source_set  'PQ' | 'JEQ'   |             |
|---------------------|     |        | query_id                    |<-+ FK to queries.query_id (PQ)
| query_id        PK  |     +--------| pipeline                     |  |   or judge_validation.query_id (JEQ)
| quadrant            |              | k_value                      |  |
| query_text          |              | retrieved_node_ids (JSON) ----+--+ (soft FK to node_id, many)
| ground_truth_answer |              | pipeline_output               |
| gt_citations (JSON) |              | cited_node_ids (JSON) ---------+ (soft FK to node_id, many)
| example_output      |              | precision_at_k / recall_at_k /  |
| human_score         |              | evidence_hit / citation_match / |
| human_reasoning     |              | token_f1 / exact_match /         |
| document_id         |              | judge_score / human_score /       |
+-------------------+               | latency_sec / input_tokens /        |
                                     | output_tokens                       |
                                     +---------------------------+
                                                  ^
                                                  | query_id (source_set='JEQ')
                                     +---------------------------+
                                     |  judge_validation (JEQ)     |
                                     |---------------------------|
                                     | query_id            PK     |
                                     | quadrant                    |
                                     | query_text                  |
                                     | ground_truth_answer         |
                                     | gt_citations (JSON)          |
                                     | document_id                  |
                                     +---------------------------+
```

`gt_citations` / `retrieved_node_ids` / `cited_node_ids` are **soft FKs**: SQLite cannot enforce a foreign key into values packed inside a JSON array, so referential integrity for these is an application-level invariant (a debug assertion in `database_manager.py` that every id in such a list exists in `nodes`), not a database-enforced constraint.

### 3.2 Table DDL

```sql
PRAGMA journal_mode = WAL;

CREATE TABLE nodes (
    node_id            TEXT PRIMARY KEY,
    document_id        TEXT NOT NULL,
    parent_item_header TEXT,
    node_type          TEXT NOT NULL CHECK (node_type IN ('text', 'table')),
    source_page_num    INTEGER,
    content            TEXT NOT NULL,
    token_count        INTEGER NOT NULL
);
CREATE INDEX idx_nodes_document_id ON nodes(document_id);

CREATE TABLE queries (
    query_id            TEXT PRIMARY KEY,
    quadrant            TEXT NOT NULL CHECK (quadrant IN
                         ('Q1_Direct_Text','Q2_Implicit_Text','Q3_Direct_Table','Q4_Implicit_Table')),
    query_text          TEXT NOT NULL,
    ground_truth_answer TEXT NOT NULL,
    gt_citations        TEXT NOT NULL,   -- JSON array of node_id
    document_id         TEXT NOT NULL,
    verified            INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0,1))
);
CREATE INDEX idx_queries_document_id ON queries(document_id);

CREATE TABLE golden_queries (
    query_id            TEXT PRIMARY KEY,
    quadrant            TEXT NOT NULL CHECK (quadrant IN
                         ('Q1_Direct_Text','Q2_Implicit_Text','Q3_Direct_Table','Q4_Implicit_Table')),
    query_text          TEXT NOT NULL,
    ground_truth_answer TEXT NOT NULL,
    gt_citations        TEXT NOT NULL,   -- JSON array of node_id
    example_output       TEXT NOT NULL,
    human_score          INTEGER NOT NULL CHECK (human_score BETWEEN 1 AND 10),
    human_reasoning       TEXT NOT NULL,
    document_id           TEXT NOT NULL
);

CREATE TABLE judge_validation (
    query_id            TEXT PRIMARY KEY,
    quadrant            TEXT NOT NULL CHECK (quadrant IN
                         ('Q1_Direct_Text','Q2_Implicit_Text','Q3_Direct_Table','Q4_Implicit_Table')),
    query_text          TEXT NOT NULL,
    ground_truth_answer TEXT NOT NULL,
    gt_citations        TEXT NOT NULL,   -- JSON array of node_id
    document_id         TEXT NOT NULL
    -- NOTE: pipeline_output / human_score / judge_score deliberately NOT here — see §1 issue #1.
    -- They live in `results`, keyed by (source_set='JEQ', query_id, pipeline, k_value).
);

CREATE TABLE results (
    result_id            TEXT PRIMARY KEY,
    source_set            TEXT NOT NULL CHECK (source_set IN ('PQ','JEQ')),
    query_id              TEXT NOT NULL,   -- FK -> queries.query_id (PQ) or judge_validation.query_id (JEQ)
    pipeline               TEXT NOT NULL CHECK (pipeline IN ('P1_vector','P2_bm25','P3_structural')),
    k_value                 INTEGER NOT NULL CHECK (k_value IN (3,5,10)),
    retrieved_node_ids       TEXT NOT NULL,   -- JSON array of node_id
    pipeline_output           TEXT,
    cited_node_ids             TEXT,         -- JSON array of node_id
    precision_at_k              REAL,
    recall_at_k                  REAL,
    evidence_hit                  INTEGER CHECK (evidence_hit IN (0,1)),
    citation_match                 INTEGER CHECK (citation_match IN (0,1)),
    token_f1                         REAL,
    exact_match                       INTEGER CHECK (exact_match IN (0,1)),   -- NULL for Q2/Q4
    judge_score                        INTEGER CHECK (judge_score BETWEEN 1 AND 10),
    human_score                         INTEGER CHECK (human_score BETWEEN 1 AND 10),  -- only for source_set='JEQ'
    latency_sec                          REAL,
    input_tokens                          INTEGER,
    output_tokens                          INTEGER,
    UNIQUE (source_set, query_id, pipeline, k_value)
);
CREATE INDEX idx_results_query_id   ON results(query_id);
CREATE INDEX idx_results_pipeline_k ON results(pipeline, k_value);
```

Row volume: `nodes` ≈ a few thousand (6–9 filings); `queries` = 100; `golden_queries` = 20; `judge_validation` = 20; `results` = 900 (PQ, full benchmark) + 60 (JEQ, Phase-6 gate) = **960 rows**.

### 3.3 Example Rows

Illustrative corpus: **AAPL, MSFT, TSLA** (3 companies) × **FY2023, FY2024, FY2025** (3 fiscal years) = 9 filings — within the agreed 2–3×2–3 range.

**`nodes`**

| node_id | document_id | parent_item_header | node_type | source_page_num | content | token_count |
|---|---|---|---|---|---|---|
| `AAPL_2025_n0421` | `SEC_10K_AAPL_2025` | Item 8 | table | 62 | `\| Year \| Net Sales \|\n\|---\|---\|\n\| 2025 \| 394,328 \|` | 180 |
| `MSFT_2024_n0118` | `SEC_10K_MSFT_2024` | Item 1A | text | 14 | "Our cloud business may be adversely affected by intense competition among a small number of hyperscale providers..." | 142 |
| `TSLA_2023_n0299` | `SEC_10K_TSLA_2023` | Item 7 | text | 41 | "Vehicle deliveries increased 38% year-over-year, driven primarily by higher production volumes at Gigafactory Texas and Gigafactory Berlin..." | 165 |

**`queries`**

| query_id | quadrant | query_text | ground_truth_answer | gt_citations | document_id | verified |
|---|---|---|---|---|---|---|
| `Q3_017` | Q3_Direct_Table | "What was Apple's total net sales for FY2025?" | "$394.3B" | `["AAPL_2025_n0421"]` | `SEC_10K_AAPL_2025` | 1 |
| `Q2_044` | Q2_Implicit_Text | "How did Tesla's management characterize the driver of FY2023 delivery growth?" | "Management attributed the increase primarily to higher production volumes at the Texas and Berlin gigafactories." | `["TSLA_2023_n0299"]` | `SEC_10K_TSLA_2023` | 1 |

**`golden_queries`**

| query_id | quadrant | query_text | ground_truth_answer | gt_citations | example_output | human_score | human_reasoning | document_id |
|---|---|---|---|---|---|---|---|---|
| `G_Q4_03` | Q4_Implicit_Table | "Calculate the YoY change in Microsoft's total operating expenses for FY2024." | "Decreased 4.2% YoY." | `["MSFT_2024_n0588","MSFT_2024_n0742"]` | "Operating expenses fell about 4% year over year." | 8 | "Correct direction and magnitude, but vague on the exact figure." | `SEC_10K_MSFT_2024` |

**`judge_validation`**

| query_id | quadrant | query_text | ground_truth_answer | gt_citations | document_id |
|---|---|---|---|---|---|
| `V_Q1_02` | Q1_Direct_Text | "Name the primary risk factor Microsoft cites for its cloud business." | "Concentration risk: reliance on a small number of hyperscale competitors and on data-center capacity." | `["MSFT_2024_n0118"]` | `SEC_10K_MSFT_2024` |

**`results`** — one PQ row, one Q2/Q4-style row showing `exact_match = NULL`, and two JEQ-gate rows for the same validation query across two pipelines (demonstrating how 60 gate outputs fit into one table):

| result_id | source_set | query_id | pipeline | k_value | retrieved_node_ids | pipeline_output | cited_node_ids | precision_at_k | recall_at_k | evidence_hit | citation_match | token_f1 | exact_match | judge_score | human_score | latency_sec | input_tokens | output_tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `R_000457` | PQ | `Q3_017` | P1_vector | 5 | `["AAPL_2025_n0421","AAPL_2025_n0420"]` | "Apple's FY2025 net sales were $394.3B. [[node:AAPL_2025_n0421]]" | `["AAPL_2025_n0421"]` | 0.20 | 1.0 | 1 | 1 | 0.95 | 1 | 9 | NULL | 1.84 | 2100 | 40 |
| `R_000312` | PQ | `Q2_044` | P3_structural | 10 | `["TSLA_2023_n0299", "TSLA_2023_n0301"]` | "Management cited higher production at the Texas and Berlin gigafactories. [[node:TSLA_2023_n0299]]" | `["TSLA_2023_n0299"]` | 0.30 | 1.0 | 1 | 1 | 0.58 | NULL | 7 | NULL | 2.40 | 3100 | 85 |
| `R_G00012` | JEQ | `V_Q1_02` | P2_bm25 | 5 | `["MSFT_2024_n0118","MSFT_2024_n0119"]` | "Reliance on a small number of third-party cloud/data-center providers. [[node:MSFT_2024_n0118]]" | `["MSFT_2024_n0118"]` | 0.20 | 1.0 | 1 | 1 | 0.62 | NULL | 6 | 7 | 0.91 | 1800 | 22 |
| `R_G00013` | JEQ | `V_Q1_02` | P3_structural | 5 | `["MSFT_2024_n0118"]` | "Concentration of supply among a few hyperscale cloud competitors. [[node:MSFT_2024_n0118]]" | `["MSFT_2024_n0118"]` | 1.0 | 1.0 | 1 | 1 | 0.71 | NULL | 7 | 7 | 1.10 | 1950 | 28 |

Note `exact_match = NULL` on the Q2/Q4 row (per `Project_Idea.md` §7, EM is Q1/Q3-only) and `human_score = NULL` on the PQ rows (only `JEQ` rows are hand-scored, per the Phase 6 gate).

### 3.4 Integrity Notes

* Disjointness across `queries` / `golden_queries` / `judge_validation` (`Guardrails.md` §3) is enforced at write time in `dataset_gen/split_and_label.py`, not by a database constraint — SQLite can't express "no PK value may repeat across three named tables" declaratively.
* `results.UNIQUE(source_set, query_id, pipeline, k_value)` is both the data-integrity constraint and the literal resume-lookup key for `loop_executor.py`.

---

## 4. Low-Level Design (LLD)

### 4.1 Core Interfaces

```python
# pipelines/base.py
class Retriever(ABC):
    def retrieve(self, query_text: str, document_id: str, k: int) -> list[NodeWithScore]: ...
    # every implementation (P1/P2/P3) must filter to `document_id` internally — never search
    # outside the query's own filing (Decision §0.2).

@dataclass
class AnswerResult:
    raw_text: str
    cited_node_ids: list[str]
    input_tokens: int
    output_tokens: int
    latency_sec: float

class Answerer:
    def __init__(self, model: str = "llama-3.3-70b-versatile", temperature: float = 0.0): ...
    async def answer(self, query_text: str, nodes: list[NodeWithScore]) -> AnswerResult: ...
    # prompt contains ONLY query_text + nodes' content — no exemplars, no ground truth (Guardrails §3)

# database_manager.py
async def insert_node(node: NodeRow) -> None: ...
async def get_nodes_by_document(document_id: str) -> list[NodeRow]: ...
async def upsert_result(row: ResultRow) -> None: ...
async def get_completed_keys(source_set: str) -> set[tuple[str, str, int]]: ...
    # -> {(query_id, pipeline, k_value), ...} already committed; loop_executor.py skips these

# pipelines/keyword/tokenizer.py
def tokenize(text: str) -> list[str]: ...
    # one function, imported by both the index-build step and the query-time step — never two
    # separate implementations (Guardrails §2)

# judge/metrics.py
def citation_audit(cited_node_ids: list[str], gt_citations: list[str]) -> bool: ...   # cited ⊆ gt
def precision_at_k(retrieved: list[str], gt: list[str], k: int) -> float: ...
def recall_at_k(retrieved: list[str], gt: list[str]) -> float: ...
def token_f1(output_text: str, gt_text: str) -> float: ...
def exact_match(output_text: str, gt_text: str, *, numeric_tolerance: float = 0.01) -> bool | None: ...
    # returns None when the quadrant is Q2/Q4 (caller passes quadrant; EM is Q1/Q3-only)
```

### 4.2 Citation Marker Convention and Parser

The shared `Answerer`'s prompt instructs the model: *"After any claim drawn from a source, immediately append `[[node:<node_id>]]` citing the exact node it came from."* `Answerer.answer()` then runs `re.findall(r"\[\[node:([\w\-]+)\]\]", raw_text)` to populate `cited_node_ids` (deduplicated, order-preserved). The markers are **kept** in `pipeline_output` (not stripped) — see the `results` examples in §3.3 — so the raw model output remains auditable against its own citations rather than being silently rewritten before storage.

### 4.3 Numeric Normalization for Exact Match

`judge/numeric_normalizer.py`:

```python
def normalize_numeric(text: str) -> Decimal | None:
    # strips currency symbols ($, £, €) and thousands separators, expands suffix
    # multipliers (K/M/B/T and "thousand"/"million"/"billion"/"trillion"), returns
    # a Decimal, or None if the string isn't numeric.
```

`exact_match()` (§4.1) tries `normalize_numeric` on both `output_text` and `gt_text`; if both parse, it compares within a relative epsilon (default 1%) so `"$394.3B"` and `"394,300 million"` match. If either side fails to parse (a short named-entity answer, e.g. Q1), it falls back to a normalized-string comparison (lowercased, punctuation-stripped).

### 4.4 JSON-in-SQLite Convention

`gt_citations`, `retrieved_node_ids`, and `cited_node_ids` are stored as `json.dumps(list_of_str)` in a `TEXT` column — SQLite has no native array type. `database_manager.py` is the only module that touches the raw JSON string; every other module receives/returns plain Python `list[str]`.

### 4.5 Sequence Diagrams

**(a) One benchmark cell** (the central, most-repeated flow — runs 960 times):

```text
loop_executor.py          Retriever (P1/P2/P3)      Answerer            Groq API         results (SQLite)
      |                          |                      |                   |                    |
      |--get_completed_keys()-------------------------------------------------------------------->|
      |<-- {(query_id,pipeline,k), ...} -------------------------------------------------------------|
      |--(skip if key already present)--|                |                   |                    |
      |--retrieve(query_text, document_id, k)-->|         |                   |                    |
      |<--List[NodeWithScore]--------------------|         |                   |                    |
      |--answer(query_text, nodes)--------------------------->|                |                    |
      |                                                       |--chat.completions.create(           |
      |                                                       |   model=Llama-3.3-70B, temp=0)----->|
      |                                                       |<--completion---------------------------|
      |                                                       |--parse [[node:...]] -> cited_node_ids  |
      |<--AnswerResult----------------------------------------|                |                    |
      |--upsert_result(row)---------------------------------------------------------------------------->|
```

**(b) Judge validation gate** (Phase 6, 60 outputs):

```text
validation_gate.py     loop_executor.py    score_gate_outputs.py    async_judge.py     results
      |                       |                     |                     |               |
      |--run JEQ(20) x {P1,P2,P3} @ K=5 via loop_executor------------------------------------->| (60 rows, source_set='JEQ')
      |                       |                     |                     |               |
      |--prompt researcher for human_score per row------>|                                    |
      |                                              |--UPDATE results SET human_score=...----->|
      |--for each of the 60 rows: build quadrant-matched 5-exemplar prefix, call Qwen3-32b------>|
      |                                                                     |--UPDATE results SET judge_score=...-->|
      |--compute Agreement Rate = f(human_score, judge_score) over the 60 rows------------------>|
      |--gate: Agreement Rate > 80%? --(NO)--> stop, fix rubric/model, re-run
      |                              --(YES)--> Phase 7 permitted to start
```

**(c) Dataset generation + critique** (Phase 4, per candidate query):

```text
async_generator.py        search_tool.py          async_critic.py       cross_check.py    queries/GQ/JEQ tables
      |                          |                       |                     |                  |
      |--read one (document_id, section) chunk-->|        |                     |                  |
      |--emit candidate {query_text, gt_answer, gt_citations}-->|                |                  |
      |                          |                       |<--query_text ONLY---|                  |
      |                          |<--search(query_text, document_id)-----------|                  |
      |                          |--BM25 results (independent of Generator)--->|                  |
      |                          |                       |--cite node(s) + value found------------>|
      |                          |                       |                     |--compare vs gt-->|
      |                          |                       |                     |--Auto-Verified or Discard-->|
      |                          |                       |                     |                  |--(if verified) insert into queries/GQ/JEQ--|
```

---

## 5. Cross-Cutting Architectural Decisions

(Unchanged from the first draft; restated briefly for completeness.)

* **LlamaIndex as the common backbone** — a node is a LlamaIndex `TextNode`; a retrieval result is `List[NodeWithScore]` for all three pipelines, so `loop_executor.py` and the answerer never need pipeline-specific branching.
* **`aiosqlite` for the async write path** over the `sqlite3`-defined schema in §3.2 — commits never block the event loop.
* **`LOCAL_TEST_THROTTLE` stays hardcoded per script**, never centralized — `Guardrails.md` §7 requires it be consciously toggled in each file individually.
* **Filing manifest instead of a discovery package** — `data/filings_manifest.json` lists the ~6–9 known filings; `requests` downloads them. No `sec-edgar-downloader`-style package is needed for a fixed, small, known list.
* **P3 retrieval stays local** — `SummaryIndex.as_retriever(retriever_mode="embedding", similarity_top_k=k)` scores summary nodes by embedding similarity (reusing `bge-small-en-v1.5`), never calling Groq at query time, per `Guardrails.md` §1 ("P3 retrieval at query time is local"). This is also how K∈{3,5,10} applies to P3, matching `Project_Idea.md` §7's requirement that all three pipelines are tested at all three K values.
* **The Critic's search tool is self-contained** — a standalone `rank_bm25` instance scoped to one document, not a forward import of Phase 5's P2 module (Phase 4 runs before Phase 5 per the week numbers in §8).

---

## 6. Phase-by-Phase Architecture

### Phase 1 — Environment, Infrastructure & Cost Guardrails (Week 1)

| Module | Responsibility |
|---|---|
| `config.py` | Loads `.env`; holds the model-routing map from `Guardrails.md` §2 as named constants. |
| `database_manager.py` | DDL from §3.2; WAL mode; typed helpers including JSON (de)serialization (§4.4) and `get_completed_keys` (§4.1). |
| `groq_client.py` | `tenacity`-decorated wrapper around `groq.AsyncGroq`; `asyncio.Semaphore(5)`. |
| `groq_limits.md` | Verified RPM/RPD/TPM/TPD per model, dated. |
| `tests/test_groq_client_backoff.py` | Mocked-429 backoff/recovery test. |

**Packages:** `groq`, `tenacity`, `aiosqlite`, `python-dotenv`, `pytest`, `pytest-asyncio`.

---

### Phase 2 — Ingestion & Parsing Pipeline (Weeks 1–3)

*(extended by one week from the original single-filing plan — see §8)*

| Module | Responsibility |
|---|---|
| `data/filings_manifest.json` | `{document_id, ticker, fiscal_year, source_url}` for each of the ~9 filings. |
| `ingest/fetch_filings.py` | Downloads each raw filing; caches to `data/raw/{document_id}.html`. |
| `ingest/parse_filing.py` | `LlamaParse` (Cost-effective tier, markdown, atomic-table instructions) per filing; caches to `data/parsed/{document_id}.md`. |
| `ingest/node_builder.py` | Markdown → `TextNode`s; assigns `node_id` (`{ticker}_{fiscal_year}_n{NNNN}`), `document_id`, `parent_item_header`, `node_type`, `source_page_num`; never bisects a table block. |
| `ingest/parsing_audit.py` | Randomized 20-section sample across the corpus for manual audit. |

**Data flow:** writes `nodes` (§3.2/§3.3). **Packages:** `llama-parse`, `llama-index-core`, `requests`.

---

### Phase 3 — P3 Summary-Index Build, one-time (Week 3)

*One summary tree per filing — summaries are bound to one document's section hierarchy.*

| Module | Responsibility |
|---|---|
| `pipelines/structural/build_summary_index.py` | Per `document_id`, builds a `SummaryIndex` over that document's nodes using `llama-3.1-8b-instant`; persists to `storage/summary_index/{document_id}/`; directory-existence check is the cache test. |
| `logs/index_build_costs.json` | One row per filing: wall-clock + token cost (Pillar 3 metric). Flat-file is acceptable here — ~9 rows, no crash-resume requirement, unlike `results`. |

**Packages:** `llama-index-core`, `llama-index-llms-groq`.

---

### Phase 4 — Dataset Generation & Adversarial Verification (Weeks 4–5)

*35/quadrant accumulated across the whole corpus, not per filing.*

| Module | Responsibility |
|---|---|
| `dataset_gen/async_generator.py` | Generator (`openai/gpt-oss-120b`) reads one `(document_id, section)` chunk at a time; accumulates 35/quadrant across all ~9 filings. |
| `dataset_gen/search_tool.py` | Critic's independent search tool — fresh `rank_bm25` instance per document (§5, self-contained). |
| `dataset_gen/async_critic.py` | Critic (`Qwen3-32b`), blind to the Generator's answer/citations. |
| `dataset_gen/cross_check.py` | Deterministic node-ID + value comparison → Auto-Verify or discard. |
| `dataset_gen/split_and_label.py` | Splits into disjoint `queries`(100)/`golden_queries`(20)/`judge_validation`(20); enforces 25/5/5-per-quadrant strata and no shared `query_id`. |
| `dataset_gen/label_gq.py` | CLI: prompts the researcher for `human_score` + `human_reasoning` on the 20 GQ. |

**Data flow:** reads `nodes`; writes `queries`, `golden_queries`, `judge_validation` (question fields only, per the redesign in §1 issue #1). **Packages:** `groq`, `rank_bm25` (already introduced).

---

### Phase 5 — Pipeline Implementation: P1 / P2 / P3 (Weeks 5–6)

| Module | Responsibility |
|---|---|
| `pipelines/base.py` | `Retriever` interface (§4.1); shared leakage-free prompt template. |
| `pipelines/vector/p1_vector.py` | One Chroma collection (`storage/chroma/`), metadata-tagged by `document_id`; `VectorIndexRetriever` → `FlagEmbeddingReranker` narrows to K; `where={"document_id": ...}` filter (§0.2). |
| `pipelines/keyword/tokenizer.py` | Custom regex tokenizer (§5, identical at index/query time). |
| `pipelines/keyword/p2_bm25.py` | One `BM25Okapi` corpus per `document_id`, cached to `storage/bm25/{document_id}.pkl`. |
| `pipelines/structural/p3_structural.py` | Loads the Phase 3 `SummaryIndex` for the query's `document_id`; retrieves via `as_retriever(retriever_mode="embedding")` (§5). |
| `pipelines/answerer.py` | Shared `Llama 3.3 70B` answerer (§4.1/§4.2) — citation-marker parsing lives here. |
| `loop_executor.py` | Orchestrator (§4.5a); resumes via `get_completed_keys` against the `UNIQUE` constraint in §3.2. |
| `tests/test_tokenizer_consistency.py` | Tokenizer is byte-identical at index/query time. |
| `tests/test_no_leakage.py` | Answerer prompt never contains exemplars/ground truth/citations beyond its own retrieved nodes. |

**Packages:** `llama-index-vector-stores-chroma`, `chromadb`, `llama-index-embeddings-huggingface`, `sentence-transformers`, `llama-index-postprocessor-flag-embedding-reranker`, `FlagEmbedding`, `rank_bm25`, `llama-index-llms-groq`.

---

### Phase 6 — Judge Build & Validation Gate (Weeks 6–7)

| Module | Responsibility |
|---|---|
| `judge/async_judge.py` | Quadrant-matched 5-exemplar prefix (§4.5b); no search tool. |
| `judge/metrics.py` | `citation_audit`, `token_f1`, `exact_match`, `precision_at_k`, `recall_at_k`, `evidence_hit_rate` (§4.1). |
| `judge/numeric_normalizer.py` | §4.3. |
| `judge/score_gate_outputs.py` | CLI: researcher hand-scores the 60 gate outputs. |
| `judge/validation_gate.py` | Orchestrates the gate (§4.5b); computes Agreement Rate; blocks Phase 7 below 80%. |

**Data flow:** writes `results.judge_score` / `.human_score` for the 60 `source_set='JEQ'` rows (§1 issue #1's resolution — **not** into `judge_validation`). **Packages:** none beyond Phases 1–5.

---

### Phase 7 — Full Benchmark Execution (Weeks 7–9, background, TPD-paced)

| Module | Responsibility |
|---|---|
| `run_benchmark.py` | Iterates the full 900-cell PQ matrix through `loop_executor.py`, then `async_judge.py` + `metrics.py`; safely re-invocable (manual or cron/`launchd`) across the multi-week window; always resumes via §3.2's `UNIQUE` key. |

**Packages:** none new — composition of Phase 5 + Phase 6 at full scale.

---

### Phase 8 — Results Consolidation & Analysis (Weeks 8–10)

| Module | Responsibility |
|---|---|
| `analysis/aggregate.py` | `results` ⋈ `queries` (for `quadrant`) into a `pandas` DataFrame; per-pipeline/per-K/per-quadrant aggregates. |
| `analysis/plots.py` | `matplotlib` charts → `analysis/figures/`. |
| `analysis/tables.py` | Summary tables → `analysis/tables/` (Markdown/CSV) for the write-up. |

**Packages:** `pandas`, `matplotlib`.

---

## 7. Out of Scope (Reserved, No Implementation)

P4 (Brute-Force Full-Context), P5 (Naive Vector RAG), P6 (Hybrid Fusion RAG) remain a documented deliberate-scoping narrative (`Project_Idea.md` §6), not build targets. No modules or packages exist for them. If pursued later, P5 reuses P1's embeddings, P6 reuses P1+P2, P4 needs no retrieval — none require new infrastructure.

---

## 8. Revised Timeline (10 Weeks)

The corpus growing from one filing to ~9 (§0.1) genuinely adds ingestion/parsing/audit work and more generation chunks to process, which the original 8-week, single-filing-shaped schedule didn't account for. The extra two weeks go there and into giving Phase 7's background run and Phase 8's analysis non-overlapping room, not into new scope.

| Phase | W1 | W2 | W3 | W4 | W5 | W6 | W7 | W8 | W9 | W10 |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 — Infra | ● | | | | | | | | | |
| 2 — Ingestion (6–9 filings) | ● | ● | ● | | | | | | | |
| 3 — P3 index build | | | ● | | | | | | | |
| 4 — Dataset gen & verification | | | | ● | ● | | | | | |
| 5 — Pipeline impl (P1/P2/P3) | | | | | ● | ● | | | | |
| 6 — Judge build & gate | | | | | | ● | ● | | | |
| 7 — Full benchmark (background) | | | | | | | ● | ● | ● | |
| 8 — Analysis | | | | | | | | ● | ● | ● |

The judge gate is now expected to pass around **Week 7** (was Week 5), so the background 900-run matrix occupies Weeks 7–9 (still the ~2–3-week TPD-bound window from `Budget.md` §2, just shifted right). Active build work (Phases 1–6) wraps by end of **Week 7**; Weeks 8–10 overlap analysis with the start of the dissertation write-up, mirroring the original plan's structure at the new scale.

This redistribution is also applied to `Phase Plan.md` (its week labels and intro framing are updated to match, so the two documents don't disagree), and the "8-week timeline" references in `Budget.md` §2 and `Project_Idea.md` §9 are updated to "10-week" for the same reason.

---

## 9. Proposed Repository Layout

```
new-project/
├── .env
├── requirements.txt
├── config.py
├── database_manager.py
├── groq_client.py
├── groq_limits.md
├── benchmark.db                      # nodes, queries, golden_queries, judge_validation, results
├── data/
│   ├── filings_manifest.json
│   ├── raw/
│   └── parsed/
├── storage/
│   ├── chroma/
│   ├── bm25/
│   └── summary_index/
├── logs/
│   └── index_build_costs.json
├── ingest/
│   ├── fetch_filings.py
│   ├── parse_filing.py
│   ├── node_builder.py
│   └── parsing_audit.py
├── dataset_gen/
│   ├── async_generator.py
│   ├── search_tool.py
│   ├── async_critic.py
│   ├── cross_check.py
│   ├── split_and_label.py
│   └── label_gq.py
├── pipelines/
│   ├── base.py
│   ├── answerer.py
│   ├── vector/p1_vector.py
│   ├── keyword/
│   │   ├── tokenizer.py
│   │   └── p2_bm25.py
│   └── structural/
│       ├── build_summary_index.py
│       └── p3_structural.py
├── loop_executor.py
├── judge/
│   ├── async_judge.py
│   ├── metrics.py
│   ├── numeric_normalizer.py
│   ├── score_gate_outputs.py
│   └── validation_gate.py
├── run_benchmark.py
├── analysis/
│   ├── aggregate.py
│   ├── plots.py
│   └── tables.py
└── tests/
    ├── test_groq_client_backoff.py
    ├── test_tokenizer_consistency.py
    └── test_no_leakage.py
```

---

## 10. Consolidated Dependency Manifest

```text
# --- Phase 1: infra ---
groq
tenacity
aiosqlite
python-dotenv
pytest
pytest-asyncio

# --- Phase 2: ingestion ---
llama-parse
llama-index-core
requests

# --- Phase 3 / Phase 5 (shared LLM binding) ---
llama-index-llms-groq

# --- Phase 5: P1 vector ---
llama-index-vector-stores-chroma
chromadb
llama-index-embeddings-huggingface
sentence-transformers
llama-index-postprocessor-flag-embedding-reranker
FlagEmbedding

# --- Phase 4 / Phase 5: P2 keyword ---
rank_bm25

# --- Phase 8: analysis ---
pandas
matplotlib
```

No new packages were needed for the §4 LLD additions (citation parsing, numeric normalization, JSON storage) — all are stdlib (`re`, `decimal`, `json`).

**Version-pin note (unchanged from v1):** LlamaIndex's current line is **0.14.x**, already past `Phase Plan.md`'s example pin of `0.10.x`. Re-verify and pin exact versions at Phase 1 implementation time against current docs, not the example string in the spec.

---

## 11. Open Items / Recommendations

1. **Regenerate `schemas/db_schema_example.jsonc`** from §3.2/§3.3 above — it still reflects the old 2-pipeline/600-row/12-JEQ design.
2. **Exact filing list** — §6 Phase 2's manifest needs the actual 2–3 tickers and 2–3 fiscal years before `data/filings_manifest.json` can be filled in. AAPL/MSFT/TSLA × FY2023–2025 is used above only as an illustrative example.
3. ~~`Guardrails.md` §6's wording is stale against §1 issue #1's fix~~ — **resolved**: `Guardrails.md` §6 has been reworded so its "mandatory schema" and `judge_validation` bullets now match this design exactly (`judge_validation` holds question fields only; the 60 gate outputs and their `human_score`/`judge_score` land on `results` tagged `source_set='JEQ'`).
4. **"Context mass held constant across pipelines" (`Project_Idea.md` §10, principle 1) is not mechanically enforced anywhere** — K is standardized as *node count*, not *token count*, and node sizes vary (a table node can be much longer than a text node), so two pipelines at the same K can still pass different token volumes to the answerer. Nothing in any spec doc specifies a token-budget truncation step to force exact equality. The recommendation here is to treat "same K" as the operational definition of "standardized context volume" and document the resulting token-volume variance as an accepted approximation (consistent with the project's existing "statistical honesty" framing elsewhere) rather than adding a truncation mechanism that no spec doc currently calls for. Flagged for the researcher to confirm or override.
5. **Per-filing query allocation isn't forced even** — Phase 4 accumulates 35/quadrant across the corpus, not a fixed number per filing. Left open deliberately, per the original v1 note.
