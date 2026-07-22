"""Builds and persists one hierarchical TreeIndex per filing (Phase 3,
Guardrails.md §1 -- the only index build permitted to call an LLM, and it
must run once and be cached, never per query).

Deliberately uses llama_index.llms.groq.Groq directly rather than routing
through groq_client.call_groq() -- see
docs/superpowers/specs/2026-07-22-phase3-summary-index-design.md for why
(Phase 5's P3 pipeline needs a real TreeIndex.as_retriever(), which a
custom-built tree wouldn't provide) and the scoped, mitigated risk this
carries (documented in resources/artifacts/Changes.md).
"""
import os
import shutil
import time
from pathlib import Path

from llama_index.core import TreeIndex
from llama_index.core.callbacks import CallbackManager, TokenCountingHandler
from llama_index.llms.groq import Groq

import config
import database_manager as dbm
from pipelines.structural.node_convert import nodes_to_llama_nodes

STORAGE_ROOT = Path("storage/summary_index")
DB_PATH = "benchmark.db"


def _final_dir(document_id: str) -> Path:
    return STORAGE_ROOT / document_id


def _temp_dir(document_id: str) -> Path:
    return STORAGE_ROOT / f"{document_id}.tmp"


def is_built(document_id: str) -> bool:
    return _final_dir(document_id).exists()


async def build_index_for_document(document_id: str) -> dict:
    if is_built(document_id):
        return {"document_id": document_id, "skipped": True}

    nodes = await dbm.get_nodes_by_document(DB_PATH, document_id)
    llama_nodes = nodes_to_llama_nodes(nodes)

    token_counter = TokenCountingHandler()
    llm = Groq(
        model=config.MODEL_ROUTING["p3_index_build"],
        api_key=config.GROQ_API_KEY or "placeholder-key-for-import-only",
        callback_manager=CallbackManager([token_counter]),
    )

    start = time.monotonic()
    index = TreeIndex(nodes=llama_nodes, llm=llm, build_tree=True)
    wall_clock_sec = time.monotonic() - start

    temp_dir = _temp_dir(document_id)
    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    index.storage_context.persist(persist_dir=str(temp_dir))
    os.rename(temp_dir, _final_dir(document_id))

    return {
        "document_id": document_id,
        "skipped": False,
        "wall_clock_sec": wall_clock_sec,
        "input_tokens": token_counter.prompt_llm_token_count,
        "output_tokens": token_counter.completion_llm_token_count,
    }
