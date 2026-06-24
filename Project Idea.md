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

## 3. The 400-Query Benchmark Dataset: The Four Quadrants

To expose the specific vulnerabilities and architectural strengths of each pipeline, evaluation is performed against a stratified test bed of **400 queries** (100 queries uniformly distributed across four distinct operational quadrants):

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

* **Q1: Direct Text Queries (100 Queries)**: Evaluates fact-retrieval performance within dense, continuous prose (e.g., extracting specific, explicitly stated legal liabilities or corporate risk disclosures).
* **Q2: Implicit Text Queries (100 Queries)**: Evaluates thematic understanding and synthesis across disparate narrative pages (e.g., identifying and cross-referencing management's overall multi-paragraph strategic outlook within the MD&A section).
* **Q3: Direct Table Queries (100 Queries)**: Evaluates strict lookup and cellular extraction capabilities from tabular formats (e.g., pulling exact revenue figures, cash balance items, or capital expenditure rows from balance sheets).
* **Q4: Implicit Table Queries (100 Queries)**: Evaluates advanced math-inference, comparative logic, and cell-to-footnote synthesis (e.g., verifying multi-year changes in segment revenue or recalculating values that require cross-referencing row calculations with appended textual footnotes).

### Dataset Controls and Meta-Tagging

Every query generated within this system is stored as a deterministic JSON object containing explicit ground-truth mappings:

```json
{
  "query_id": "Q4_087",
  "quadrant": "Implicit_Table",
  "query_text": "Calculate the year-over-year percentage change in total operating expenses for FY2025, taking into account the restructuring asset impairment notes on page 74.",
  "ground_truth_answer": "Operating expenses decreased by 4.2% YoY. Factoring in the $15M impairment, normalized expenses rose 1.1%.",
  "evidence_pages": [62, 74],
  "document_id": "SEC_10K_XYZ_CORP_2025"
}

```

---

## 4. Vertex AI Generation and Adversarial Verification Architecture

To eliminate the bottleneck of manually verifying 400 ground-truth queries while remaining academically rigorous, the system leverages **Google Vertex AI** capabilities utilizing **Gemini 1.5 Pro**. This capitalizes on an ultra-long context window (2 million tokens) to bypass human scaling limitations while programmatically breaking the "circular validation loop".

```text
       +-------------------------------------------------------------+
       |                 Vertex AI (Gemini 1.5 Pro)                  |
       |                     Full 10-K Ingestion                     |
       +-------------------------------------------------------------+
                                      |
                                      v
                       +------------------------------+
                       |       Generator Agent        |
                       |  Creates: Query & Page GT    |
                       +------------------------------+
                                      |
                                      | (Hide Answer & Pages From Critic)
                                      v
                       +------------------------------+
                       |         Critic Agent         |
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
                |  400-Query Pool   |    |   & Regenerate    |
                +-------------------+    +-------------------+

```

### Step 1: Long-Context Ground-Truth Synthesis (The Generator Agent)

Because Gemini 1.5 Pro can ingest the entire SEC 10-K document simultaneously, it has a holistic structural overview that a chunked RAG pipeline lacks.

* A Python execution script targets the Vertex AI API using Gemini 1.5 Pro to ingest the entire un-chunked document text.
* The model is prompted to output exactly 100 highly complex questions per quadrant, along with the exact `evidence_pages` and the detailed `ground_truth_answer` directly sourced from the material.

### Step 2: Multi-Agent Adversarial Quality Control (The Critic Agent)

To certify that these 400 generated questions are completely unambiguous and factually sound without manual human intervention, you pass the dataset through a decoupled, multi-agent adversarial loop within Vertex AI:

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
           |        400 Auto-Verified Query Pool         |
           +---------------------------------------------+
                                  |
                                  v  (Extract 10 per Quadrant)
           +---------------------------------------------+
           |         Golden Subset (40 Queries)          |
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
                                  v  (Inject as Static Few-Shot Data)
           +---------------------------------------------+
           |      Primary LLM-as-a-Judge System          |
           |  - Fixed Instruction Rubrics                |
           |  - 40 In-Context Learning Examples (1-10)   |
           +---------------------------------------------+

```

### Step 1: Golden Subset Selection and Human Labeling

Out of the 400 auto-verified queries, a subset of **40 queries** (exactly 10 per quadrant) is extracted to serve as the **Golden Subset**. The researcher manually reviews these 40 queries and their system outputs, providing expert labeling.

### Step 2: Meta-Prompt Construction

For each query in the Golden Subset, the researcher compiles an array containing:

* The original input query and quadrant categorization.
* The generated output response from a test run.
* A human-assigned quality score on a **1-to-10 scale**.
* A granular text justification explaining *why* the human assigned that score against the rubric.

### Step 3: Few-Shot In-Context Learning Engine

These 40 comprehensive human evaluations are embedded directly into the static system prompt of the primary LLM-as-a-Judge model as structured few-shot examples. This provides the Judge LLM with a clear understanding of the difference between an acceptable and an exceptional response. This approach bypasses the need for model fine-tuning, which risks introducing black-box evaluation biases.

### Gold Standard Queries Usage and Dynamic Few-Shot Rerouting

To prevent rapid exhaustion of the $300 Vertex AI credit allocation, the 40 human-verified "Gold Standard" queries are managed programmatically via relational database isolation and conditional in-context routing.

Inserting all 40 detailed human-labeled examples (each including the query, ground-truth text, pipeline output, 1–10 score, and qualitative reasoning) into a single static system prompt creates a massive token payload. Multiplying this large context block across 4,000 independent evaluation runs would generate millions of unnecessary input tokens, inflating costs and risking API rate-limiting crashes.

Instead of a single static file, the system architecture implements a **Dynamic Few-Shot Rerouting** mechanism.

```text
                      DYNAMIC FEW-SHOT REROUTING SYSTEM
                      
                       +--------------------------------+
                       |   Central SQLite Database      |
                       |   - Table: queries             |
                       |   - 400 Verified Rows          |
                       |   - 40 Tagged "is_golden = 1"  |
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
                                       | (Extracts EXACTLY 10 Rows, Drops 30)
                                       v
                       +--------------------------------+
                       |   Dynamic Prompt Assembler     |
                       | - General Scoring Rubrics      |
                       | - 10 Context-Relevant Examples |
                       +--------------------------------+
                                       |
                                       v
                       +--------------------------------+
                       |     Vertex AI Evaluation       |
                       |  (Gemini 1.5 Flash Engine)     |
                       +--------------------------------+

```

#### 1. Relational Database Seeding

All 400 auto-verified queries are written directly to a local SQLite database table named `queries`. A dedicated Boolean column named `is_golden` is assigned to every row.

* The 360 unverified baseline testing queries are marked with `is_golden = 0`.
* The 40 highly vetted, human-scored, and reasoned baseline queries are marked with `is_golden = 1`.

#### 2. Runtime Context Filtering

During the evaluation phase, the loop execution script processes the 3,600 pipeline generation outputs row by row. Before sending an output text block to the Judge LLM (Gemini 1.5 Flash), the evaluation worker checks the target query's `quadrant` attribute (e.g., `Q1_Direct_Text`, `Q4_Implicit_Table`).

The script executes a localized SQL query to retrieve *only* the golden subset rows matching that specific quadrant context:

```sql
SELECT query_text, true_answer, pipeline_output, human_score, human_reasoning 
FROM queries 
WHERE is_golden = 1 AND quadrant = :current_pipeline_quadrant;

```

#### 3. Token Payload Reduction and Cost Optimization

By shifting from a static 40-example text prompt to this dynamic 10-example filter, the payload size is reduced by 75% per API call.

```text
+-------------------------------------------------------------------------+
|                          TOKEN PAYLOAD COMPARISON                       |
+-------------------------------------------------------------------------+
| [Static Payload Attempt]                                                |
| 40 Examples x ~500 Tokens/Example = 20,000 Input Tokens                 |
| 20,000 Tokens x 4,000 Evaluation Runs = 80,000,000 Total Tokens         |
|                                                                         |
| [Dynamic Rerouting Execution]                                           |
| 10 Contextual Examples x ~500 Tokens = 5,000 Input Tokens               |
| 5,000 Tokens x 4,000 Evaluation Runs = 20,000,000 Total Tokens          |
+-------------------------------------------------------------------------+
| TOTAL RESOURCE CONSERVATION = 60,000,000 TOKENS SAVED                   |
+-------------------------------------------------------------------------+

```

This structural modification keeps token costs safely within the university budget while ensuring the Judge LLM receives highly relevant in-context training examples tailored to the specific text or tabular structure it is currently grading.

---

## 6. Multi-Pipeline Architectural Registry

This project systematically analyzes and records performance metrics for **six pipelines**: four core production architectures are actively implemented, while two are structurally documented as excluded or reserved to protect research depth.

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
| Pipeline 1: Brute-Force Context       |         | Pipeline 5: Vectorless Structural RAG |
| Pipeline 2: Naive Vector RAG          |         |             (SummaryIndex)            |
| Pipeline 3: Optimized Vector RAG      |         |             [EXCLUDED]                |
| Pipeline 4: Vectorless Keyword RAG    |         |                                       |
|             (BM25 Table Index)        |         | Pipeline 6: Hybrid RAG (Fusion Engine)|
+---------------------------------------+         |             [RESERVED FUTURE WORK]    |
                                                  +---------------------------------------+

```

### Active Pipelines

* **Pipeline 1: Brute-Force Context (Baseline)**
* *Architecture*: Zero retrieval layer. The entire parsed document is directly injected into the LLM context window alongside the prompt.
* *Purpose*: Establishes the theoretical accuracy and semantic generation ceiling for the model.
* *Constraint*: Strictly restricted to Micro and Small datasets (under 100 pages) due to physical context-window boundaries and processing degradation over massive sequences.


* **Pipeline 2: Naive Vector RAG**
* *Architecture*: Document text nodes are passed through a uniform embedding model (e.g., `text-embedding-3-small`) to construct a flat vector space. Retrieval is executed purely via top-$K$ cosine similarity search.
* *Purpose*: Acts as the vector baseline control group, isolating how basic semantic similarity fares against dense table maps without any structural guidance.


* **Pipeline 3: Optimized Vector RAG**
* *Architecture*: Inherits the base architecture of Pipeline 2, but applies a two-layer optimization: (a) hard metadata pre-filtering using structural header parameters extracted during ingestion parsing, and (b) a downstream cross-encoder **Re-ranker** (e.g., `Cohere Rerank`) to critically re-order the top-$K$ documents before passing them to the generation engine.
* *Purpose*: Measures whether standard semantic search can be salvaged for complex financial lookups by tuning context densities and applying re-ranking.


* **Pipeline 4: Vectorless Keyword RAG (BM25)**
* *Architecture*: Implemented via LlamaIndex's `KeywordTableIndex`. It completely bypasses dense vector space creation and geometric calculations. Instead, it tokenizes the parsed document hierarchy into discrete keyword blocks, utilizing the statistical **BM25 algorithm** to match explicit query terms directly to structural node components.
* *Purpose*: Serves as the primary alternative architecture, evaluating if strict, frequency-based statistical keyword indexing outperforms high-dimensional embeddings when seeking explicit numerical coordinates or narrow tabular data.



### Excluded and Reserved Pipelines

* **Pipeline 5: Vectorless Structural RAG (SummaryIndex) — [EXCLUDED]**
* *Architecture*: Designed to execute retrieval by traversing an abstract, hierarchical tree structure built from parent summaries and child-node descriptions using LlamaIndex `SummaryIndex`.
* *Justification for Exclusion*: Highly vulnerable to **table fragmentation**. During the automated construction of hierarchical summaries, abstract summary generators routinely drop cell ranges, numeric footnotes, and narrow row variables. Building a custom parser capable of maintaining table integrity introduces high software-engineering overhead that would detract from the core comparative analysis.


* **Pipeline 6: Hybrid RAG (The Fusion Pipeline) — [RESERVED / FUTURE SCOPE]**
* *Architecture*: A serial/parallel composite system that first routes queries through the deterministic BM25 keyword engine (Pipeline 4) to narrow down the target context space, followed by an optimized vector embedding search (Pipeline 3) within that restricted subset.
* *Justification for Reservation*: High risk of **cascading routing degradation**. Stacking two distinct error vectors introduces substantial operational complexity. If the initial BM25 statistical filter improperly excludes a relevant section due to minor semantic phrasing differences, the downstream vector engine will search an incorrect subset, causing a fatal error. To protect research validity, this architecture is excluded from core benchmarking and reserved strictly as an optional extension if core data collection concludes ahead of schedule.



---

## 7. Tri-Pillar Evaluation and Benchmarking Framework

Pipelines are comprehensively audited and compared across three independent variables to create a complete operational profile. To evaluate retrieval performance across different operational constraints, all active retrieval pipelines (Pipelines 2, 3, and 4) are tested using **three distinct values of $K$**:

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
* **Automated LLM-as-a-Judge Prompt Matrix**: Evaluates the text block across a **1-to-10 scoring rubric** embedded with the static few-shot examples from Section 5.
* **Citation Audit Layer**: The judge LLM cross-references the page numbers cited in the generated answer text against the true `evidence_pages` JSON metadata element. If a pipeline outputs a correct numeric answer but cites an incorrect source page, the system flags it as a *coincidental hallucination* and downgrades its score.
* **The Agreement-Rate Guardrail**: To mathematically justify the automated evaluation of the 360 unverified queries, the system runs the Judge LLM against the 40 human-labeled Golden Subset queries and computes the **LLM-Judge Agreement Rate**:

$$\text{Agreement Rate} = \frac{\text{Matches between Human Score and Judge Score}}{\text{Total Samples within Golden Subset}} \times 100\%$$



The system prompt parameters must be tuned until the Agreement Rate is stable at **$>80\%$** before running the full evaluation loop.

### Pillar 3: Efficiency, Cost, and Latency Evaluation Metrics

This pillar captures the production viability and engineering trade-offs of each system architecture:

* **Latency per Query**: Time elapsed (in seconds) from initial query submission to final token generation.
* **Token Consumption & Financial Cost per Query**: Tracking input/output token volume per query to map the operational cost curve of each pipeline across document scales.
* **One-Time Indexing Cost**: Benchmarking the computational overhead, time duration, and token cost required to build a standard vector embedding space vs. a structured index/KeywordTableIndex tree.

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
                                   |  2. DATASET SYNTHESIS (Vertex AI)     |
                                   |  - async_generator.py (Gemini Pro)    |
                                   |  - async_critic.py (Gemini Flash)     |
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
|  - naive_vector_pipeline.py                |         |  - bm25_keyword_pipeline.py                |
|  - optimized_vector_pipeline.py            |         |    (LlamaIndex KeywordTableIndex)          |
|    (Metadata filters + Cohere Re-ranker)   |         |                                            |
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
                                   |  - async_judge.py                     |
                                   |    (Few-Shot Prompt + Citation Audit) |
                                   +---------------------------------------+
```
---

## 9. Limitations and Caveats

### Combinatorial Scale and Execution Overhead

The architectural design introduces a massive execution matrix due to testing multiple variables. Evaluating 400 unique queries across different configuration layers results in an explosive scaling problem that requires careful script tracking.

```text
+-----------------------------------------------------------------------+
|                        COMBINATORIAL SCALE MATH                       |
+-----------------------------------------------------------------------+
|  400 Evaluation Queries (100 per Quadrant)                            |
|                                                                       |
|  [Active Retrieval Pipelines]         [Baseline Stack]                |
|  - Pipeline 2: Naive Vector           - Pipeline 1: Brute-Force       |
|  - Pipeline 3: Optimized Vector       (Runs once per query)           |
|  - Pipeline 4: BM25 Keyword                                           |
|  (Each runs at K = 3, 5, 10)                                          |
|                                                                       |
|  3 Pipelines x 3 K-Values = 9         1 Pipeline x 1 Run = 1          |
|  9 x 400 Queries = 3,600 runs         1 x 400 Queries = 400 runs      |
+-----------------------------------------------------------------------+
|                 TOTAL PIPELINE GENERATIONS = 4,000 RUNS               |
|                 TOTAL JUDGE EVALUATIONS    = 4,000 RUNS               |
+-----------------------------------------------------------------------+

```

* **Query Count Baseline:** A total pool of 400 verified questions (100 items evenly distributed across the 4 core quadrants) is required to establish statistical significance. Small evaluation pools (e.g., 20–30 queries) fail to expose performance boundaries in structural vs. narrative text.
* **Run Count Multiplier:** Running 3 variable retrieval pipelines across 3 independent values of $K$ ($K \in \{3, 5, 10\}$) produces 3,600 runs. Adding the 400 control baseline runs from the un-retrieved Brute-Force context layer locks the execution requirement at **4,000 total pipeline iterations**.
* **Evaluation Volume:** Once those 4,000 answers are generated, they must each be checked individually by the evaluation system, creating an additional **4,000 evaluation engine runs**.

---

### The Necessity of Asynchronous Batch Processing

Executing 4,000 sequential pipeline generation runs and 4,000 sequential evaluation steps using standard, single-threaded Python synchronous `for` loops is entirely unfeasible within an 8-week timeline.

```text
[Synchronous Process] (Fatal Timeout Risk)
Run 1 ----> Wait for API (2s) ----> Run 2 ----> Wait for API (2s) [Total: ~4+ Hours per pipeline]

[Asynchronous Batch Processing] (Required Production Design)
Run 1 ---\
Run 2 -----+---> Async IO Loop Queue ---> Concurrent Vertex AI Engine [Total: Minutes per pipeline]
Run 3 ---/

```

* **Network Timeout Defenses:** Standard synchronous network calls frequently experience connection drops or socket timeouts over large datasets, which can stall scripts and lead to data losses.
* **Concurrent Resource Maximization:** The system must utilize asynchronous worker pools (`asyncio`, `aiohttp`, or native SDK Async clients). Grouping tasks into concurrent batches allows multiple inputs to hit the cloud APIs simultaneously, drastically reducing data ingestion time from hours down to minutes.

---

### Vertex AI Rate Limits and Credit Constraints

Operating heavily within a solo environment backed by a $300 Google Cloud credit budget exposes the architecture to two hard operational limits.

* **HTTP 429 Rate Limiting:** Concurrent batching will quickly exhaust standard API token-per-minute (TPM) or requests-per-minute (RPM) quotas, triggering immediate HTTP 429 exceptions. The asynchronous framework must be configured with a strict resilience handler (e.g., the `tenacity` library) to apply **exponential backoff and jitter algorithms**, keeping the execution traffic smoothly within cloud bounds without crashing.
* **Budget Exhaustion Trap:** Processing 2-million-token files repeatedly using high-tier models will drain the $300 allocation long before data collection finishes. To prevent this, model roles must be tiered: **Gemini 1.5 Pro** is used only for the initial, long-context Query Generation phase. The lightweight **Gemini 1.5 Flash** model must be used for bulk Critic lookups and Judge evaluations to significantly reduce token costs.

---

### Software Stack Version Instability (LlamaIndex Drift)

Data framework orchestration tools (specifically LlamaIndex) undergo rapid development and frequent breaking syntax changes.

* **Syntax Degradation:** Standard model coding tools often reference older, deprecated library models and methods. If code generation isn't strictly controlled, it can result in broken implementations of key structures like `KeywordTableIndex` or vector configurations.
* **Mitigation Strategy:** Code requirements must pin exact version dependencies (e.g., `llama-index==0.10.x`). Current framework documentation snippets should be directly provided to your programming assistant to prevent it from inventing non-existent parameters.

---

### Relational Data Management Overload

Generating 4,000 distinct data points across multiple pipelines, tracking varying parameters of $K$, and recording latency, costs, and output text strings will quickly become unmanageable if stored in loose CSV or JSON flat files.

* **File Corruption Vulnerability:** Appending raw strings to loose files mid-loop often breaks file structures during unexpected script crashes, corrupting previously harvested data.
* **Relational Enforcement Layer:** A local **SQLite database schema** is required from day one. Pipelines must commit results immediately to strongly isolated tables (`nodes`, `queries`, `results`), ensuring that if a process crashes at run 2,500, the data from the first 2,499 runs remains safely preserved and queryable.

---

### Coincidental Correctness and Citation Blindspots

A significant algorithmic vulnerability in RAG systems is "coincidental correctness," where an engine outputs a factually accurate answer by pulling data from an completely irrelevant page.

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

1. **Standardized Context Volumes**: To guarantee parity between Pipeline 2, Pipeline 3, and Pipeline 4, the total context mass (token volume passed to the generation LLM) is kept constant across evaluations.
2. **Explicit Citation Enforcement**: RAG prompt configurations explicitly mandate that the generating model provide source-page attributions. This allows the evaluation framework to flag instances of coincidental correctness, where the correct answer was generated from irrelevant or incorrect context.
3. **Methodological Transparency**: The methodology chapter will document all six original architectural iterations. It will provide formal, engineering-based justifications for the exclusion of the SummaryIndex architecture and the reservation of the Hybrid model, establishing a clear narrative of deliberate project scoping.