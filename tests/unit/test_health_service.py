from __future__ import annotations

from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from src.application.dto.health_dto import HealthRequest
from src.application.services.health_service import HealthService
from src.domain.exceptions.health_exceptions import (
    DuplicateHealthRecordError,
    HealthNotFoundError,
    InvalidHealthRecordError,
    InvalidHealthStatusError,
)
from src.domain.models.health import Health, HealthStatus
from src.domain.repositories.health_repository import HealthRepository


@pytest.mark.asyncio
async def test_should_create_health_record_when_request_is_valid() -> None:
    repository = AsyncMock(spec=HealthRepository)
    start_time = datetime.now(timezone.utc) - timedelta(seconds=20)
    service = HealthService(repository, app_start_time=start_time)

    request = HealthRequest(
        service_name="open-spec-base-app",
        status=HealthStatus.healthy,
        version="1.0.0",
    )

    expected_health = Health.create(
        service_name=request.service_name,
        status=request.status,
        version=request.version,
        uptime_seconds=10,
    )
    repository.save.return_value = expected_health

    response = await service.create(request)

    repository.save.assert_awaited_once()
    assert response.service_name == expected_health.service_name
    assert response.status == expected_health.status
    assert response.version == expected_health.version
    assert response.uptime_seconds >= 0


def test_should_raise_invalid_health_record_error_when_service_name_is_blank() -> None:
    with pytest.raises(InvalidHealthRecordError) as exc_info:
        Health.create(
            service_name="  ",
            status=HealthStatus.healthy,
            version="1.0.0",
            uptime_seconds=10,
        )

    assert exc_info.value.field_name == "service_name"


def test_should_raise_invalid_health_record_error_when_version_is_blank() -> None:
    with pytest.raises(InvalidHealthRecordError) as exc_info:
        Health.create(
            service_name="open-spec-base-app",
            status=HealthStatus.healthy,
            version="",
            uptime_seconds=10,
        )

    assert exc_info.value.field_name == "version"


def test_should_raise_invalid_health_record_error_when_uptime_is_negative() -> None:
    with pytest.raises(InvalidHealthRecordError) as exc_info:
        Health.create(
            service_name="open-spec-base-app",
            status=HealthStatus.healthy,
            version="1.0.0",
            uptime_seconds=-1,
        )

    assert exc_info.value.field_name == "uptime_seconds"


@pytest.mark.asyncio
async def test_should_raise_not_found_when_get_by_id_does_not_exist() -> None:
    repository = AsyncMock(spec=HealthRepository)
    repository.find_by_id.return_value = None
    start_time = datetime.now(timezone.utc)
    service = HealthService(repository, app_start_time=start_time)

    with pytest.raises(HealthNotFoundError):
        await service.get_by_id(uuid4())


@pytest.mark.asyncio
async def test_should_update_health_record_when_it_exists() -> None:
    repository = AsyncMock(spec=HealthRepository)
    start_time = datetime.now(timezone.utc) - timedelta(seconds=10)
    existing = Health.create(
        service_name="open-spec-base-app",
        status=HealthStatus.healthy,
        version="1.0.0",
        uptime_seconds=10,
    )
    service = HealthService(repository, app_start_time=start_time)

    repository.find_by_id.return_value = existing
    repository.save.return_value = existing.update(
        service_name=existing.service_name,
        status=HealthStatus.degraded,
        version="1.0.1",
        uptime_seconds=20,
    )

    request = HealthRequest(
        service_name="open-spec-base-app",
        status=HealthStatus.degraded,
        version="1.0.1",
    )

    response = await service.update(existing.id, request)

    repository.find_by_id.assert_awaited_once_with(existing.id)
    repository.save.assert_awaited_once()
    assert response.status == HealthStatus.degraded
    assert response.version == "1.0.1"


def test_should_raise_invalid_health_status_error() -> None:
    with pytest.raises(InvalidHealthStatusError) as exc_info:
        raise InvalidHealthStatusError("invalid-status")

    assert exc_info.value.status == "invalid-status"
    assert exc_info.value.code == "INVALID_HEALTH_STATUS"


def test_should_raise_duplicate_health_record_error() -> None:
    with pytest.raises(DuplicateHealthRecordError) as exc_info:
        raise DuplicateHealthRecordError("open-spec-base-app")

    assert exc_info.value.service_name == "open-spec-base-app"
    assert exc_info.value.code == "DUPLICATE_HEALTH_RECORD"
