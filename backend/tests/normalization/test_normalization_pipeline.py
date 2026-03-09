import pytest
from sqlalchemy import select

from app.models import Entity, EntityThemeLink, Event, SourceDocument, Theme
from app.services.ingestion import persist_ingestion_run
from app.services.normalization_types import ThemeMatch
from app.services.normalization import normalize_pending_documents
from app.sources.base import FetchConfig
from app.sources.registry import build_adapter
from app.services.theme_tagging import attach_themes_to_entity


@pytest.mark.parametrize(
    ("source_type", "fixture_name", "expected_event_type", "expected_entity_type", "expected_theme_slug"),
    [
        ("arxiv", "arxiv_feed.xml", "paper_published", "paper", "inference-economics"),
        ("github", "github_releases.json", "major_release", "repository", "model-portability"),
        ("huggingface", "huggingface_models.json", "product_launch", "product", "inference-economics"),
        ("edgar", "edgar_submissions.json", "capex_signal", "public_company", "ai-capex-signals"),
    ],
)
def test_normalization_creates_entities_events_and_themes(
    session,
    fixture_dir,
    source_type,
    fixture_name,
    expected_event_type,
    expected_entity_type,
    expected_theme_slug,
) -> None:
    adapter = build_adapter(source_type)
    documents = adapter.fetch(FetchConfig(fixture_path=fixture_dir / fixture_name))
    persist_ingestion_run(session, source_type=source_type, documents=documents, run_metadata={"fixture": True})

    summaries = normalize_pending_documents(session, limit=10)

    assert len(summaries) == 1
    source_document = session.scalar(select(SourceDocument))
    event = session.scalar(select(Event).where(Event.source_document_id == source_document.id))
    entity_types = set(session.scalars(select(Entity.entity_type)).all())
    theme_slugs = set(session.scalars(select(Theme.slug)).all())

    assert event is not None
    assert event.event_type == expected_event_type
    assert expected_entity_type in entity_types
    assert expected_theme_slug in theme_slugs
    assert expected_theme_slug in event.metadata_json["theme_slugs"]
    assert source_document.normalized_at is not None
    assert source_document.normalization_version is not None


def test_arxiv_normalization_creates_author_entities(session, fixture_dir) -> None:
    adapter = build_adapter("arxiv")
    documents = adapter.fetch(FetchConfig(fixture_path=fixture_dir / "arxiv_feed.xml"))
    persist_ingestion_run(session, source_type="arxiv", documents=documents, run_metadata={"fixture": True})

    normalize_pending_documents(session, limit=10)

    people = session.scalars(select(Entity).where(Entity.entity_type == "person")).all()
    assert len(people) == 2


def test_attach_themes_to_entity_is_idempotent_with_autoflush_disabled(session) -> None:
    entity = Entity(
        entity_type="company",
        canonical_name="TensorForge",
        slug="tensorforge",
        metadata_json={},
    )
    theme = Theme(
        name="Inference Economics",
        slug="inference-economics",
        description="Cost and throughput shifts that materially alter inference deployment choices.",
        metadata_json={},
    )
    session.add_all([entity, theme])
    session.flush()

    match = ThemeMatch(
        name=theme.name,
        slug=theme.slug,
        description=theme.description or "",
        stack_layer="Training and inference systems",
        confidence=0.7,
        rationale="Matched keywords: inference",
    )

    attach_themes_to_entity(session, entity, [match], [theme])
    attach_themes_to_entity(session, entity, [match], [theme])
    session.flush()

    links = session.scalars(select(EntityThemeLink).where(EntityThemeLink.entity_id == entity.id)).all()
    assert len(links) == 1
    assert links[0].confidence == 0.7
