from sqlalchemy.orm import Session

from app.models.note import CustomerNote
from app.schemas.note import NoteCreate


def add_note(db: Session, customer_id: str, data: NoteCreate) -> CustomerNote:
    note = CustomerNote(customer_id=customer_id, **data.model_dump())
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


def list_notes_for_customer(db: Session, customer_id: str) -> list[CustomerNote]:
    return (
        db.query(CustomerNote)
        .filter(CustomerNote.customer_id == customer_id)
        .order_by(CustomerNote.created_at.desc())
        .all()
    )
