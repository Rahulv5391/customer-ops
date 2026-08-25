from pydantic import BaseModel


class TicketVolumePoint(BaseModel):
    date: str
    count: int


class TopIssueCategory(BaseModel):
    category: str
    count: int


class CountResponse(BaseModel):
    count: int


class AnalyticsSummaryResponse(BaseModel):
    ticket_volume_7d: list[TicketVolumePoint]
    avg_resolution_time_hours: float | None = None
    csat_average: float | None = None
    deflection_rate: float | None = None
