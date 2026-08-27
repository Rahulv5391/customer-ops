from sqlalchemy.orm import Session

from app.models.kb_document import KBDocument
from app.schemas.kb_document import KBDocumentUpdate


def get_document(db: Session, document_id: str) -> KBDocument | None:
    return db.get(KBDocument, document_id)


def get_by_content_hash(db: Session, content_hash: str) -> KBDocument | None:
    return db.query(KBDocument).filter(KBDocument.content_hash == content_hash).first()


def list_documents(db: Session, category: str | None = None) -> list[KBDocument]:
    q = db.query(KBDocument)
    if category:
        q = q.filter(KBDocument.category == category)
    return q.order_by(KBDocument.title).all()


def update_document(db: Session, document: KBDocument, updates: KBDocumentUpdate) -> KBDocument:
    for field, value in updates.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(document, field, value)
    db.commit()
    db.refresh(document)
    return document


def delete_document(db: Session, document: KBDocument) -> None:
    db.delete(document)
    db.commit()
