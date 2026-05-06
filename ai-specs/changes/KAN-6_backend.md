# Backend Implementation Plan: KAN-6 Python FastAPI Base Application

## 1. Overview
This ticket delivers a base Python FastAPI application template for new backend projects in the OpenSpec platform. The goal is to create a reusable skeleton that follows the projects Clean Architecture and Domain-Driven Design patterns, including layers for Domain, Application, Presentation, and Infrastructure, with async SQLAlchemy, Alembic migrations, DTO validation, and test/CI support.

Active stack: `python-fastapi` (`Python 3.12 + FastAPI`)

## 2. Architecture Context
- Active stack: `python-fastapi` (`Python 3.12 + FastAPI`)
- Layers involved:
  - Domain: models, repositories, exceptions
  - Application: services, DTOs, mappers
  - Presentation: FastAPI routers, dependencies, exception handlers
  - Infrastructure: SQLAlchemy async repository, DB engine, config, Alembic migrations
- Files affected per layer:
  - Domain: `src/domain/models/health.py`, `src/domain/repositories/health_repository.py`, `src/domain/exceptions/health_exceptions.py`
  - Application: `src/application/services/health_service.py`, `src/application/dto/health_dto.py`, `src/application/mappers/health_mapper.py`
  - Presentation: `src/presentation/routers/health_router.py`, `src/presentation/dependencies/health_dependencies.py`, `src/presentation/exception_handlers/global_handlers.py`
  - Infrastructure: `src/infrastructure/repositories/health_repository_impl.py`, `src/infrastructure/database/engine.py`, `src/infrastructure/database/models/health_orm.py`, `src/infrastructure/config/settings.py`
  - Root: `main.py`, `pyproject.toml`, `requirements.txt`, `alembic/env.py`, `alembic/versions/001_initial_health_table.py`, `.env.example`, `README.md`, `Dockerfile`, `docker-compose.yml`
  - Tests: `tests/unit/test_health_service.py`, `tests/integration/test_health_endpoints.py`, `tests/e2e/test_full_health_flow.py`

## 3. Implementation Steps

### Step 0: Create Feature Branch
- Action: create and switch to the feature branch.
- Branch: `feature/KAN-6-backend`
- Commands:
  ```bash
  git checkout main && git pull origin main
  git checkout -b feature/KAN-6-backend
  ```

### Step 1: Configure Base Project Dependencies
- File: `pyproject.toml` and/or `requirements.txt`
- Changes:
  - Add FastAPI, uvicorn, SQLAlchemy[asyncio], psycopg[binary] or psycopg3, alembic, pydantic, pytest, pytest-asyncio, httpx, ruff, mypy
  - Set Python version to 3.12
  - Configure pytest and coverage settings
  - Configure mypy strict and ruff lint settings

### Step 2: Initialize Infrastructure Config
- File: `src/infrastructure/config/settings.py`
- Changes:
  - Add Pydantic `BaseSettings` for `DATABASE_URL`, `APP_NAME`, `APP_VERSION`, `ENVIRONMENT`
  - Load `.env` support if needed
  - Add typed accessors for runtime configuration

### Step 3: Add Async DB Engine and Session Factory
- File: `src/infrastructure/database/engine.py`
- Changes:
  - Create `create_async_engine` with `DATABASE_URL`
  - Define `AsyncSessionLocal` factory
  - Add async dependency for session lifecycle
  - Register SQLAlchemy declarative base if needed

### Step 4: Create SQLAlchemy ORM Model
- File: `src/infrastructure/database/models/health_orm.py`
- Changes:
  - Add `HealthORM` model mapped to table `health`
  - Define columns: `id` (UUID PK), `service_name`, `status`, `timestamp`, `version`, `uptime_seconds`
  - Configure `sqlalchemy.dialects.postgresql.UUID`, `sqlalchemy.DateTime(timezone=True)`, `server_default` or Python assignment for timestamps

### Step 5: Create Domain Model and Repository Interface
- File: `src/domain/models/health.py`
- Changes:
  - Define dataclass/class `Health` with fields: `id`, `service_name`, `status`, `timestamp`, `version`, `uptime_seconds`
  - Add factory method(s): `create`, `update_status`
  - Enforce invariants: valid status enum values, non-empty `service_name`, non-empty `version`

- File: `src/domain/repositories/health_repository.py`
- Changes:
  - Define abstract base class `HealthRepository`
  - Include methods: `find_by_id`, `save`, `delete_by_id`, `list_all`
  - Return domain models, not ORM models

- File: `src/domain/exceptions/health_exceptions.py`
- Changes:
  - Add `HealthDomainException` base class
  - Add `InvalidHealthStatusError`, `HealthNotFoundError`, `DuplicateHealthRecordError` if applicable

### Step 6: Add Application DTOs and Mapper
- File: `src/application/dto/health_dto.py`
- Changes:
  - Define `HealthRequest` with `service_name`, `status`, `version`
  - Define `HealthResponse` with `id`, `service_name`, `status`, `timestamp`, `version`, `uptime_seconds`
  - Add Pydantic validation for `status` enum and required fields

- File: `src/application/mappers/health_mapper.py`
- Changes:
  - Add conversion functions `to_domain` and `to_response`
  - Keep mapping logic simple and deterministic

### Step 7: Implement Health Service Use Cases
- File: `src/application/services/health_service.py`
- Changes:
  - Create `HealthService` with constructor injection of `HealthRepository`
  - Add methods:
    - `async def create(self, dto: HealthRequest) -> HealthResponse`
    - `async def get_by_id(self, id: UUID) -> HealthResponse`
    - `async def update(self, id: UUID, dto: HealthRequest) -> HealthResponse`
    - `async def delete(self, id: UUID) -> None`
    - Optionally `async def list_all(self) -> list[HealthResponse]`
  - Use mapper and domain models
  - Raise domain exceptions for invalid state or missing records

### Step 8: Add FastAPI Router and Dependencies
- File: `src/presentation/routers/health_router.py`
- Changes:
  - Define `APIRouter(prefix="/api/v1/health", tags=["Health"])`
  - Implement endpoints:
    - `GET /` -> list or current health record(s)
    - `GET /{id}` -> get specific health record
    - `POST /` -> create health record, return `201`
    - `PUT /{id}` -> update record, return `200`
    - `DELETE /{id}` -> delete record, return `204`
  - Use response_model on endpoints

- File: `src/presentation/dependencies/health_dependencies.py`
- Changes:
  - Create `get_health_repository` dependency returning configured repository implementation
  - Create `get_health_service` dependency injecting repository into service
  - Keep lifecycle management explicit and async

### Step 9: Add Global Exception Handlers
- File: `src/presentation/exception_handlers/global_handlers.py`
- Changes:
  - Add handler for `HealthDomainException` or generic `DomainException`
  - Add handler for `RequestValidationError`
  - Add handler for `HTTPException` if custom payload required
  - Return structured JSON:
    ```json
    {
      "success": false,
      "code": "ERROR_CODE",
      "message": "Human-readable description",
      "details": ["field: validation message"]
    }
    ```
  - Map statuses: `400`, `404`, `409`, `422`, `500`

### Step 10: Create App Factory and Router Registration
- File: `main.py`
- Changes:
  - Create FastAPI app instance with title, version, docs URLs
  - Include router registration for health router
  - Register global exception handlers
  - Optionally add startup/shutdown events for DB connection

### Step 11: Add Alembic Migrations
- File: `alembic/env.py`
- Changes:
  - Configure Alembic to use SQLAlchemy async engine and metadata from infrastructure models
  - Ensure `run_migrations_online` uses async DB URL

- File: `alembic/versions/001_initial_health_table.py`
- Changes:
  - Create initial migration for `health` table with correct columns and types
  - Use `postgresql.UUID`, `TIMESTAMP(timezone=True)`, `INTEGER`, `VARCHAR` columns

### Step 12: Create Test Suite
- Files:
  - `tests/unit/test_health_service.py`
  - `tests/integration/test_health_endpoints.py`
  - `tests/e2e/test_full_health_flow.py`
- Changes:
  - Unit tests with mocked repository for service methods and domain logic
  - Integration tests with `httpx.AsyncClient` against FastAPI app
  - E2E tests verifying full request-to-DB path using test DB (Docker Compose optional)
- Cases to cover:
  - `test_should_create_health_record_when_request_is_valid`
  - `test_should_return_health_response_when_record_exists`
  - `test_should_update_health_record_when_payload_is_valid`
  - `test_should_delete_health_record_when_id_exists`
  - `test_should_return_404_when_health_id_not_found`
  - `test_should_return_422_when_request_payload_is_invalid`
  - `test_should_raise_domain_exception_for_invalid_status`

### Step 13: Add Documentation and API Contract
- File: `README.md`
  - Add setup instructions, how to run locally, how to run tests, how to apply migrations, how to use the health endpoints
- File: `ai-specs/specs/development_guide.md`
  - Add Python/FastAPI section with commands and environment variables
- File: `ai-specs/specs/api-spec.yml`
  - Add OpenAPI contract definitions for health endpoints if applicable
- File: `ai-specs/changes/KAN-6_backend.md`
  - Save this implementation plan as the developer handoff reference

## 4. Implementation Order
1. Step 0: Create feature branch
2. Step 1: Configure base project dependencies
3. Step 2: Initialize infrastructure config
4. Step 3: Add async DB engine and session factory
5. Step 4: Create SQLAlchemy ORM model
6. Step 5: Create domain model and repository interface
7. Step 6: Add application DTOs and mapper
8. Step 7: Implement health service use cases
9. Step 8: Add FastAPI router and dependencies
10. Step 9: Add global exception handlers
11. Step 10: Create app factory and router registration
12. Step 11: Add Alembic migrations
13. Step 12: Create test suite
14. Step 13: Add documentation and API contract

## 5. Testing Checklist
- [ ] `pytest` passes with 0 failures
- [ ] `pytest --cov --cov-report=html` reports >= 90% coverage
- [ ] All new endpoints are manually tested for happy path and error cases
- [ ] Existing tests are not broken
- [ ] `ruff check .` passes
- [ ] `mypy src/` passes

## 6. Tooling Reference
Commands resolved from `openspec/config.yaml` for the active stack:

| Purpose | Command |
|---|---|
| Build | `pip install -r requirements.txt` |
| Test | `pytest` |
| Run | `uvicorn main:app --reload` |
| Coverage | `pytest --cov --cov-report=html` |

## 7. Error Response Format
```json
{
  "success": false,
  "code": "ERROR_CODE",
  "message": "Human-readable description",
  "details": ["field: validation message"]
}
```
HTTP mapping:
- `400` VALIDATION_ERROR
- `404` NOT_FOUND
- `409` CONFLICT
- `422` BUSINESS_RULE_VIOLATION
- `500` INTERNAL_ERROR

## 8. Dependencies
New libraries or tools required for this active stack:
- FastAPI
- uvicorn
- SQLAlchemy[asyncio]
- psycopg[binary] or psycopg3
- alembic
- pydantic v2
- pytest
- pytest-asyncio
- httpx
- ruff
- mypy

## 9. Notes
- Use domain models and repository interfaces to keep business logic decoupled from ORM.
- Do not import SQLAlchemy or FastAPI in domain/application layers.
- Use Alembic for schema changes, never `Base.metadata.create_all()` for production migration behavior.
- Keep code and docs in English.
- Configure `APP_VERSION` and `ENVIRONMENT` for runtime settings.
- Start with a health domain as a minimal proof-of-concept, then evolve the template.

## 10. Implementation Verification Checklist
- [ ] Code quality: no type or linting errors
- [ ] Domain: invariants enforced via factory methods
- [ ] Application: services use DTOs and repository interfaces only
- [ ] Presentation: handlers are thin, use dependencies and validation
- [ ] Migrations: migration script created and tested with Alembic
- [ ] Tests: all tests green, coverage >= 90%
- [ ] Documentation: README, development guide, and API spec updated
