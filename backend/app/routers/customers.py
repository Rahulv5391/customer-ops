from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import customer as customer_crud
from app.crud import note as note_crud
from app.models.agent import SupportAgent
from app.schemas.customer import (
    CustomerCreate,
    CustomerDetailResponse,
    CustomerResponse,
    CustomerUpdate,
)
from app.schemas.note import NoteCreate, NoteResponse
from app.services.auth_service import get_current_agent

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=list[CustomerResponse])
def list_customers(
    query: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    return customer_crud.list_customers(db, query=query, status=status, limit=limit, offset=offset)


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    customer = customer_crud.get_customer_with_history(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("", response_model=CustomerResponse, status_code=201)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    return customer_crud.create_customer(db, payload)


@router.patch("/{customer_id}", response_model=CustomerResponse)
def update_customer(
    customer_id: str,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    customer = customer_crud.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer_crud.update_customer(db, customer, payload.model_dump(exclude_unset=True))


@router.post("/{customer_id}/notes", response_model=NoteResponse, status_code=201)
def add_note(
    customer_id: str,
    payload: NoteCreate,
    db: Session = Depends(get_db),
    agent: SupportAgent = Depends(get_current_agent),
):
    customer = customer_crud.get_customer(db, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return note_crud.add_note(db, customer_id, author=agent.full_name, body=payload.body)
