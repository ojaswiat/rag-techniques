"""Builds the shared P1 vector index (Phase 5) -- one Chroma collection,
metadata-tagged by document_id, covering every filing's nodes.

Fully local: embeddings via fastembed (BAAI/bge-small-en-v1.5), no LLM
call, per Guardrails.md's "Retrieval/indexing runs locally" rule.
Resumable at document granularity, matching build_summary_index.py's
skip-if-already-built pattern.
"""
import asyncio
import json
from pathlib import Path

import chromadb
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.schema import NodeRelationship, RelatedNodeInfo
from llama_index.embeddings.fastembed import FastEmbedEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

import database_manager as dbm
import loop_template
from pipelines.structural.node_convert import nodes_to_llama_nodes

STORAGE_ROOT = Path("storage/chroma")
COLLECTION_NAME = "p1_vector"
DB_PATH = "benchmark.db"
MANIFEST_PATH = "data/filings_manifest.json"
_EMBED_MODEL_NAME = "BAAI/bge-small-en-v1.5"


def _get_collection(storage_root: Path | None = None):
    # storage_root defaults to the module-level STORAGE_ROOT, resolved at
    # call time (not bound as a default argument) so tests can monkeypatch
    # bvi.STORAGE_ROOT and have every call pick up the override.
    if storage_root is None:
        storage_root = STORAGE_ROOT
    client = chromadb.PersistentClient(path=str(storage_root))
    return client.get_or_create_collection(COLLECTION_NAME)


def is_document_indexed(document_id: str, storage_root: Path | None = None) -> bool:
    collection = _get_collection(storage_root)
    existing = collection.get(where={"document_id": document_id}, limit=1)
    return len(existing["ids"]) > 0


async def build_index_for_document(
    document_id: str,
    db_path: str = DB_PATH,
    storage_root: Path | None = None,
) -> dict:
    if is_document_indexed(document_id, storage_root=storage_root):
        return {"document_id": document_id, "skipped": True, "node_count": 0}

    nodes = await dbm.get_nodes_by_document(db_path, document_id)
    if not nodes:
        raise ValueError(
            f"No nodes found for document_id={document_id!r} -- this filing "
            "has not been ingested yet (Phase 2). Refusing to index nothing, "
            "which would leave is_document_indexed() permanently False for "
            "a real gap vs a not-yet-run build."
        )

    llama_nodes = nodes_to_llama_nodes(nodes)
    # ChromaVectorStore writes node.ref_doc_id into its own reserved
    # top-level "document_id" metadata field (llama_index.core.vector_stores
    # .utils.node_to_metadata_dict), independent of our custom
    # metadata["document_id"] set by nodes_to_llama_nodes. Without a source
    # relationship, ref_doc_id is None and that reserved field overwrites
    # ours with the literal string "None", breaking is_document_indexed's
    # where-filter. Set the SOURCE relationship so both agree.
    for node in llama_nodes:
        node.relationships[NodeRelationship.SOURCE] = RelatedNodeInfo(
            node_id=document_id
        )

    collection = _get_collection(storage_root)
    vector_store = ChromaVectorStore(chroma_collection=collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    embed_model = FastEmbedEmbedding(model_name=_EMBED_MODEL_NAME)

    VectorStoreIndex(
        nodes=llama_nodes,
        storage_context=storage_context,
        embed_model=embed_model,
    )

    return {"document_id": document_id, "skipped": False, "node_count": len(nodes)}


async def main():
    STORAGE_ROOT.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
    manifest = loop_template.apply_throttle(manifest)

    for entry in manifest:
        document_id = entry["document_id"]
        result = await build_index_for_document(document_id)
        status = "skipped (cached)" if result["skipped"] else f"indexed ({result['node_count']} nodes)"
        print(f"{document_id}: {status}")


if __name__ == "__main__":
    asyncio.run(main())
