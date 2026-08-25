from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.schemas.data_source import DataSourceCreate


def get_data_source(db: Session, data_source_id: str) -> DataSource | None:
    return db.get(DataSource, data_source_id)


def list_data_sources(db: Session) -> list[DataSource]:
    return db.query(DataSource).order_by(DataSource.name).all()


def create_data_source(db: Session, data: DataSourceCreate) -> DataSource:
    data_source = DataSource(**data.model_dump())
    db.add(data_source)
    db.commit()
    db.refresh(data_source)
    return data_source


def mark_synced(db: Session, data_source: DataSource) -> DataSource:
    data_source.sync_status = "healthy"
    data_source.sync_health_pct = 100
    data_source.last_synced_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(data_source)
    return data_source


def delete_data_source(db: Session, data_source: DataSource) -> None:
    db.delete(data_source)
    db.commit()
