from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import data_source as data_source_crud
from app.models.agent import SupportAgent
from app.schemas.data_source import DataSourceResponse
from app.services.auth_service import get_current_agent, require_team_lead

router = APIRouter(prefix="/data-sources", tags=["data-sources"])


@router.get("", response_model=list[DataSourceResponse])
def list_data_sources(
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    return data_source_crud.list_data_sources(db)


@router.get("/{data_source_id}", response_model=DataSourceResponse)
def get_data_source(
    data_source_id: str,
    db: Session = Depends(get_db),
    _agent: SupportAgent = Depends(get_current_agent),
):
    data_source = data_source_crud.get_data_source(db, data_source_id)
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return data_source


@router.post("/{data_source_id}/sync", response_model=DataSourceResponse)
def sync_data_source(
    data_source_id: str,
    db: Session = Depends(get_db),
    _lead: SupportAgent = Depends(require_team_lead),
):
    data_source = data_source_crud.get_data_source(db, data_source_id)
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    return data_source_crud.mark_synced(db, data_source)


@router.delete("/{data_source_id}", status_code=204)
def delete_data_source(
    data_source_id: str,
    db: Session = Depends(get_db),
    _lead: SupportAgent = Depends(require_team_lead),
):
    data_source = data_source_crud.get_data_source(db, data_source_id)
    if not data_source:
        raise HTTPException(status_code=404, detail="Data source not found")
    data_source_crud.delete_data_source(db, data_source)
