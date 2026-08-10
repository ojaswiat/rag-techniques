"""Shared retriever interface for P1/P2/P3 (Architecture.md §4.1).

Every retrieval pipeline implements retrieve(), which must filter to the
given document_id internally and never return nodes from another filing
(Architecture.md §0 Decision 2 -- per-document retrieval scope, not a
banned metadata pre-filter, since document_id is a property of the query
itself, not an answer-location hint).
"""
from abc import ABC, abstractmethod

from llama_index.core.schema import NodeWithScore


class Retriever(ABC):
    @abstractmethod
    def retrieve(self, query_text: str, document_id: str, k: int) -> list[NodeWithScore]:
        ...
