from __future__ import annotations

from datetime import datetime, timezone
from fastapi import Depends

from src.application.services.health_service import HealthService
from src.infrastructure.database.engine import get_async_session
from src.infrastructure.repositories.health_repository_impl import HealthRepositoryImpl

APP_START_TIME = datetime.now(timezone.utc)


def get_health_repository(session=Depends(get_async_session)) -> HealthRepositoryImpl:
    return HealthRepositoryImpl(session=session)


def get_health_service(repository: HealthRepositoryImpl = Depends(get_health_repository)) -> HealthService:
    return HealthService(repository=repository, app_start_time=APP_START_TIME)
