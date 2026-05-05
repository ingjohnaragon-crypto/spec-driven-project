from __future__ import annotations

from uuid import UUID

from src.application.dto.health_dto import HealthRequest, HealthResponse
from src.domain.models.health import Health


class HealthMapper:
    @staticmethod
    def to_domain(dto: HealthRequest, uptime_seconds: int, id: UUID | None = None) -> Health:
        return Health.create(
            id=id,
            service_name=dto.service_name,
            status=dto.status,
            version=dto.version,
            uptime_seconds=uptime_seconds,
        )

    @staticmethod
    def to_response(health: Health) -> HealthResponse:
        return HealthResponse(
            id=health.id,
            service_name=health.service_name,
            status=health.status,
            timestamp=health.timestamp,
            version=health.version,
            uptime_seconds=health.uptime_seconds,
        )
