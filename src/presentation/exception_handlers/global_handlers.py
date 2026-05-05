from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.domain.exceptions.health_exceptions import HealthDomainException


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(HealthDomainException)
    async def health_domain_exception_handler(request: Request, exc: HealthDomainException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.http_status,
            content={
                "success": False,
                "code": exc.code,
                "message": exc.message,
                "details": [],
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "success": False,
                "code": "VALIDATION_ERROR",
                "message": "Validation failed",
                "details": exc.errors(),
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "code": "HTTP_EXCEPTION",
                "message": exc.detail,
                "details": [],
            },
        )
