from app.sources.arxiv.adapter import ArxivAdapter
from app.sources.base import FetchConfig


def test_arxiv_fixture_parses_expected_document(fixture_dir) -> None:
    adapter = ArxivAdapter()

    documents = adapter.fetch(FetchConfig(fixture_path=fixture_dir / "arxiv_feed.xml"))

    assert len(documents) == 1
    document = documents[0]
    assert document.source_external_id == "2603.01234v1"
    assert document.title == "Accelerant Sparse Runtime"
    assert document.published_at is not None
    assert document.published_at.tzinfo is not None
    assert document.metadata["authors"] == ["Casey Lin", "Priya Desai"]
    assert document.metadata["categories"] == ["cs.LG", "cs.DC"]
