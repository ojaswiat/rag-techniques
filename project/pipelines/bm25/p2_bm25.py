"""P2: BM25 statistical retrieval (Architecture.md §6 Phase 5).

Loads the per-document pickled BM25Okapi corpus built by
build_bm25_index.py, tokenizes the query with the exact same tokenizer
used at index time, and ranks by BM25 score. No embeddings, no LLM call
anywhere in this class -- node content comes straight from
database_manager rather than through the LlamaIndex node-conversion
machinery P1/P3 use, keeping P2 a genuinely raw statistical baseline.
"""
import asyncio
import pickle
from pathlib import Path

from llama_index.core.schema import NodeWithScore, TextNode

import database_manager as dbm
import pipelines.bm25.build_bm25_index as bbi
from pipelines.base import Retriever
from pipelines.bm25.tokenizer import tokenize


class P2BM25Retriever(Retriever):
    def __init__(self, storage_root: Path | None = None, db_path: str = bbi.DB_PATH):
        if storage_root is None:
            storage_root = bbi.STORAGE_ROOT
        self._storage_root = storage_root
        self._db_path = db_path

    def retrieve(self, query_text: str, document_id: str, k: int) -> list[NodeWithScore]:
        index_path = bbi.index_path(document_id, self._storage_root)
        if not index_path.exists():
            raise FileNotFoundError(
                f"No BM25 index found for document_id={document_id!r} at "
                f"{index_path}. Run build_bm25_index.py for this filing "
                "before querying it."
            )
        with open(index_path, "rb") as f:
            payload = pickle.load(f)
        node_ids: list[str] = payload["node_ids"]
        bm25 = payload["bm25"]

        tokenized_query = tokenize(query_text)
        scores = bm25.get_scores(tokenized_query)

        ranked = sorted(
            zip(scores, range(len(node_ids)), node_ids),
            key=lambda item: (-item[0], item[1]),
        )[:k]

        # retrieve() is sync because the shared Retriever ABC requires it, so
        # this async DB read is driven by asyncio.run(). asyncio.run() raises
        # RuntimeError if called while an event loop is already running, so a
        # future async caller (an `async def main()` loop script, as used
        # elsewhere in this repo) must not call retrieve() directly on its own
        # loop. Such a caller should either wrap the call in
        # asyncio.to_thread(retriever.retrieve, ...), or drop the DB round-trip
        # entirely by carrying node text inside the pickled index payload.
        nodes = asyncio.run(dbm.get_nodes_by_document(self._db_path, document_id))
        nodes_by_id = {node["node_id"]: node for node in nodes}

        results = []
        for score, _, node_id in ranked:
            row = nodes_by_id[node_id]
            text_node = TextNode(
                id_=row["node_id"],
                text=row["content"],
                metadata={
                    "document_id": row["document_id"],
                    "parent_item_header": row["parent_item_header"],
                    "node_type": row["node_type"],
                    "source_page_num": row["source_page_num"],
                },
            )
            results.append(NodeWithScore(node=text_node, score=float(score)))
        return results
