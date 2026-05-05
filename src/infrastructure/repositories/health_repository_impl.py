from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from src.domain.models.health import Health, HealthStatus
from src.domain.repositories.health_repository import HealthRepository
from src.infrastructure.database.models.health_orm import HealthORM


class HealthRepositoryImpl(HealthRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find_by_id(self, id: UUID) -> Health | None:
        orm = await self._session.get(HealthORM, id)
        if orm is None:
            return None
        return self._to_domain(orm)

    async def list_all(self) -> list[Health]:
        result = await self._session.execute(select(HealthORM))
        return [self._to_domain(row[0]) for row in result.fetchall()]

    async def save(self, health: Health) -> Health:
        existing = await self._session.get(HealthORM, health.id)
        if existing is None:
            orm = HealthORM(
                id=health.id,
                service_name=health.service_name,
                status=health.status.value,
                timestamp=health.timestamp,
                version=health.version,
                uptime_seconds=health.uptime_seconds,
            )
            self._session.add(orm)
            await self._session.commit()
            await self._session.refresh(orm)
            return self._to_domain(orm)

        existing.service_name = health.service_name
        existing.status = health.status.value
        existing.timestamp = health.timestamp
        existing.version = health.version
        existing.uptime_seconds = health.uptime_seconds
        await self._session.commit()
        await self._session.refresh(existing)
        return self._to_domain(existing)

    async def delete_by_id(self, id: UUID) -> None:
        orm = await self._session.get(HealthORM, id)
        if orm is None:
            return
        await self._session.delete(orm)
        await self._session.commit()

    @staticmethod
    def _to_domain(orm: HealthORM) -> Health:
        return Health(
            id=orm.id,
            service_name=orm.service_name,
            status=HealthStatus(orm.status),
            timestamp=orm.timestamp,
            version=orm.version,
            uptime_seconds=orm.uptime_seconds,
        )
