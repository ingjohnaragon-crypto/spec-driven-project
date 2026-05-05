from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.domain.models.health import HealthStatus


class HealthRequest(BaseModel):
    service_name: str
    status: HealthStatus
    version: str

    model_config = ConfigDict(extra="forbid")


class HealthResponse(BaseModel):
    id: UUID
    service_name: str
    status: HealthStatus
    timestamp: datetime
    version: str
    uptime_seconds: int

    model_config = ConfigDict(from_attributes=True)
