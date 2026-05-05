from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from uuid import UUID

from src.application.dto.health_dto import HealthRequest, HealthResponse
from src.application.services.health_service import HealthService
from src.presentation.dependencies.health_dependencies import get_health_service

router = APIRouter(prefix="/api/v1/health", tags=["Health"])


@router.get("/", response_model=list[HealthResponse])
async def list_health(service: HealthService = Depends(get_health_service)) -> list[HealthResponse]:
    return await service.list_all()


@router.get("/{id}", response_model=HealthResponse)
async def get_health(id: UUID, service: HealthService = Depends(get_health_service)) -> HealthResponse:
    return await service.get_by_id(id)


@router.post("/", response_model=HealthResponse, status_code=status.HTTP_201_CREATED)
async def create_health(
    request: HealthRequest,
    service: HealthService = Depends(get_health_service),
) -> HealthResponse:
    return await service.create(request)


@router.put("/{id}", response_model=HealthResponse)
async def update_health(
    id: UUID,
    request: HealthRequest,
    service: HealthService = Depends(get_health_service),
) -> HealthResponse:
    return await service.update(id, request)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_health(id: UUID, service: HealthService = Depends(get_health_service)) -> Response:
    await service.delete(id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
