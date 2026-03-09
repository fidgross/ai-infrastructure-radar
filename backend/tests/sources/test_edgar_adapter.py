from app.sources.base import FetchConfig
from app.sources.edgar.adapter import EdgarAdapter


def test_edgar_fixture_parses_submission_document(fixture_dir) -> None:
    adapter = EdgarAdapter()

    documents = adapter.fetch(FetchConfig(fixture_path=fixture_dir / "edgar_submissions.json"))

    assert len(documents) == 1
    document = documents[0]
    assert document.source_external_id == "0001234567-26-000010"
    assert document.metadata["form"] == "10-K"
    assert "gpu capacity expansion" in document.normalized_text.lower()
    assert document.url.endswith("/skybridge-10k.htm")
