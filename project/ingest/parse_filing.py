"""Parses raw filings into clean Markdown via LlamaParse (Cost-effective
tier, atomic-table mode). Caches aggressively: re-parsing the same file
within 48 hours is free on LlamaParse's side, but we still skip the network
call entirely when a fresh cached copy already exists.

See resources/specs/Budget.md §3 and this phase's plan Global Constraints:
Cost-effective tier only, never Agentic/Premium.
"""
import os
import time

from llama_parse import LlamaParse

import config

_CACHE_FRESH_SECONDS = 48 * 3600

_parser = LlamaParse(
    api_key=config.LLAMA_CLOUD_API_KEY or "placeholder-key-for-import-only",
    result_type="markdown",
    parsing_instruction=(
        "This is a SEC 10-K filing. Extract all tables as clean, complete "
        "Markdown tables -- never split or truncate a table across multiple "
        "chunks. Preserve section headers (e.g. 'Item 1A. Risk Factors') as "
        "Markdown headings."
    ),
)


def _is_cache_fresh(path: str) -> bool:
    if not os.path.exists(path):
        return False
    age = time.time() - os.path.getmtime(path)
    return age < _CACHE_FRESH_SECONDS


async def parse_filing(document_id: str, raw_path: str, parsed_dir: str = "data/parsed") -> str:
    os.makedirs(parsed_dir, exist_ok=True)
    cached_path = os.path.join(parsed_dir, f"{document_id}.md")

    if _is_cache_fresh(cached_path):
        return cached_path

    documents = await _parser.aload_data(raw_path)
    markdown_text = "\n\n".join(doc.text for doc in documents)

    with open(cached_path, "w") as f:
        f.write(markdown_text)

    return cached_path
