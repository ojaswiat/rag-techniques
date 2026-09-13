<!-- converted from Proposal_v1.0.0.docx -->


A Comparative Benchmark of Semantic, Statistical, and Structural Retrieval Paradigms for Retrieval-Augmented Generation over SEC 10-K Filings

Design and Specification Proposal, COMP702 M.Sc. Project (2026/27)

Submitted by
Ojaswi Athghara
(Student ID 201959096)
under the supervision of
Blaine Keetch

SCHOOL OF COMPUTER SCIENCE AND INFORMATICS
UNIVERSITY OF LIVERPOOL

# Statement of Ethical Compliance: A0
Data Category: A. Every source document is a United States SEC 10-K filing obtained from SEC EDGAR, a public regulatory archive. The data is publicly available, contains no personal or confidential information, and its use requires no licence, consent, or data-sharing agreement.
Participant Category: 0. The project involves no human participants at any stage. The 140-query benchmark is generated and verified entirely by two independent language models acting as generator and critic, and the two manual steps (labelling teaching exemplars and hand-scoring validation outputs) are carried out solely by the researcher on the project’s own outputs, not on data gathered from, or about, other people.
I confirm that I have read the ethical guidelines and will follow them during this project. This project uses only publicly available, non-personal United States SEC 10-K corporate filings sourced from SEC EDGAR. It involves no human participants and no personal data of any kind.

# Table of Contents

# 1. Project Description
Retrieval-Augmented Generation (RAG) systems answer questions by pairing a retriever that selects relevant evidence from a corpus with a language model that generates a grounded answer (Lewis et al., 2020). Most RAG benchmarks target encyclopaedic or open-domain text; far less is known about how different retrieval paradigms behave on dense, table-heavy financial disclosures such as SEC 10-K filings, where an answer may sit inside a single cell of a multi-row table rather than a sentence of prose (Chen et al., 2021). This project builds and benchmarks three complete RAG pipelines: a semantic retriever, which finds evidence by meaning using numeric representations of text (dense vector embeddings); a statistical retriever, which finds evidence by matching exact words and their frequency using the long-established BM25 algorithm; and a structural retriever, which navigates a tree of AI-generated summaries built once over each document. These three are tested against a 140-query, human-anchored benchmark spanning direct and inferential questions over both narrative text and financial tables, to establish where each paradigm succeeds and where it degrades.
# 2. Aims and Requirements
## 2.1 Aims
- Design and implement three architecturally distinct RAG retrieval pipelines (semantic, statistical, structural) sharing one evaluation harness, so that performance differences are attributable to retrieval strategy rather than to generation.
- Construct an adversarially verified, human-anchored benchmark of 140 questions, stratified across four query types (direct/implicit retrieval over text/table content), grounded in real SEC 10-K filings.
- Quantify each pipeline’s retrieval accuracy, answer quality, and computational efficiency, and identify the conditions under which each paradigm degrades.
## 2.2 Requirements: Essential
- Parse SEC 10-K filings into metadata-enriched, atomic text/table nodes without bisecting tables.
- Implement three distinct pipelines - P1 (dense embeddings with a cross-encoder reranker), P2 (Okapi BM25), and P3 (hierarchical summary-tree) retrievers sharing one answering model.
- Generate and adversarially verify a 140-query benchmark with node level ground truth citations.
- Validate an automated LLM judge against human scores before using it to grade the full benchmark.
- Persist all queries, retrieved evidence, and scores in a relational (SQLite) store with crash-safe resume.
## 2.3 Requirements: Desirable
- Extend the comparison with a metadata pre-filter or hybrid-fusion ablation (reserved future-scope pipelines).
- Visualise per-quadrant performance gaps in a comparison view for the dissertation write-up.
# 3. Key Literature and Background Reading
Lewis et al. (2020) framed answer generation grounded in retrieved evidence as a way of reducing hallucination relative to purely parametric generation, and this Retrieval-Augmented Generation framing motivates the project’s overall design: a retriever supplies evidence, and one shared answerer consumes it.
On the statistical side, Robertson and Zaragoza (2009) formalised the probabilistic relevance framework that underlies BM25, which remains a strong, fully deterministic retrieval baseline and forms this project’s P2 pipeline. On the semantic side, Karpukhin et al. (2020) showed that learned dense bi-encoder retrieval can outperform BM25 by 9–19% absolute on open-domain question answering, while Nogueira and Cho (2019) showed that adding a cross-encoder reranking stage over an initial candidate set materially improves precision; together these findings motivate the project’s P1 embed-then-rerank design. The embedding and reranker models used for P1 draw on the BGE family released by Xiao et al. (2023).
Sarthi et al. (2024) introduced RAPTOR, which recursively clusters and summarises text into a retrievable tree; this is the architectural basis for the project’s P3 structural pipeline, although their evaluation, like most RAG literature, is conducted on narrative rather than tabular text.
The domain challenge that motivates this project is well documented: Chen et al. (2021) introduced FinQA and showed that even strong pre-trained models fall far short of expert humans at multi-step numerical reasoning over financial tables, which is why the benchmark constructed here explicitly stratifies table-heavy query quadrants. Liu et al. (2024) further showed that model accuracy degrades when relevant evidence sits in the middle of a long context, which is the argument for retrieval-based context selection over naive full-document stuffing.
Finally, on evaluation methodology, Zheng et al. (2023) showed that a strong LLM judge can reach over 80% agreement with human preference judgements, the same threshold this project adopts as its judge-validation gate before trusting an automated judge to grade the full benchmark.
None of the studies above evaluate all three retrieval paradigms side by side on a single financial-filing benchmark stratified by both query type and content modality (text versus table); this is the specific gap the proposed project addresses.
# 4. Development and Implementation Summary
The core of the system is built in Python 3 and uses LlamaIndex as a common retrieval and orchestration backbone, so that all three pipelines expose the same retriever interface. Python is chosen because the whole ecosystem, i.e., LlamaIndex, the Groq SDK, rank_bm25, ChromaDB, and the HuggingFace BGE models, is all Python-native, so trying to rebuild these components in another language would mean redoing mature retrieval and embedding infrastructure from scratch. LlamaIndex is specifically chosen over a lower-level option like LangChain, because its node and scored-result abstractions already line up with the project's node-centric data model (Section 5), which lets the three pipelines share one retriever interface without needing an extra adapter layer. Generation, dataset critique, and judging are all handled by open-source instruction models served for free through Groq (rate-limited rather than billed, so the implementation ends up with zero recurring spend). Embeddings (BAAI/bge-small-en-v1.5) and reranking (BAAI/bge-reranker-base) both run locally on CPU.
ChromaDB acts as the local vector store for P1, rank_bm25 handles the keyword index for P2, and a cached LlamaIndex SummaryIndex serves as the structural pipeline for P3. A single SQLite database, run in Write-Ahead Logging mode, is the only state store; every benchmark run commits right away, so if there's a crash, it picks back up from the last written row instead of burning unnecessary tokens again. Queries get split into three separate sets, PQ (100, the benchmark), GQ (20, Judge teaching exemplars), and JEQ (20, Judge validation), and this is enforced at the schema level, so no pipeline or prompt ever sees past its own group. Asynchronous worker pools, kept in check by a semaphore and wrapped in an exponential-backoff retry layer, keep concurrent API calls within Groq's free-tier rate limits. The workflow is organized phase by phase as laid out in Section 10, with the code for each phase committed and tested under a three-item local throttle before it gets released at full scale, so a fault found in one phase never ends up eating into the free-tier quota set aside for an earlier or later phase.
Figure 4.1: High-Level Pipeline Architecture
# 5. Data Sources
All data is sourced from SEC EDGAR, the US Securities and Exchange Commission's public filing system: a corpus of approximately six to nine 10-K annual filings, drawn from two to three companies across two to three fiscal years. Filings are parsed via LlamaParse (free tier) into metadata-enriched text and table nodes.
## 5.1 Nature of the SEC 10-K Filing Data
Each filing contains narrative sections (risk factors, business description, management's discussion) and structured tables (financial statements, segment data, numerical metrics with currency values). The data is heterogeneous: prose sections use formal language with embedded financial figures, while tables present precisely formatted multi-year numerical comparisons. This heterogeneity is valuable for benchmarking. It tests whether retrieval pipelines can handle both semantic and structured data extraction. The raw structure of the data is covered in the next section (5.2).
## 5.2 Raw Data Sample of the SEC 10-K Filing Data
Figure 5.1 shows a sample paragraph from Apple's SEC 10-K filing in raw iXBRL format, with a financial figure embedded in XML markup. Figure 5.2 displays the rendered table corresponding to the raw HTML/XML code in Figure 5.3. This table from Apple's 10-K, presents interest rate sensitivity analysis with comparative figures across fiscal years. Together, these samples illustrate the dual nature of SEC 10-K data: unstructured prose with embedded financial figures and structured tabular data with precise column and row definitions. Both formats are parsed as nodes during data preparation, preserving their original structure and metadata for retrieval and evaluation.

Figure 5.1: Sample paragraph data structure (iXBRL disclosure section)


Figure 5.2: Sample table render (Interest Rate Sensitivity table)

Figure 5.3: Sample table data structure (Interest Rate Sensitivity table)
# 6. Testing and Evaluation
We evaluate the system along three key dimensions, each chosen to reveal where different retrieval approaches excel or struggle:
- Retrieval metrics (Precision@K, Recall@K, Evidence Hit Rate) measure how well each pipeline finds the right evidence nodes. Since we know exactly which nodes answer each query, we compute these deterministically against that ground truth.
- Answer-quality metrics assess how well the final answers actually work. We use an LLM-as-judge scoring on a 1–10 scale as our primary measure, backed up by lexical checks (token-level F1 and numeric-tolerant Exact Match) and a Citation Audit that flags answers which happen to be correct despite citing the wrong evidence.
- Efficiency metrics capture the real cost of running each approach: wall-clock latency, LLM token consumption, and the one-time cost to build each pipeline’s index.
The automated judge isn’t trusted right out of the box. Before it’s allowed to grade all 900 benchmark runs, it must first pass a validation gate: achieving greater than 80% agreement with hand-scored outputs on a separate validation set, a threshold established by prior work on LLM judges (Zheng et al., 2023). To catch bugs before spending free-tier quota at scale, every script that calls a language model is run end-to-end first under a hardcoded three-item local throttle.
# 7. Project Ethics and Human Participants
This project involves no human participants and no personal data; all source material is SEC 10-K filings, which are public corporate disclosures (Data Category A0). The two manual steps in the methodology, hand-labelling 20 teaching exemplars and hand-scoring 60 judge-validation outputs, are carried out solely by the researcher as part of constructing the evaluation harness itself, rather than as a study involving external participants, and therefore fall outside the scope of human-participant ethics review. No further ethical approval beyond this statement is required for the activity planned within this assessment.
# 8. BCS Project Criteria
- Systematic understanding: a cross-paradigm RAG comparison grounded in current literature (Lewis et al., 2020; Karpukhin et al., 2020; Sarthi et al., 2024), exposing paradigm limits which is not yet documented for the SEC-filing data.
- Comprehensive technique understanding: dense retrieval, sparse retrieval, hierarchical summarisation, reranking, and LLM-based evaluation are all designed and built within a single project.
- Originality: the cross-family generator/critic adversarial verification pipeline and the disjoint three-set (PQ/GQ/JEQ) evaluation design are original contributions to constructing a RAG benchmark without manual annotation at scale.
- Sound judgement under incomplete information: deliberate, documented scoping decisions, such as dropping a metadata pre-filter and accepting a token-per-day-bound runtime, demonstrate judgement under real resource constraints.
- Self-direction: a one person, ten weeks build plan run entirely on free-tier infrastructure with no managed budget demonstrates autonomous planning.
- Critical self-evaluation of the process: the Limitations framing already built into the methodology, a single temperature-zero run per benchmark cell and an approximately eighty per cent judge-validation pass on only sixty hand-scored samples, is treated explicitly as a pragmatic constraint rather than a strong statistical proof.
# 9. UI/UX Mockup
This is a research and benchmarking system rather than an end-user application, so its principal "interface" is the results comparison view produced at the end of the run. Day to day, the researcher's surface is a command line. A wireframe sketch of the final comparison view, the artefact consulted most, is shown below.
Figure 9.1: Results Comparison View (Wireframe, illustrative placeholder values, not final results)
# 10. Project Plan
The build is scoped to a one person, ten-week schedule, with active development substantially complete by Week 7 and the final three weeks overlapping the full benchmark run with results analysis, dissertation write-up, and preparation of the final project presentation.
Table 10.1: 10-Week Project Gantt Chart
# 11. Risks and Contingency Plans
Table 11.1: Risk Management Plan

# 12. References
Chen, Z., Chen, W., Smiley, C., Shah, S., Borova, I., Langdon, D., Moussa, R., Beane, M., Huang, T.-H., Routledge, B. and Wang, W.Y. (2021) 'FinQA: A Dataset of Numerical Reasoning over Financial Data', Proceedings of the 2021 Conference on Empirical Methods in Natural Language Processing (EMNLP 2021), pp. 3697–3711.
Karpukhin, V., Oguz, B., Min, S., Lewis, P., Wu, L., Edunov, S., Chen, D. and Yih, W.-t. (2020) 'Dense Passage Retrieval for Open-Domain Question Answering', Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP 2020), pp. 6769–6781.
Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N., Küttler, H., Lewis, M., Yih, W.-t., Rocktäschel, T., Riedel, S. and Kiela, D. (2020) 'Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks', Advances in Neural Information Processing Systems, 33 (NeurIPS 2020).
Liu, N.F., Lin, K., Hewitt, J., Paranjape, A., Bevilacqua, M., Petroni, F. and Liang, P. (2024) 'Lost in the Middle: How Language Models Use Long Contexts', Transactions of the Association for Computational Linguistics, 12, pp. 157–173.
Nogueira, R. and Cho, K. (2019) 'Passage Re-ranking with BERT', arXiv preprint, arXiv:1901.04085.
Robertson, S. and Zaragoza, H. (2009) 'The Probabilistic Relevance Framework: BM25 and Beyond', Foundations and Trends in Information Retrieval, 3(4), pp. 333–389.
Sarthi, P., Abdullah, S., Tuli, A., Khanna, S., Goldie, A. and Manning, C.D. (2024) 'RAPTOR: Recursive Abstractive Processing for Tree-Organized Retrieval', Proceedings of the International Conference on Learning Representations (ICLR 2024).
Xiao, S., Liu, Z., Zhang, P. and Muennighoff, N. (2023) 'C-Pack: Packaged Resources to Advance General Chinese Embedding', arXiv preprint, arXiv:2309.07597.
Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E.P., Zhang, H., Gonzalez, J.E. and Stoica, I. (2023) 'Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena', Advances in Neural Information Processing Systems, 36 (NeurIPS 2023).
| SEC EDGAR 10-K Filings (public, free) |
| --- |
| ↓ |
| Ingestion & Parsing: LlamaParse → metadata-enriched Node Store (SQLite) |
| ↓ |
|  |
| ↓ |
| Shared Answerer: Llama 3.3 70B (temperature = 0) |
| ↓ |
| LLM Judge (Qwen3-32b, validated >80% human agreement on JEQ) + Deterministic Code Metrics |
| ↓ |
| Results Store (SQLite) → Analysis & Comparison |
| Key point. Every recurring component in this pipeline runs on a free tier or local CPU, so the expected spend for the full benchmark is $0.00; the only binding constraint is Groq's daily token throughput, not budget. |
| --- |
| Key point. The judge is gated, not trusted by default: it must clear 80% agreement with hand-scored human judgements on a disjoint validation set before it is allowed to grade the full 900-run benchmark. |
| --- |
| Pipeline | K | Precision@K | Recall@K | Judge Score | Latency (s) |
| --- | --- | --- | --- | --- | --- |
| P1_vector | 5 | 0.62 | 0.81 | 8.1 | 1.84 |
| P2_bm25 | 5 | 0.54 | 0.73 | 7.0 | 0.91 |
| P3_structural | 5 | 0.41 | 0.66 | 6.4 | 1.10 |
| Phase | W1 | W2 | W3 | W4 | W5 | W6 | W7 | W8 | W9 | W10 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1. Environment & Infra |  |  |  |  |  |  |  |  |  |  |
| 2. Ingestion & Parsing |  |  |  |  |  |  |  |  |  |  |
| 3. P3 Summary-Index Build |  |  |  |  |  |  |  |  |  |  |
| 4. Dataset Gen & Verification |  |  |  |  |  |  |  |  |  |  |
| 5. Pipeline Impl. (P1/P2/P3) |  |  |  |  |  |  |  |  |  |  |
| 6. Judge Build & Validation Gate |  |  |  |  |  |  |  |  |  |  |
| 7. Full Benchmark Execution |  |  |  |  |  |  |  |  |  |  |
| 8. Results Analysis & Write-up |  |  |  |  |  |  |  |  |  |  |
| Risk | Contingency | Likelihood | Impact |
| --- | --- | --- | --- |
| Groq free-tier token-per-day limit reached mid-run | Exponential backoff with jitter, multi-day paced execution with crash-safe resume, prompt caching, fallback to the paid Developer tier if the schedule slips | Medium | Medium |
| LlamaParse fragments or bisects a financial table | Randomised 20-section manual parsing audit; re-tune parser settings or discard and re-parse the affected filing | Medium | High |
| Automated LLM judge fails the 80% human-agreement gate | Tune the scoring rubric and/or swap the judge to a different model family; re-run the validation gate before proceeding | Medium | High |
| Breaking API changes in a fast-moving dependency (LlamaIndex) | Pin exact package versions at project start; consult current documentation before any upgrade | Low | Medium |
| Concurrent writes corrupt the SQLite results store mid-run | Write-Ahead Logging (WAL) mode; crash-safe resume keyed on a unique constraint; commit after every individual run | Low | High |
| One person, ten-week timeline slips | Throttle-first testing on every phase before full-scale release; background-paced benchmark execution; buffer reserved across the final three weeks | Medium | Medium |
| Local machine failure or loss of unsynced work (no backups) | Nightly off-machine backup of the SQLite database, parsed nodes, and code to a second location (a git remote and cloud sync); Write-Ahead Logging commits keep the loss window to minutes of work, not days | Low | High |