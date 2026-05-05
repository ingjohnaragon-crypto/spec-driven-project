# OpenSpec Python FastAPI Base Application

This repository contains a base Python FastAPI template for OpenSpec backend projects. It follows Clean Architecture and DDD principles with async PostgreSQL persistence, Alembic migrations, Pydantic validation, and a minimal health domain example.

## Getting Started

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run locally

```bash
uvicorn main:app --reload
```

### API docs

- Swagger: `http://localhost:8000/docs`
- Redoc: `http://localhost:8000/redoc`

## Health Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/health/` | List all health records |
| GET | `/api/v1/health/{id}` | Retrieve a health record by ID |
| POST | `/api/v1/health/` | Create a health record |
| PUT | `/api/v1/health/{id}` | Update a health record |
| DELETE | `/api/v1/health/{id}` | Delete a health record |

## Database

The application uses async SQLAlchemy with PostgreSQL.

### Local environment variables

Copy the example file:

```bash
cp .env.example .env
```

Update `.env` with your PostgreSQL connection string:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/openspec
APP_NAME=open-spec-base-app
APP_VERSION=0.1.0
ENVIRONMENT=development
```

### Run migrations

```bash
alembic upgrade head
```

## Testing

```bash
pytest
```

## Linting and type checking

```bash
ruff check .
mypy src
```

## Docker

Start the application and PostgreSQL locally:

```bash
docker-compose up --build
```

## Architecture

```
src/
├── application/
├── domain/
├── infrastructure/
└── presentation/
```

## Notes

- Domain logic is isolated in `src/domain`
- SQLAlchemy models and repository implementations live in `src/infrastructure`
- FastAPI routes and exception handlers are in `src/presentation`
- DTO validation occurs in `src/application`
