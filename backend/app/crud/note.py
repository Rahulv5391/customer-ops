from sqlalchemy.orm import Session

from app.models.note import CustomerNote


def add_note(db: Session, customer_id: str, author: str, body: str) -> CustomerNote:
    note = CustomerNote(customer_id=customer_id, author=author, body=body)
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
