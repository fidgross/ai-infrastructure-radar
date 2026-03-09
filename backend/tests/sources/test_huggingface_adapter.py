from app.sources.base import FetchConfig
from app.sources.huggingface.adapter import HuggingFaceAdapter


def test_huggingface_fixture_parses_model_document(fixture_dir) -> None:
    adapter = HuggingFaceAdapter()

    documents = adapter.fetch(FetchConfig(fixture_path=fixture_dir / "huggingface_models.json"))

    assert len(documents) == 1
    document = documents[0]
    assert document.source_external_id == "tensorforge/tfserve"
    assert document.metadata["pipeline_tag"] == "text-generation"
    assert "speculative decoding" in document.normalized_text.lower()
