from collections.abc import Generator

from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.schemas.api import OperationsStatusResponse


def override_session() -> Generator[None, None, None]:
    yield None


def test_add_watchlist_item_rejects_invalid_uuid() -> None:
    app.dependency_overrides[get_db_session] = override_session
    client = TestClient(app)

    response = client.post(
        "/api/watchlists/not-a-uuid/items",
        json={"entity_slug": "nvidia"},
    )

    app.dependency_overrides.clear()
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid watchlist_id."


def test_operations_status_route(monkeypatch) -> None:
    sample = OperationsStatusResponse(
        overall_status="ok",
        ingest_runs=[],
        pending_normalization_count=0,
        latest_event_scored_at=None,
        latest_entity_scored_at=None,
        latest_brief_date=None,
        latest_brief_updated_at=None,
        stale_reasons=[],
    )

    monkeypatch.setattr("app.api.routes.operations.get_operations_status", lambda _session: sample)
    app.dependency_overrides[get_db_session] = override_session
    client = TestClient(app)

    response = client.get("/api/operations/status")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == sample.model_dump(mode="json")
