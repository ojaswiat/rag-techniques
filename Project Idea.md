### COMP702 M.Sc. Dissertation Project: Comprehensive Research Concept, Benchmarking Framework, and System Design

---

## 1. Research Overview and Core Objectives

The central objective of this research is to conduct an academically rigorous, multi-dimensional comparative performance analysis of various Retrieval-Augmented Generation (RAG) architectures when executed against highly complex, structurally dense financial data—specifically, United States SEC 10-K corporate filings.

The primary research question explores the performance boundaries, accuracy limits, and cost-efficiency trade-offs between standard **semantic retrieval (vector-based)** and **deterministic statistical retrieval (keyword-based)** models. By evaluating these paradigms across multi-layered data structures (narrative text vs. granular financial tables), this study establishes explicit boundaries regarding when vector embeddings fail, where keyword indices excel, and how structural tracking impacts financial document intelligence.

---

## 2. Data Strategy and Ingestion Parsing Architecture

Financial SEC 10-K filings present severe token, layout, and structural parsing obstacles. To eliminate noise and guarantee structural parity across all down-stream pipelines, the ingestion framework follows a strict structural mapping mechanism:

```text
+------------------------------------------------------------------------+
|                      RAW SEC 10-K FILING (PDF / HTML)                  |
+------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|           LLAMAPARSE ENGINE (Atomic Table Extraction Mode)             |
+------------------------------------------------------------------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+---------------------------------------+       +------------------------+
| Continuous Narrative Prose Paragraphs |       |  Tabular Data Blocks   |
| (Clean Markdown Strings)              |       | (Clean Markdown Tables)|
+---------------------------------------+       +------------------------+
            |                                               |
            +-----------------------+-----------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|          TEXTNODE ENRICHMENT LAYER (Metadata Injected Programmatically)|
|  - document_id      - parent_item_header (e.g., Item 1A, Item 8)       |
|  - source_page_num  - structural_node_type (Text vs Table)             |
+------------------------------------------------------------------------+
                                    |
                                    v
+------------------------------------------------------------------------+
|          PARSING VALIDATION GUARDRAIL (Randomized 20-Section Audit)    |
|  - Checks: Column truncation, table bisection, markdown rendering      |
+------------------------------------------------------------------------+

```

* **Atomic Table Preservation**: Standard token-count or paragraph-based splitting breaks row-and-column alignment, destroying cell relationships and rendering tabular financial analysis incoherent. This project mandates the use of **LlamaParse** configured explicitly for **atomic table extraction into clean Markdown syntax**.
* **Node Atomicity**: The parser is programmatically configured to treat each isolated table as an independent, indivisible `TextNode` or data structure. It is strictly prohibited to bisect or slice a Markdown table block during parsing.
* **Metadata Enrichment Layer**: Every processed node is enriched with structural context prior to indexing. This metadata dictionary binds parent section headers (e.g., *Item 1A: Risk Factors*, *Item 8: Financial Statements and Supplementary Data*) directly to downstream text snippets and markdown tables, ensuring structural lineage is preserved.
* **Structural Parsing Validation**: To maintain dataset integrity and avoid systemic failure, a manual parsing audit is carried out on a randomized sample of 20 distinct document sections. If table fragmentation, column truncation, or row misalignments are observed, parsing parameters are dynamically tuned or corrupted files are discarded to ensure a pristine text/tabular data baseline.

---

## 3. The 100-Query Benchmark Dataset: The Four Quadrants

To expose the specific vulnerabilities and architectural strengths of each pipeline, evaluation is performed against a stratified test bed of **100 queries** (25 queries uniformly distributed across four distinct operational quadrants). This count is deliberately scoped to a solo 8-week dissertation timeline: it is large enough to expose per-quadrant performance differences while keeping the total run matrix (see Section 9) within free-tier API rate limits and a near-zero budget.

```text
                           TEXT-HEAVY CONTEXT             TABLE-HEAVY CONTEXT
                    +------------------------------+------------------------------+
                    |                              |                              |
  DIRECT /          |              Q1              |              Q3              |
  EXPLICIT          |         Direct Text          |         Direct Table         |
  RETRIEVAL         |       (Fact Retrieval)       |     (Cell/Value Extraction)  |
                    |                              |                              |
                    +------------------------------+------------------------------+
                    |                              |                              |
  IMPLICIT /        |              Q2              |              Q4              |
  SYNTHESIS         |        Implicit Text         |        Implicit Table        |
  RETRIEVAL         |    (Multi-Hop Inference)     |   (Cross-Row/Footnote Calc)  |
                    |                              |                              |
                    +------------------------------+------------------------------+

```

* **Q1: Direct Text Queries (25 Queries)**: Evaluates fact-retrieval performance within dense, continuous prose (e.g., extracting specific, explicitly stated legal liabilities or corporate risk disclosures).
* **Q2: Implicit Text Queries (25 Queries)**: Evaluates thematic understanding and synthesis across disparate narrative pages (e.g., identifying and cross-referencing management's overall multi-paragraph strategic outlook within the MD&A section).
* **Q3: Direct Table Queries (25 Queries)**: Evaluates strict lookup and cellular extraction capabilities from tabular formats (e.g., pulling exact revenue figures, cash balance items, or capital expenditure rows from balance sheets).
* **Q4: Implicit Table Queries (25 Queries)**: Evaluates advanced math-inference, comparative logic, and cell-to-footnote synthesis (e.g., verifying multi-year changes in segment revenue or recalculating values that require cross-referencing row calculations with appended textual footnotes).

### Dataset Controls and Meta-Tagging

Every query generated within this system is stored as a deterministic JSON object containing explicit ground-truth mappings:

```json
{
  "query_id": "Q4_087",
  "quadrant": "Implicit_Table",
  "query_text": "Using the operating expense breakdown in the income statement (page 62), calculate the year-over-year percentage change in total operating expenses for FY2025, then adjust the result for the restructuring asset impairment disclosed in the footnotes on page 74.",
  "ground_truth_answer": "Operating expenses decreased by 4.2% YoY. Factoring in the $15M impairment, normalized expenses rose 1.1%.",
  "evidence_pages": [62, 74],
  "document_id": "SEC_10K_XYZ_CORP_2025"
}

```

---

## 4. Open-Model Generation and Adversarial Verification Architecture

To eliminate the bottleneck of manually verifying 100 ground-truth queries while remaining academically rigorous, the system leverages **open-source instruction models served on Groq's free tier** (no credit card; rate-limited rather than billed). Because open models cap at a ~128K-token context window — far short of an entire SEC 10-K — generation operates on a **per-section (chunked) basis** rather than ingesting the whole filing at once. Each section (e.g., *Item 1A*, *Item 7 MD&A*, *Item 8 Financial Statements*) is fed to the generator independently, with its source page range tracked, so the model always reasons over a context that fits comfortably in-window.

Crucially, the Generator and Critic use **different model families** to break the circular-validation loop: agreement between two independent architectures is far stronger evidence of a query's soundness than agreement within one family.

```text
       +-------------------------------------------------------------+
       |        SEC 10-K SPLIT INTO PER-SECTION CHUNKS (<128K)        |
       +-------------------------------------------------------------+
                                      |
                                      v
                       +------------------------------+
                       |   Generator Agent            |
                       |   (Llama 3.3 70B - Groq)     |
                       |   Creates: Query & Page GT   |
                       +------------------------------+
                                      |
                                      | (Hide Answer & Pages From Critic)
                                      v
                       +------------------------------+
                       |   Critic Agent               |
                       |   (Qwen3 32B - Groq)         |
                       |   Independent Doc Search     |
                       +------------------------------+
                                      |
                                      v
                       +------------------------------+
                       |    Automated Cross-Check     |
                       |      Page Match Check        |
                       +------------------------------+
                                  /        \
                           (Yes) /          \ (No)
                                v            v
                +-------------------+    +-------------------+
                |   Auto-Verified   |    |      Discard      |
                |  100-Query Pool   |    |   & Regenerate    |
                +-------------------+    +-------------------+

```

### Step 1: Per-Section Ground-Truth Synthesis (The Generator Agent)

Because open models cannot ingest an entire 10-K at once, generation is scoped to one document section at a time, preserving each chunk's page range for ground-truth tracking.

* A Python execution script targets the Groq API using **Llama 3.3 70B** to read one parsed section at a time.
* The model is prompted to output complex questions for the relevant quadrant(s) that section can support, along with the exact `evidence_pages` and the detailed `ground_truth_answer` directly sourced from the material.
* Questions are accumulated across sections until each quadrant reaches its target of 25 verified queries.

### Step 2: Multi-Agent Adversarial Quality Control (The Critic Agent)

To certify that these 100 generated questions are completely unambiguous and factually sound without manual human intervention, the dataset is passed through a decoupled, multi-agent adversarial loop. The Critic runs on **Qwen3 32B** — a deliberately different model family from the Llama-based Generator — so that agreement reflects cross-architecture consensus rather than a single model agreeing with itself:

1. **The Blind Test**: A separate, decoupled "Critic Agent" prompt receives *only* the `query_text` generated in Step 1. The ground-truth page numbers and target answers are completely redacted and hidden from it.
2. **Contextual Search Challenge**: The Critic Agent is given access to the raw parsed document text blocks. It must independently scan the text, locate the correct answer, and state the exact source page numbers based purely on the text.
3. **Automated Cross-Check**: A deterministic code layer cross-references the Critic's results with the Generator's ground truth.
* If both independent models agree on the exact page numbers and numerical values, the query is automatically stamped as **"Auto-Verified"** and admitted to the benchmark.
* If there is a mismatch (indicating the question was vague, poorly phrased, or hallucinated), the query is automatically discarded, and the Generator script runs an iteration loop to replace it.



---

## 5. The Human Anchor: Golden Subset Calibration and Few-Shot Prompting System

To anchor this automated evaluation pipeline, a high-quality human verification step is layered over a small subset to dictate standard behaviors to the downstream evaluation engine.

```text
           +---------------------------------------------+
           |        100 Auto-Verified Query Pool         |
           +---------------------------------------------+
                                  |
                                  v  (Extract 3 per Quadrant)
           +---------------------------------------------+
           |         Golden Subset (12 Queries)          |
           +---------------------------------------------+
                                  |
                                  v  (Manual Human Analysis)
           +---------------------------------------------+
           |    Human Evaluation & Expert Labeling       |
           |  - Document Output Analysis                 |
           |  - Scoring on a 1-10 Rubric Scale           |
           |  - Detailed Human Explanatory Reasoning     |
           +---------------------------------------------+
                                  |
                                  v  (Inject as Dynamic Few-Shot Data)
           +---------------------------------------------+
           |      Primary LLM-as-a-Judge System          |
           |  - Fixed Instruction Rubrics                |
           |  - 3 In-Context Examples per Quadrant (1-10)|
           +---------------------------------------------+

```

### Step 1: Golden Subset Selection and Human Labeling

Out of the 100 auto-verified queries, a subset of **12 queries** (exactly 3 per quadrant) is extracted to serve as the **Golden Subset**. The researcher manually reviews these 12 queries and their system outputs, providing expert labeling.

### Step 2: Meta-Prompt Construction

For each query in the Golden Subset, the researcher compiles an array containing:

* The original input query and quadrant categorization.
* The generated output response from a test run.
* A human-assigned quality score on a **1-to-10 scale**.
* A granular text justification explaining *why* the human assigned that score against the rubric.

### Step 3: Few-Shot In-Context Learning Engine

These 12 comprehensive human evaluations are embedded into the system prompt of the primary LLM-as-a-Judge model as structured few-shot examples (dynamically filtered by quadrant — see below). This provides the Judge LLM with a clear understanding of the difference between an acceptable and an exceptional response. This approach bypasses the need for model fine-tuning, which risks introducing black-box evaluation biases.

### Gold Standard Queries Usage and Dynamic Few-Shot Rerouting

The 12 human-verified "Gold Standard" queries are managed programmatically via relational database isolation and conditional in-context routing. Although the run volume is modest, dynamic filtering keeps each Judge prompt tightly relevant to the quadrant being graded and avoids diluting the context with mismatched examples.

Inserting all 12 detailed human-labeled examples (each including the query, ground-truth text, pipeline output, 1–10 score, and qualitative reasoning) into every prompt would mix table-grading and text-grading exemplars indiscriminately. Instead of a single static block, the system implements a **Dynamic Few-Shot Rerouting** mechanism that injects only the 3 examples matching the current query's quadrant.

```text
                      DYNAMIC FEW-SHOT REROUTING SYSTEM
                      
                       +--------------------------------+
                       |   Central SQLite Database      |
                       |   - Table: queries             |
                       |   - 100 Verified Rows          |
                       |   - 12 Tagged "is_golden = 1"  |
                       +--------------------------------+
                                       |
                                       | (Pipeline Output Delivered)
                                       v
                       +--------------------------------+
                       |    Active Evaluation Worker    |
                       |    Identifies Target Row       |
                       |    e.g., Quadrant = Q4_Table   |
                       +--------------------------------+
                                       |
                                       v
                       +--------------------------------+
                       |      SQL Conditional Query     |
                       | SELECT * FROM queries WHERE    |
                       | is_golden=1 AND quadrant='Q4'  |
                       +--------------------------------+
                                       |
                                       | (Extracts EXACTLY 3 Rows, Drops 9)
                                       v
                       +--------------------------------+
                       |   Dynamic Prompt Assembler     |
                       | - General Scoring Rubrics      |
                       | - 3 Context-Relevant Examples  |
                       +--------------------------------+
                                       |
                                       v
                       +--------------------------------+
                       |     LLM-as-a-Judge Engine      |
                       |   (Llama 3.3 70B - Groq)       |
                       +--------------------------------+

```

#### 1. Relational Database Seeding

All 100 auto-verified queries are written directly to a local SQLite database table named `queries`. A dedicated Boolean column named `is_golden` is assigned to every row.

* The 88 unverified baseline testing queries are marked with `is_golden = 0`.
* The 12 highly vetted, human-scored, and reasoned baseline queries are marked with `is_golden = 1`.

#### 2. Runtime Context Filtering

During the evaluation phase, the loop execution script processes the 600 pipeline generation outputs row by row. Before sending an output text block to the Judge LLM (Llama 3.3 70B on Groq), the evaluation worker checks the target query's `quadrant` attribute (e.g., `Q1_Direct_Text`, `Q4_Implicit_Table`).

The script executes a localized SQL query to retrieve *only* the golden subset rows matching that specific quadrant context:

```sql
SELECT query_text, true_answer, pipeline_output, human_score, human_reasoning 
FROM queries 
WHERE is_golden = 1 AND quadrant = :current_pipeline_quadrant;

```

#### 3. Token Payload Reduction and Cost Optimization

By shifting from a static 12-example prompt to this dynamic 3-example filter, each Judge call carries only quadrant-relevant exemplars, reducing per-call payload by roughly 75% while improving grading relevance.

```text
+-------------------------------------------------------------------------+
|                          TOKEN PAYLOAD COMPARISON                       |
+-------------------------------------------------------------------------+
| [Static Payload Attempt]                                                |
| 12 Examples x ~500 Tokens/Example = 6,000 Input Tokens                  |
| 6,000 Tokens x 600 Evaluation Runs = 3,600,000 Total Tokens             |
|                                                                         |
| [Dynamic Rerouting Execution]                                           |
| 3 Contextual Examples x ~500 Tokens = 1,500 Input Tokens                |
| 1,500 Tokens x 600 Evaluation Runs = 900,000 Total Tokens               |
+-------------------------------------------------------------------------+
| TOTAL RESOURCE CONSERVATION = 2,700,000 TOKENS SAVED                    |
+-------------------------------------------------------------------------+

```

This keeps token throughput well within Groq's free-tier per-day limits while ensuring the Judge LLM receives highly relevant in-context examples tailored to the specific text or tabular structure it is currently grading.

---

## 6. Multi-Pipeline Architectural Registry

This project focuses on **two core production architectures** (Pipelines 3 and 4), which form a clean, directly comparable head-to-head between optimized semantic retrieval and statistical keyword retrieval. Four further pipelines are documented as deprioritized, excluded, or reserved — each with an explicit engineering justification — to demonstrate deliberate scoping and preserve a clear future-work narrative.

```text
                  +---------------------------------------+
                  |       RESEARCH PIPELINE REGISTRY      |
                  +---------------------------------------+
                                      |
         +----------------------------+----------------------------+
         |                                                         |
         v                                                         v
+---------------------------------------+         +---------------------------------------+
|          ACTIVE CODESPACE             |         |         DEPRIORITIZED / SCOPE         |
+---------------------------------------+         +---------------------------------------+
| Pipeline 3: Optimized Vector RAG      |         | Pipeline 1: Brute-Force Context       |
|             (Metadata + Re-ranker)    |         |             [DEPRIORITIZED]           |
| Pipeline 4: Vectorless Keyword RAG    |         | Pipeline 2: Naive Vector RAG          |
|             (True BM25 / rank_bm25)   |         |             [DEPRIORITIZED]           |
+---------------------------------------+         |                                       |
                                                  | Pipeline 5: Vectorless Structural RAG |
                                                  |             (SummaryIndex) [EXCLUDED] |
                                                  |                                       |
                                                  | Pipeline 6: Hybrid RAG (Fusion)       |
                                                  |             [RESERVED FUTURE WORK]    |
                                                  +---------------------------------------+

```

### Active Pipelines

* **Pipeline 3: Optimized Vector RAG**
* *Architecture*: A semantic retrieval pipeline with two-layer optimization: (a) hard metadata pre-filtering using structural header parameters extracted during ingestion parsing, and (b) a downstream cross-encoder **Re-ranker** (`BAAI/bge-reranker-base`, run locally on CPU at zero API cost) to re-order the top-$K$ candidates before passing them to the generation engine. Embeddings are generated locally with `BAAI/bge-small-en-v1.5`.
* *Purpose*: Measures whether tuned semantic search — metadata-aware retrieval plus re-ranking — can be made competitive for complex financial lookups against dense tabular data.


* **Pipeline 4: Vectorless Keyword RAG (True BM25)**
* *Architecture*: Implemented via the **`rank_bm25`** library, applying the statistical **Okapi BM25 algorithm** directly over tokenized document nodes. It completely bypasses dense vector space creation and geometric similarity. Retrieval is deterministic, reproducible, and requires no LLM call or API at the retrieval step.
* *Purpose*: Serves as the primary alternative architecture, evaluating whether strict, frequency-based statistical keyword matching outperforms high-dimensional embeddings when seeking explicit numerical coordinates or narrow tabular data.
* *Design note*: An earlier draft specified LlamaIndex's `KeywordTableIndex` for this role. That index was rejected because it uses an **LLM to extract keywords** at index/query time — it is neither statistical nor deterministic, adds per-node API cost and latency, and would not constitute a clean test of the BM25 paradigm the research question targets. `rank_bm25` is the correct instrument for a genuine semantic-vs-statistical comparison.



### Deprioritized, Excluded, and Reserved Pipelines

* **Pipeline 1: Brute-Force Context (Baseline) — [DEPRIORITIZED]**
* *Architecture*: Zero retrieval layer; the entire parsed document is injected directly into the LLM context window.
* *Justification for Deprioritization*: With open models capped at ~128K tokens, full 10-K injection is infeasible for anything but the shortest filings, and it tests generation-ceiling behavior rather than the retrieval question at the heart of this study. **It can be pursued later if time allows** as a context-ceiling reference point on short filings.


* **Pipeline 2: Naive Vector RAG — [DEPRIORITIZED]**
* *Architecture*: Flat embedding space (`BAAI/bge-small-en-v1.5`) with top-$K$ cosine similarity and no metadata filtering or re-ranking.
* *Justification for Deprioritization*: It is the un-optimized ablation of Pipeline 3. The core research question — semantic vs. statistical retrieval — is most sharply tested by comparing the *best* vector pipeline (3) against BM25 (4). **It can be pursued later if time allows**, as an ablation isolating how much the metadata + re-ranker layers in Pipeline 3 actually contribute.


* **Pipeline 5: Vectorless Structural RAG (SummaryIndex) — [EXCLUDED]**
* *Architecture*: Designed to execute retrieval by traversing an abstract, hierarchical tree structure built from parent summaries and child-node descriptions using LlamaIndex `SummaryIndex`.
* *Justification for Exclusion*: Highly vulnerable to **table fragmentation**. During the automated construction of hierarchical summaries, abstract summary generators routinely drop cell ranges, numeric footnotes, and narrow row variables. Building a custom parser capable of maintaining table integrity introduces high software-engineering overhead that would detract from the core comparative analysis.


* **Pipeline 6: Hybrid RAG (The Fusion Pipeline) — [RESERVED / FUTURE SCOPE]**
* *Architecture*: A serial/parallel composite system that first routes queries through the deterministic BM25 keyword engine (Pipeline 4) to narrow down the target context space, followed by an optimized vector embedding search (Pipeline 3) within that restricted subset.
* *Justification for Reservation*: High risk of **cascading routing degradation**. Stacking two distinct error vectors introduces substantial operational complexity. If the initial BM25 statistical filter improperly excludes a relevant section due to minor semantic phrasing differences, the downstream vector engine will search an incorrect subset, causing a fatal error. To protect research validity, this architecture is excluded from core benchmarking and reserved strictly as an optional extension if core data collection concludes ahead of schedule.



---

## 7. Tri-Pillar Evaluation and Benchmarking Framework

Pipelines are comprehensively audited and compared across three independent variables to create a complete operational profile. To evaluate retrieval performance across different operational constraints, both active retrieval pipelines (Pipelines 3 and 4) are tested using **three distinct values of $K$**:

$$\mathbf{K \in \{3, 5, 10\}}$$

```text
                               +----------------------------------------+
                               |     TRI-PILLAR SYSTEM EVALUATION       |
                               +----------------------------------------+
                                                   |
         +-----------------------------------------+-----------------------------------------+
         |                                         |                                         |
         v                                         v                                         v
+--------------------------------+       +--------------------------------+       +--------------------------------+
|      RETRIEVAL PARITY LAYER    |       |     ANSWER QUALITY LAYER       |       |       EFFICIENCY LAYER         |
+--------------------------------+       +--------------------------------+       +--------------------------------+
|  Executes across:              |       |  - Exact Match (EM) Text check |       |  - Query Latency Time (Seconds)|
|  - K = 3 Retrieved Nodes       |       |  - Token-Level F1 Calculation  |       |  - In/Out Token Vol Tracking   |
|  - K = 5 Retrieved Nodes       |       |  - LLM-as-a-Judge 1-10 Rubric  |       |  - Real Financial Cost Mapping |
|  - K = 10 Retrieved Nodes      |       |  - Citation Audit Layer        |       |  - One-time Index Building     |
|  Calculates:                   |       |  - Golden Agreement Rate Check |       |    Computational Cost          |
|  - Precision @ K               |       +--------------------------------+       +--------------------------------+
|  - Recall @ K                  |
|  - Evidence-Page Hit Rate      |
+--------------------------------+

```

### Pillar 1: Retrieval Evaluation Metrics

These metrics isolate the performance of the information retrieval component, measuring the pipeline's ability to feed the correct document nodes to the LLM generation layer:

* **Precision@K**: Measures context density by tracking the ratio of retrieved nodes within the top-$K$ slot that match the ground-truth evidence pages.

$$\text{Precision}@K = \frac{|\{\text{Retrieved Nodes up to } K\} \cap \{\text{Ground Truth Pages}\}|}{K}$$


* **Recall@K**: Measures context comprehensiveness by tracking the ratio of true ground-truth pages successfully caught within the top-$K$ slot.

$$\text{Recall}@K = \frac{|\{\text{Retrieved Nodes up to } K\} \cap \{\text{Ground Truth Pages}\}|}{|\{\text{Ground Truth Pages}\}|}$$


* **Evidence-Page Hit Rate**: A binary flag (1 or 0) tracking if the single critical page needed to answer the query is present anywhere in the retrieved bundle.

### Pillar 2: Answer Quality and Generation Evaluation Metrics

This pillar measures the semantic and lexical precision of the output generated by the downstream LLM:

* **Lexical Metrics (Exact Match and Token F1-Score)**: Evaluates lexical overlap and string similarity between the generated response text and the ground-truth target text.
* **Automated LLM-as-a-Judge Prompt Matrix**: Evaluates the text block across a **1-to-10 scoring rubric** embedded with the dynamically-filtered few-shot examples from Section 5.
* **Citation Audit Layer**: The judge LLM cross-references the page numbers cited in the generated answer text against the true `evidence_pages` JSON metadata element. If a pipeline outputs a correct numeric answer but cites an incorrect source page, the system flags it as a *coincidental hallucination* and downgrades its score.
* **The Agreement-Rate Guardrail**: To mathematically justify the automated evaluation of the 88 non-golden queries, the system runs the Judge LLM against the 12 human-labeled Golden Subset queries and computes the **LLM-Judge Agreement Rate**:

$$\text{Agreement Rate} = \frac{\text{Matches between Human Score and Judge Score}}{\text{Total Samples within Golden Subset}} \times 100\%$$



The system prompt parameters must be tuned until the Agreement Rate is stable at **$>80\%$** before running the full evaluation loop.

### Pillar 3: Efficiency, Cost, and Latency Evaluation Metrics

This pillar captures the production viability and engineering trade-offs of each system architecture:

* **Latency per Query**: Time elapsed (in seconds) from initial query submission to final token generation.
* **Token Consumption & Financial Cost per Query**: Tracking input/output token volume per query to map the operational cost curve of each pipeline across document scales.
* **One-Time Indexing Cost**: Benchmarking the computational overhead, time duration, and (where applicable) token cost required to build a local vector embedding space vs. a `rank_bm25` statistical index.

---

## 8. Complete Pipeline Structure (Bird's Eye View)
```
                                   +---------------------------------------+
                                   |       1. INGESTION & PARSING          |
                                   |  - llama_parser.py (Atomic Markdown)  |
                                   |  - database_manager.py (SQLite Init)  |
                                   +---------------------------------------+
                                                        |
                                                        v
                                   +---------------------------------------+
                                   |  2. DATASET SYNTHESIS (Groq Open LLMs)|
                                   |  - async_generator.py (Llama 3.3 70B) |
                                   |  - async_critic.py    (Qwen3 32B)     |
                                   +---------------------------------------+
                                                        |
                                                        v
                                   +---------------------------------------+
                                   |       3. CENTRAL SQLITE DATABASE      |
                                   |  - Tables: nodes, queries, results    |
                                   +---------------------------------------+
                                         /                         \
                                        /                           \
                                       v                             v
+--------------------------------------------+         +--------------------------------------------+
|         4A. VECTOR RETRIEVAL STACK         |         |        4B. KEYWORD RETRIEVAL STACK         |
|  - optimized_vector_pipeline.py            |         |  - bm25_keyword_pipeline.py                |
|    (bge embeddings, local; metadata        |         |    (rank_bm25 - true statistical BM25)     |
|     pre-filter + bge-reranker, local CPU)  |         |                                            |
+--------------------------------------------+         +--------------------------------------------+
                                       \                             /
                                        \                           /
                                         v                         v
                                   +---------------------------------------+
                                   |     5. ASYNC PIPELINE RUNNER          |
                                   |  - loop_executor.py                   |
                                   |  - Iterates K over [3, 5, 10]         |
                                   +---------------------------------------+
                                                        |
                                                        v
                                   +---------------------------------------+
                                   |         6. METRICS & JUDGE            |
                                   |  - code_metrics.py (P@K, R@K, Hit)    |
                                   |  - async_judge.py (Llama 3.3 70B)     |
                                   |    (Few-Shot Prompt + Citation Audit) |
                                   +---------------------------------------+
```
---

## 9. Limitations and Caveats

### Combinatorial Scale and Execution Overhead

The architectural design introduces a bounded execution matrix. Evaluating 100 unique queries across two pipelines and three values of $K$ produces a run count that is large enough for meaningful per-quadrant analysis yet small enough to complete comfortably within free-tier rate limits.

```text
+-----------------------------------------------------------------------+
|                        COMBINATORIAL SCALE MATH                       |
+-----------------------------------------------------------------------+
|  100 Evaluation Queries (25 per Quadrant)                             |
|                                                                       |
|  [Active Retrieval Pipelines]                                         |
|  - Pipeline 3: Optimized Vector                                       |
|  - Pipeline 4: True BM25 Keyword                                      |
|  (Each runs at K = 3, 5, 10)                                          |
|                                                                       |
|  2 Pipelines x 3 K-Values = 6                                         |
|  6 x 100 Queries = 600 runs                                           |
+-----------------------------------------------------------------------+
|                 TOTAL PIPELINE GENERATIONS = 600 RUNS                 |
|                 TOTAL JUDGE EVALUATIONS    = 600 RUNS                 |
+-----------------------------------------------------------------------+

```

* **Query Count Baseline:** A pool of 100 verified questions (25 evenly distributed across the 4 core quadrants) balances statistical signal against a solo 8-week timeline. Larger pools (e.g., 400) add little per-quadrant insight at this scope while multiplying API load.
* **Run Count Multiplier:** Running 2 retrieval pipelines across 3 values of $K$ ($K \in \{3, 5, 10\}$) produces 600 generation runs.
* **Evaluation Volume:** Each of the 600 generated answers is checked once by the Judge, creating an additional **600 evaluation runs**.

---

### The Necessity of Asynchronous Batch Processing

Executing 600 pipeline generation runs and 600 evaluation steps using standard, single-threaded Python synchronous `for` loops is slow and fragile — at ~2s of network wait per call, a single pipeline's loop can stall for long stretches and is prone to connection drops over a long run.

```text
[Synchronous Process] (Fatal Timeout Risk)
Run 1 ----> Wait for API (2s) ----> Run 2 ----> Wait for API (2s) [Total: ~4+ Hours per pipeline]

[Asynchronous Batch Processing] (Required Production Design)
Run 1 ---\
Run 2 -----+---> Async IO Loop Queue ---> Concurrent Groq API Engine [Total: Minutes per pipeline]
Run 3 ---/

```

* **Network Timeout Defenses:** Standard synchronous network calls frequently experience connection drops or socket timeouts over large datasets, which can stall scripts and lead to data losses.
* **Concurrent Resource Maximization:** The system must utilize asynchronous worker pools (`asyncio`, `aiohttp`, or native SDK Async clients). Grouping tasks into concurrent batches allows multiple inputs to hit the cloud APIs simultaneously, drastically reducing data ingestion time from hours down to minutes.

---

### Groq Free-Tier Rate Limits

Operating on Groq's free tier (no credit card; rate-limited rather than billed) exposes the architecture to throughput limits rather than a spend ceiling.

* **Per-Model Daily Caps:** Free-tier limits are per-model and per-organization. As of mid-2026, `llama-3.3-70b-versatile` is published at roughly 30 RPM and ~1,000 requests/day, with smaller models (e.g. `llama-3.1-8b-instant`) allowing far more. The full project — 100 generation + 100 critique + 600 evaluation calls plus regeneration overhead — sits within a few days of free-tier headroom even without optimization, and caching reduces this further.
* **HTTP 429 Rate Limiting:** Concurrent batching can exceed per-minute (RPM/TPM) quotas, triggering HTTP 429 exceptions. The asynchronous framework must wrap all calls in a resilience handler (e.g., the `tenacity` library) applying **exponential backoff and jitter**, so the script pauses and retries smoothly instead of crashing.
* **No Budget-Exhaustion Risk:** Because retrieval (bge embeddings, bge reranker, BM25) runs locally on CPU at $0 and all LLM calls use the free tier, there is no per-token billing to exhaust. The binding constraint is daily request count, not dollars.

---

### Software Stack Version Instability (LlamaIndex Drift)

Data framework orchestration tools (specifically LlamaIndex) undergo rapid development and frequent breaking syntax changes.

* **Syntax Degradation:** Standard model coding tools often reference older, deprecated library models and methods. If code generation isn't strictly controlled, it can result in broken implementations of key structures like vector index configurations or retriever interfaces.
* **Mitigation Strategy:** Code requirements must pin exact version dependencies (e.g., `llama-index==0.10.x`, `rank-bm25` at a fixed version). Current framework documentation snippets should be directly provided to your programming assistant to prevent it from inventing non-existent parameters.

---

### Relational Data Management Overload

Generating 600 distinct data points across two pipelines, tracking varying parameters of $K$, and recording latency, costs, and output text strings will quickly become unmanageable if stored in loose CSV or JSON flat files.

* **File Corruption Vulnerability:** Appending raw strings to loose files mid-loop often breaks file structures during unexpected script crashes, corrupting previously harvested data.
* **Relational Enforcement Layer:** A local **SQLite database schema** is required from day one. Pipelines must commit results immediately to strongly isolated tables (`nodes`, `queries`, `results`), ensuring that if a process crashes partway through, the data from completed runs remains safely preserved and queryable, and the worker can resume from the last written row.

---

### Coincidental Correctness and Citation Blindspots

A significant algorithmic vulnerability in RAG systems is "coincidental correctness," where an engine outputs a factually accurate answer by pulling data from a completely irrelevant page.

```text
                      COINCIDENTAL CORRECTNESS TRAP
                      
   Target Query: "What was the FY2025 R&D spend?" [True Value: $150M on Page 45]
   
   [Faulty Pipeline Retrieval Component] ---> Pulls Page 12 (An unrelated marketing table)
                                               Page 12 happens to list a $150M lease expense.
                                               
   [Downstream Generation LLM Component] ---> Reads Page 12, extracts "$150M".
   
   Result: Answer looks 100% correct to standard Token F1 / Exact Match string evaluation, 
           but the retrieval step was a complete failure.

```

* **Evaluation Bias:** Relying entirely on simple text-string comparisons (like Token F1 or Exact Match) will make flawed retrieval components look artificially successful.
* **Mitigation Requirement:** The Judge system must enforce a strict **Citation Audit layer**. It must check whether the page numbers cited in the generated answer match the true `evidence_pages` stored in the query's ground-truth metadata. If there is a page mismatch, the score must be programmatically downgraded to expose the faulty retrieval step.
---

## 10. Academic Rigor and Methodological Principles

To ensure this dissertation withstands rigorous academic evaluation, the following architectural principles are enforced:

1. **Standardized Context Volumes**: To guarantee parity between Pipeline 3 and Pipeline 4, the total context mass (token volume passed to the generation LLM) is kept constant across evaluations at each value of $K$.
2. **Explicit Citation Enforcement**: RAG prompt configurations explicitly mandate that the generating model provide source-page attributions. This allows the evaluation framework to flag instances of coincidental correctness, where the correct answer was generated from irrelevant or incorrect context.
3. **Methodological Transparency**: The methodology chapter documents all six originally-scoped architectural iterations and gives formal, engineering-based justifications for deprioritizing the two baseline pipelines (1 and 2), excluding the SummaryIndex architecture (5), and reserving the Hybrid model (6) — establishing a clear narrative of deliberate project scoping around the core semantic-vs-statistical comparison.