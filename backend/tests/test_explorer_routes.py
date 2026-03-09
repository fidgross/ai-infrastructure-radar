from collections.abc import Generator

from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app


def override_session() -> Generator[None, None, None]:
    yield None


def test_event_detail_rejects_invalid_uuid() -> None:
    app.dependency_overrides[get_db_session] = override_session
    client = TestClient(app)

    response = client.get("/api/events/not-a-uuid")

    app.dependency_overrides.clear()
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid event_id."
