from __future__ import annotations

from httpx import ASGITransport, AsyncClient
import pytest

from main import app


@pytest.mark.asyncio
async def test_should_return_empty_health_list_when_no_records_exist() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_should_create_and_retrieve_health_record() -> None:
    body = {
        "service_name": "open-spec-base-app",
        "status": "healthy",
        "version": "1.0.0",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        create_response = await client.post("/api/v1/health/", json=body)
        assert create_response.status_code == 201
        created = create_response.json()
        assert created["service_name"] == "open-spec-base-app"
        assert created["status"] == "healthy"
        assert created["version"] == "1.0.0"
        assert created["uptime_seconds"] >= 0

        get_response = await client.get(f"/api/v1/health/{created['id']}")
        assert get_response.status_code == 200
        assert get_response.json()["id"] == created["id"]

        update_response = await client.put(
            f"/api/v1/health/{created['id']}",
            json={
                "service_name": "open-spec-base-app",
                "status": "degraded",
                "version": "1.0.1",
            },
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["status"] == "degraded"
        assert updated["version"] == "1.0.1"


@pytest.mark.asyncio
async def test_should_return_422_for_invalid_health_request() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/health/",
            json={"service_name": "open-spec-base-app", "status": "unknown", "version": "1.0.0"},
        )

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "VALIDATION_ERROR"
    assert body["success"] is False
@pytest.mark.asyncio
async def test_should_return_404_when_getting_nonexistent_health_record() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/api/v1/health/99999")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_should_return_404_when_updating_nonexistent_health_record() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.put(
            "/api/v1/health/99999",
            json={"service_name": "x", "status": "healthy", "version": "1.0.0"},
        )
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_should_return_404_when_deleting_nonexistent_health_record() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.delete("/api/v1/health/99999")
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["code"] == "NOT_FOUND"


@pytest.mark.asyncio
async def test_should_delete_existing_health_record() -> None:
    body = {"service_name": "delete-test", "status": "healthy", "version": "1.0.0"}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        create = await client.post("/api/v1/health/", json=body)
        assert create.status_code == 201
        record_id = create.json()["id"]
        delete = await client.delete(f"/api/v1/health/{record_id}")
        assert delete.status_code == 204
        get = await client.get(f"/api/v1/health/{record_id}")
        assert get.status_code == 404
