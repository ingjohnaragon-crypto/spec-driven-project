from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from src.domain.exceptions.health_exceptions import InvalidHealthRecordError, HealthNotFoundError


class HealthStatus(str, Enum):
    healthy = "healthy"
    degraded = "degraded"
    unhealthy = "unhealthy"


@dataclass
class Health:
    id: UUID | None
    service_name: str
    status: HealthStatus
    timestamp: datetime
    version: str
    uptime_seconds: int

    @classmethod
    def create(
        cls,
        service_name: str,
        status: HealthStatus,
        version: str,
        uptime_seconds: int,
        id: UUID | None = None,
    ) -> "Health":
        if not service_name or not service_name.strip():
            raise InvalidHealthRecordError("service_name", service_name)

        if not version or not version.strip():
            raise InvalidHealthRecordError("version", version)

        if uptime_seconds < 0:
            raise InvalidHealthRecordError("uptime_seconds", uptime_seconds)

        return cls(
            id=id or uuid4(),
            service_name=service_name.strip(),
            status=status,
            timestamp=datetime.now(timezone.utc),
            version=version.strip(),
            uptime_seconds=uptime_seconds,
        )

    def update(
        self,
        service_name: str,
        status: HealthStatus,
        version: str,
        uptime_seconds: int,
    ) -> "Health":
        if not service_name or not service_name.strip():
            raise InvalidHealthRecordError("service_name", service_name)

        if not version or not version.strip():
            raise InvalidHealthRecordError("version", version)

        if uptime_seconds < 0:
            raise InvalidHealthRecordError("uptime_seconds", uptime_seconds)

        return Health(
            id=self.id,
            service_name=service_name.strip(),
            status=status,
            timestamp=datetime.now(timezone.utc),
            version=version.strip(),
            uptime_seconds=uptime_seconds,
        )
