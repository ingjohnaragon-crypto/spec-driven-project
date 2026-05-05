from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from src.domain.models.health import Health


class HealthRepository(ABC):
    @abstractmethod
    async def find_by_id(self, id: UUID) -> Health | None:
        ...

    @abstractmethod
    async def list_all(self) -> List[Health]:
        ...

    @abstractmethod
    async def save(self, health: Health) -> Health:
        ...

    @abstractmethod
    async def delete_by_id(self, id: UUID) -> None:
        ...
