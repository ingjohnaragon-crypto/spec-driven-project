from __future__ import annotations

from httpx import ASGITransport, AsyncClient
import pytest

from main import app


@pytest.mark.asyncio
async def test_should_run_full_health_flow() -> None:
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

        update_response = await client.put(
            f"/api/v1/health/{created['id']}",
            json={"service_name": "open-spec-base-app", "status": "degraded", "version": "1.0.1"},
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "degraded"

        delete_response = await client.delete(f"/api/v1/health/{created['id']}")
        assert delete_response.status_code == 204

        get_response = await client.get(f"/api/v1/health/{created['id']}")
        assert get_response.status_code == 404
