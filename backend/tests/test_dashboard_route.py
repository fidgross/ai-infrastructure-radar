from collections.abc import Generator

from fastapi.testclient import TestClient

from app.db.session import get_db_session
from app.main import app
from app.schemas.dashboard import DashboardSummaryResponse


def override_session() -> Generator[None, None, None]:
    yield None


def test_dashboard_summary(monkeypatch) -> None:
    sample = DashboardSummaryResponse(
        top_events=[],
        emerging_entities=[],
        theme_heatmap=[],
        opportunities=[],
        latest_brief=None,
    )

    monkeypatch.setattr("app.api.routes.dashboard.get_dashboard_summary", lambda _session: sample)
    app.dependency_overrides[get_db_session] = override_session
    client = TestClient(app)

    response = client.get("/api/dashboard/summary")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == sample.model_dump(mode="json")
