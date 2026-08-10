"""P1: semantic vector retrieval (Architecture.md §6 Phase 5).

Filters to the query's own document_id (required, not the banned
metadata pre-filter -- see Architecture.md Decision 0.2), then reranks a
wider Chroma candidate set down to k with a local cross-encoder. No LLM
call anywhere in this class.
"""
from pathlib import Path

from llama_index.core import VectorStoreIndex
from llama_index.core.schema import NodeWithScore
from llama_index.core.vector_stores import (
    ExactMatchFilter,
    MetadataFilters,
)
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from pipelines.base import Retriever
from pipelines.vector.build_vector_index import (
    STORAGE_ROOT,
    _EMBED_MODEL_NAME,
    _get_collection,
)
from pipelines.vector.fastembed_reranker import FastEmbedReranker

_PREFETCH_MULTIPLIER = 4
_MIN_PREFETCH = 20


class P1VectorRetriever(Retriever):
    def __init__(self, storage_root: Path = STORAGE_ROOT):
        collection = _get_collection(storage_root)
        vector_store = ChromaVectorStore(chroma_collection=collection)
        embed_model = FastEmbedEmbedding(model_name=_EMBED_MODEL_NAME)
        self._index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
        self._reranker = FastEmbedReranker()

    def retrieve(self, query_text: str, document_id: str, k: int) -> list[NodeWithScore]:
        # Over-fetch from Chroma so the cross-encoder reranker has enough
        # candidates to meaningfully reorder before truncating to k.
        prefetch_k = max(k * _PREFETCH_MULTIPLIER, _MIN_PREFETCH)
        filters = MetadataFilters(filters=[ExactMatchFilter(key="document_id", value=document_id)])
        base_retriever = self._index.as_retriever(similarity_top_k=prefetch_k, filters=filters)
        candidates = base_retriever.retrieve(query_text)
        reranked = self._reranker.postprocess_nodes(candidates, query_str=query_text)
        return reranked[:k]
