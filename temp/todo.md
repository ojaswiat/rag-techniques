## Ingest the data before page 4

Try to run for TSLA first instead of MSFT.

Run this from the project directory:

cd /Users/ojaswi/Projects/rag-techniques/project
.venv/bin/python -m pipelines.structural.build_summary_index

That's the same command that was already run — it'll skip the 3 cached AAPL filings (AAPL_2023, AAPL_2024, AAPL_2025) automatically and resume from MSFT_2023 onward once Groq's daily token quota has reset.