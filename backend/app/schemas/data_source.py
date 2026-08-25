from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DataSourceBase(BaseModel):
    name: str
    connector_type: str


class DataSourceCreate(DataSourceBase):
    pass


class DataSourceResponse(DataSourceBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    sync_status: str
    sync_health_pct: int
    tables_schema: str
    sync_logs: str
    last_synced_at: datetime | None = None
