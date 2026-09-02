"""Tests rag_service.reingest_if_empty - the safety net that re-derives the
Chroma index from KBDocument rows already in the SQL database, so KB search
survives an ephemeral filesystem (e.g. Render without a persistent disk)
resetting the local Chroma directory on every restart."""

import json

from app.models.kb_document import KBDocument
from app.services import rag_service
from app.services.document_extraction import compute_content_hash


def _make_kb_document(db, title="Refund Policy", sections=None):
    sections = sections or [
        {"heading": "Standard Window", "content": "Refunds are accepted within 30 days of delivery."}
    ]
    doc = KBDocument(
        title=title,
        category="policy",
        version="v1",
        source_updated_at="2026-01-01",
        content_json=json.dumps({"sections": sections}),
        content_hash=compute_content_hash(sections),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


def test_reingest_if_empty_rebuilds_the_index_from_db_rows(db):
    rag_service.reset_collection()
    _make_kb_document(db)

    assert rag_service.search("refund window") == []  # nothing ingested yet

    rag_service.reingest_if_empty(db)

    hits = rag_service.search("refund window")
    assert len(hits) == 1
    assert hits[0]["document_title"] == "Refund Policy"


def test_reingest_if_empty_is_a_no_op_when_the_index_already_has_data(db):
    rag_service.reset_collection()
    doc = _make_kb_document(db, title="Existing Doc")
    rag_service.ingest_document(doc)

    # A second KBDocument exists in the DB but was never ingested - if
    # reingest_if_empty ran anyway, this title would also become searchable.
    _make_kb_document(
        db,
        title="Never Ingested",
        sections=[{"heading": "Other", "content": "Unrelated shipping policy content."}],
    )

    rag_service.reingest_if_empty(db)

    hits = rag_service.search("refund window", top_k=10)
    titles = {h["document_title"] for h in hits}
    assert titles == {"Existing Doc"}
