import chromadb
import pytest
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo, TextNode
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from pipelines.vector.p1_vector import P1VectorRetriever


def _seed_collection(storage_root, collection_name):
    client = chromadb.PersistentClient(path=str(storage_root))
    collection = client.get_or_create_collection(collection_name)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    embed_model = FastEmbedEmbedding(model_name="BAAI/bge-small-en-v1.5")

    nodes = [
        TextNode(
            id_="AAPL_2025_n0001",
            text="Apple's total net sales were $394.3 billion in fiscal 2025.",
            metadata={"document_id": "AAPL_2025"},
        ),
        TextNode(
            id_="AAPL_2025_n0002",
            text="Apple's research and development expense grew 10 percent.",
            metadata={"document_id": "AAPL_2025"},
        ),
        TextNode(
            id_="MSFT_2025_n0001",
            text="Microsoft's total revenue was $245 billion in fiscal 2025.",
            metadata={"document_id": "MSFT_2025"},
        ),
    ]
    # Chroma's node_to_metadata_dict overwrites metadata["document_id"] with
    # node.ref_doc_id ("None" when unset), independent of the custom
    # document_id key -- mirror build_vector_index.py's fix by setting the
    # SOURCE relationship so both agree, matching the real ingested data
    # shape this retriever queries against.
    for node in nodes:
        node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(
            node_id=node.metadata["document_id"]
        )
    VectorStoreIndex(nodes=nodes, storage_context=storage_context, embed_model=embed_model)


def test_retrieve_filters_to_given_document_id(tmp_path, monkeypatch):
    import pipelines.vector.build_vector_index as bvi
    monkeypatch.setattr(bvi, "STORAGE_ROOT", tmp_path)
    _seed_collection(tmp_path, bvi.COLLECTION_NAME)

    retriever = P1VectorRetriever(storage_root=tmp_path)
    results = retriever.retrieve("What were total net sales?", document_id="AAPL_2025", k=5)

    assert len(results) > 0
    assert all(node.node.metadata["document_id"] == "AAPL_2025" for node in results)
    node_ids = {node.node.node_id for node in results}
    assert "MSFT_2025_n0001" not in node_ids


def test_retrieve_respects_k(tmp_path, monkeypatch):
    import pipelines.vector.build_vector_index as bvi
    monkeypatch.setattr(bvi, "STORAGE_ROOT", tmp_path)
    _seed_collection(tmp_path, bvi.COLLECTION_NAME)

    retriever = P1VectorRetriever(storage_root=tmp_path)
    results = retriever.retrieve("What were total net sales?", document_id="AAPL_2025", k=1)

    assert len(results) == 1


def test_retrieve_returns_most_relevant_node_first(tmp_path, monkeypatch):
    import pipelines.vector.build_vector_index as bvi
    monkeypatch.setattr(bvi, "STORAGE_ROOT", tmp_path)
    _seed_collection(tmp_path, bvi.COLLECTION_NAME)

    retriever = P1VectorRetriever(storage_root=tmp_path)
    results = retriever.retrieve("What were Apple's total net sales?", document_id="AAPL_2025", k=2)

    assert results[0].node.node_id == "AAPL_2025_n0001"
