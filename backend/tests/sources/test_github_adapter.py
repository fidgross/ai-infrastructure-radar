from app.sources.base import FetchConfig
from app.sources.github.adapter import GitHubAdapter


def test_github_fixture_parses_release_document(fixture_dir) -> None:
    adapter = GitHubAdapter()

    documents = adapter.fetch(FetchConfig(fixture_path=fixture_dir / "github_releases.json"))

    assert len(documents) == 1
    document = documents[0]
    assert document.source_external_id == "example/fluxrouter:v0.9.0"
    assert document.title == "FluxRouter v0.9.0"
    assert "policy routing" in document.normalized_text.lower()
    assert document.metadata["repo_name"] == "example/fluxrouter"
