from __future__ import annotations

from http import HTTPStatus
from uuid import UUID


class HealthDomainException(Exception):
    code = "HEALTH_DOMAIN_ERROR"
    http_status = HTTPStatus.BAD_REQUEST

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class InvalidHealthStatusError(HealthDomainException):
    code = "INVALID_HEALTH_STATUS"
    http_status = HTTPStatus.UNPROCESSABLE_ENTITY

    def __init__(self, status: str) -> None:
        super().__init__(f"Invalid health status: {status}")
        self.status = status


class InvalidHealthRecordError(HealthDomainException):
    code = "INVALID_HEALTH_RECORD"
    http_status = HTTPStatus.BAD_REQUEST

    def __init__(self, field_name: str, value: object | None = None) -> None:
        message = f"Invalid health record field: {field_name}"
        if value is not None:
            message = f"Invalid health record field: {field_name}, value={value}"
        super().__init__(message)
        self.field_name = field_name
        self.value = value


class HealthNotFoundError(HealthDomainException):
    code = "HEALTH_NOT_FOUND"
    http_status = HTTPStatus.NOT_FOUND

    def __init__(self, health_id: UUID) -> None:
        super().__init__(f"Health record not found for id: {health_id}")
        self.health_id = health_id


class DuplicateHealthRecordError(HealthDomainException):
    code = "DUPLICATE_HEALTH_RECORD"
    http_status = HTTPStatus.CONFLICT

    def __init__(self, service_name: str) -> None:
        super().__init__(f"Health record already exists for service: {service_name}")
        self.service_name = service_name
