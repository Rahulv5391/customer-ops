import json

import chromadb

from app.core.config import settings
from app.models.kb_document import KBDocument

_COLLECTION_NAME = "kb_documents"

_client = chromadb.PersistentClient(path=settings.chroma_persist_dir)


def _get_collection():
    # Explicit cosine space so similarity = 1 - distance is a well-defined
    # comparison against RAG_MIN_SIMILARITY (Chroma's default is squared L2,
    # which has no fixed 0..1 range to threshold against).
    return _client.get_or_create_collection(
        name=_COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


def reset_collection() -> None:
    """Drop and recreate the collection - the Chroma-side equivalent of
    seed_data.py's Base.metadata.drop_all/create_all. Necessary because
    KBDocument.id is regenerated fresh on every reseed, so a per-document
    delete-then-add can't clean up the previous run's now-orphaned ids."""
    try:
        _client.delete_collection(_COLLECTION_NAME)
    except Exception:
        pass


def ingest_document(document: KBDocument) -> None:
    """(Re-)ingest one KBDocument's sections as embedded chunks.

    Deletes any existing chunks for this document_id first, then adds the
    current sections - idempotent re-ingestion regardless of whether the
    section count changed since the last ingest (Architecture.md §5).
    """
    collection = _get_collection()
    collection.delete(where={"document_id": document.id})

    content = json.loads(document.content_json or "{}")
    sections = content.get("sections", [])
    if not sections:
        return

    ids, texts, metadatas = [], [], []
    for i, section in enumerate(sections):
        heading = section.get("heading", "")
        body = section.get("content", "")
        ids.append(f"{document.id}:{i}")
        texts.append(f"{document.title} - {heading}\n{body}")
        metadatas.append(
            {
                "document_id": document.id,
                "document_title": document.title,
                "category": document.category,
                "version": document.version,
                "source_updated_at": document.source_updated_at,
                "section": heading,
            }
        )
    collection.add(ids=ids, documents=texts, metadatas=metadatas)


def remove_document(document_id: str) -> None:
    _get_collection().delete(where={"document_id": document_id})


def search(query: str, top_k: int | None = None) -> list[dict]:
    """Returns the top_k most similar chunks, each as
    {text, similarity, document_title, version, source_updated_at, section},
    ordered most-similar first. Empty list if the collection has no
    documents yet."""
    collection = _get_collection()
    if collection.count() == 0:
        return []

    result = collection.query(
        query_texts=[query],
        n_results=top_k or settings.rag_top_k,
    )
    hits = []
    documents = result.get("documents") or [[]]
    metadatas = result.get("metadatas") or [[]]
    distances = result.get("distances") or [[]]
    for text, metadata, distance in zip(documents[0], metadatas[0], distances[0]):
        hits.append(
            {
                "text": text,
                "similarity": 1.0 - distance,
                "document_title": metadata["document_title"],
                "version": metadata["version"],
                "source_updated_at": metadata["source_updated_at"],
                "section": metadata["section"],
            }
        )
    return hits
