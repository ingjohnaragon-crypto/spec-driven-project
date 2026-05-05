from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from src.application.dto.health_dto import HealthRequest, HealthResponse
from src.application.mappers.health_mapper import HealthMapper
from src.domain.exceptions.health_exceptions import HealthNotFoundError
from src.domain.models.health import HealthStatus
from src.domain.repositories.health_repository import HealthRepository


class HealthService:
    def __init__(self, repository: HealthRepository, app_start_time: datetime) -> None:
        self._repository = repository
        self._app_start_time = app_start_time

    async def create(self, dto: HealthRequest) -> HealthResponse:
        uptime_seconds = self._calculate_uptime_seconds()
        health = HealthMapper.to_domain(dto, uptime_seconds)
        saved_health = await self._repository.save(health)
        return HealthMapper.to_response(saved_health)

    async def get_by_id(self, id: UUID) -> HealthResponse:
        health = await self._repository.find_by_id(id)
        if health is None:
            raise HealthNotFoundError(id)
        return HealthMapper.to_response(health)

    async def list_all(self) -> list[HealthResponse]:
        health_records = await self._repository.list_all()
        return [HealthMapper.to_response(record) for record in health_records]

    async def update(self, id: UUID, dto: HealthRequest) -> HealthResponse:
        existing = await self._repository.find_by_id(id)
        if existing is None:
            raise HealthNotFoundError(id)

        uptime_seconds = self._calculate_uptime_seconds()
        updated_health = existing.update(
            service_name=dto.service_name,
            status=dto.status,
            version=dto.version,
            uptime_seconds=uptime_seconds,
        )
        saved_health = await self._repository.save(updated_health)
        return HealthMapper.to_response(saved_health)

    async def delete(self, id: UUID) -> None:
        existing = await self._repository.find_by_id(id)
        if existing is None:
            raise HealthNotFoundError(id)
        await self._repository.delete_by_id(id)

    def _calculate_uptime_seconds(self) -> int:
        return int((datetime.now(timezone.utc) - self._app_start_time).total_seconds())
