from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

from src.infrastructure.database.engine import Base


class HealthORM(Base):
    __tablename__ = "health"

    id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid4)
    service_name = Column(String(255), nullable=False)
    status = Column(String(50), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    version = Column(String(50), nullable=False)
    uptime_seconds = Column(Integer, nullable=False)
