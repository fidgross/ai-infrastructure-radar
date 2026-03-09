from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from slugify import slugify
from sqlalchemy import select

from app.db.session import SessionLocal
from app.models import (
    DailyBrief,
    DailyBriefItem,
    Entity,
    EntityAlias,
    EntityScore,
    EntityThemeLink,
    Event,
    EventEntityLink,
    EventScore,
    IngestionRun,
    Opportunity,
    OpportunityEventLink,
    SourceDocument,
    SourcePayload,
    Theme,
    Watchlist,
    WatchlistItem,
)

SCORING_VERSION = "v1_seed"


def get_or_create_theme(session, *, name: str, description: str) -> Theme:
    slug = slugify(name)
    theme = session.scalar(select(Theme).where(Theme.slug == slug))
    if theme is None:
        theme = Theme(name=name, slug=slug, description=description)
        session.add(theme)
        session.flush()
    else:
        theme.name = name
        theme.description = description
    return theme


def get_or_create_entity(session, *, entity_type: str, canonical_name: str, website: str, description: str) -> Entity:
    slug = slugify(canonical_name)
    entity = session.scalar(select(Entity).where(Entity.slug == slug))
    if entity is None:
        entity = Entity(
            entity_type=entity_type,
            canonical_name=canonical_name,
            slug=slug,
            website=website,
            description=description,
        )
        session.add(entity)
        session.flush()
        session.add(EntityAlias(entity_id=entity.id, alias=canonical_name, confidence=1.0, is_manual=True))
    else:
        entity.entity_type = entity_type
        entity.canonical_name = canonical_name
        entity.website = website
        entity.description = description
    return entity


def attach_theme(session, *, entity: Entity, theme: Theme, confidence: float = 0.9) -> None:
    existing = session.scalar(
        select(EntityThemeLink).where(EntityThemeLink.entity_id == entity.id, EntityThemeLink.theme_id == theme.id)
    )
    if existing is None:
        session.add(EntityThemeLink(entity_id=entity.id, theme_id=theme.id, confidence=confidence))


def get_or_create_run(session, *, source_type: str) -> IngestionRun:
    run = session.scalar(select(IngestionRun).where(IngestionRun.source_type == source_type))
    if run is None:
        run = IngestionRun(
            source_type=source_type,
            status="success",
            started_at=datetime.now(timezone.utc) - timedelta(minutes=10),
            finished_at=datetime.now(timezone.utc) - timedelta(minutes=5),
            documents_seen=1,
            documents_created=1,
            metadata_json={"seeded": True},
        )
        session.add(run)
        session.flush()
    return run


def get_or_create_source_document(
    session,
    *,
    source_type: str,
    source_external_id: str,
    title: str,
    url: str,
    raw_text: str,
    normalized_text: str,
    published_at: datetime,
) -> SourceDocument:
    fingerprint = f"{source_type}:{source_external_id}"
    document = session.scalar(select(SourceDocument).where(SourceDocument.fingerprint == fingerprint))
    run = get_or_create_run(session, source_type=source_type)
    if document is None:
        document = SourceDocument(
            ingestion_run_id=run.id,
            source_type=source_type,
            source_external_id=source_external_id,
            title=title,
            url=url,
            raw_text=raw_text,
            normalized_text=normalized_text,
            normalized_at=datetime.now(timezone.utc),
            normalization_version="v1_seed",
            published_at=published_at,
            detected_at=datetime.now(timezone.utc),
            fingerprint=fingerprint,
            metadata_json={"seeded": True},
        )
        session.add(document)
        session.flush()
        session.add(
            SourcePayload(
                ingestion_run_id=run.id,
                source_document_id=document.id,
                source_type=source_type,
                payload_hash=f"{fingerprint}:payload",
                payload_json={"seeded": True, "source_external_id": source_external_id},
            )
        )
    else:
        document.title = title
        document.url = url
        document.raw_text = raw_text
        document.normalized_text = normalized_text
        document.normalized_at = datetime.now(timezone.utc)
        document.normalization_version = "v1_seed"
        document.published_at = published_at
    return document


def get_or_create_event(
    session,
    *,
    title: str,
    event_type: str,
    source_document: SourceDocument,
    summary: str,
    why_it_matters: str,
    skeptical_note: str,
    stack_layer: str,
    confidence: float,
    occurred_at: datetime,
) -> Event:
    event = session.scalar(select(Event).where(Event.title == title))
    if event is None:
        event = Event(
            title=title,
            event_type=event_type,
            source_document_id=source_document.id,
            summary=summary,
            why_it_matters=why_it_matters,
            skeptical_note=skeptical_note,
            stack_layer=stack_layer,
            confidence=confidence,
            occurred_at=occurred_at,
            detected_at=datetime.now(timezone.utc),
            status="seeded",
            metadata_json={"seeded": True},
        )
        session.add(event)
        session.flush()
    else:
        event.event_type = event_type
        event.source_document_id = source_document.id
        event.summary = summary
        event.why_it_matters = why_it_matters
        event.skeptical_note = skeptical_note
        event.stack_layer = stack_layer
        event.confidence = confidence
        event.occurred_at = occurred_at
    return event


def attach_event_entity(session, *, event: Event, entity: Entity, role: str) -> None:
    existing = session.scalar(
        select(EventEntityLink).where(
            EventEntityLink.event_id == event.id,
            EventEntityLink.entity_id == entity.id,
            EventEntityLink.role == role,
        )
    )
    if existing is None:
        session.add(EventEntityLink(event_id=event.id, entity_id=entity.id, role=role, confidence=0.95))


def upsert_event_score(session, *, event: Event, scores: dict) -> None:
    score = session.get(EventScore, event.id)
    if score is None:
        score = EventScore(event_id=event.id, scoring_version=SCORING_VERSION)
        session.add(score)

    score.novelty_score = scores["novelty_score"]
    score.momentum_score = scores["momentum_score"]
    score.strategic_importance_score = scores["strategic_importance_score"]
    score.aws_relevance_score = scores["aws_relevance_score"]
    score.corpdev_score = scores["corpdev_score"]
    score.confidence_score = scores["confidence_score"]
    score.radar_score = scores["radar_score"]
    score.rationale_json = scores["rationale_json"]
    score.scored_at = datetime.now(timezone.utc)


def upsert_entity_score(session, *, entity: Entity, scores: dict) -> None:
    score = session.get(EntityScore, entity.id)
    if score is None:
        score = EntityScore(entity_id=entity.id, scoring_version=SCORING_VERSION)
        session.add(score)

    score.momentum_score = scores["momentum_score"]
    score.aws_relevance_score = scores["aws_relevance_score"]
    score.corpdev_interest_score = scores["corpdev_interest_score"]
    score.entity_priority_score = scores["entity_priority_score"]
    score.rationale_json = scores["rationale_json"]
    score.scored_at = datetime.now(timezone.utc)


def main() -> None:
    now = datetime.now(timezone.utc)

    with SessionLocal() as session:
        inference_theme = get_or_create_theme(
            session,
            name="Inference Economics",
            description="Cost and throughput shifts that materially alter inference deployment choices.",
        )
        portability_theme = get_or_create_theme(
            session,
            name="Model Portability",
            description="Control points for routing, portability, and platform leverage.",
        )
        capex_theme = get_or_create_theme(
            session,
            name="AI Capex Signals",
            description="Public signals about infrastructure demand and spending.",
        )

        tensorforge = get_or_create_entity(
            session,
            entity_type="company",
            canonical_name="TensorForge",
            website="https://tensorforge.example.com",
            description="Inference stack vendor focused on latency-aware GPU serving.",
        )
        skybridge = get_or_create_entity(
            session,
            entity_type="public_company",
            canonical_name="SkyBridge Compute",
            website="https://skybridge.example.com",
            description="GPU cloud operator expanding regional AI factory capacity.",
        )
        fluxrouter = get_or_create_entity(
            session,
            entity_type="repository",
            canonical_name="FluxRouter",
            website="https://github.com/example/fluxrouter",
            description="Open-source routing layer for multi-model inference portability.",
        )
        accelerant_paper = get_or_create_entity(
            session,
            entity_type="paper",
            canonical_name="Accelerant Sparse Runtime",
            website="https://arxiv.org/abs/2603.01234",
            description="Paper describing a sparse runtime that cuts inference costs for frontier models.",
        )

        attach_theme(session, entity=tensorforge, theme=inference_theme)
        attach_theme(session, entity=skybridge, theme=capex_theme)
        attach_theme(session, entity=fluxrouter, theme=portability_theme)
        attach_theme(session, entity=accelerant_paper, theme=inference_theme)

        arxiv_doc = get_or_create_source_document(
            session,
            source_type="arxiv",
            source_external_id="2603.01234",
            title="Accelerant Sparse Runtime",
            url="https://arxiv.org/abs/2603.01234",
            raw_text="Sparse runtime work shows lower token cost at competitive throughput.",
            normalized_text="Sparse runtime work shows lower token cost at competitive throughput.",
            published_at=now - timedelta(days=2),
        )
        github_doc = get_or_create_source_document(
            session,
            source_type="github",
            source_external_id="fluxrouter-v0.9.0",
            title="FluxRouter v0.9.0 release",
            url="https://github.com/example/fluxrouter/releases/tag/v0.9.0",
            raw_text="Release adds weighted failover and policy routing across model providers.",
            normalized_text="Release adds weighted failover and policy routing across model providers.",
            published_at=now - timedelta(days=1, hours=4),
        )
        hf_doc = get_or_create_source_document(
            session,
            source_type="huggingface",
            source_external_id="tensorforge-tfserve",
            title="TensorForge tfserve update",
            url="https://huggingface.co/tensorforge/tfserve",
            raw_text="Updated model serving stack with speculative decoding support.",
            normalized_text="Updated model serving stack with speculative decoding support.",
            published_at=now - timedelta(hours=20),
        )
        edgar_doc = get_or_create_source_document(
            session,
            source_type="edgar",
            source_external_id="skybridge-10k-2026",
            title="SkyBridge Compute annual filing",
            url="https://www.sec.gov/Archives/edgar/data/example",
            raw_text="Filing notes step-function expansion in GPU capacity and multiyear commitments.",
            normalized_text="Filing notes step-function expansion in GPU capacity and multiyear commitments.",
            published_at=now - timedelta(days=3),
        )

        paper_event = get_or_create_event(
            session,
            title="Sparse runtime paper claims lower inference cost",
            event_type="paper_published",
            source_document=arxiv_doc,
            summary="A new paper describes a sparse runtime that reduces serving cost without a large quality tradeoff.",
            why_it_matters="If replicated, it changes inference unit economics and vendor leverage.",
            skeptical_note="Benchmarks are self-reported and need replication on production traffic.",
            stack_layer="Training and inference systems",
            confidence=0.72,
            occurred_at=now - timedelta(days=2),
        )
        repo_event = get_or_create_event(
            session,
            title="FluxRouter gains policy routing and failover",
            event_type="major_release",
            source_document=github_doc,
            summary="The release expands control-plane features for multi-model routing and graceful failover.",
            why_it_matters="Routing layers are potential control points above underlying model providers.",
            skeptical_note="Feature breadth may outrun real enterprise adoption.",
            stack_layer="Model routing / portability / gateway layer",
            confidence=0.81,
            occurred_at=now - timedelta(days=1, hours=4),
        )
        product_event = get_or_create_event(
            session,
            title="TensorForge ships speculative decoding in serving stack",
            event_type="product_launch",
            source_document=hf_doc,
            summary="TensorForge published a serving stack update centered on speculative decoding and latency gains.",
            why_it_matters="Serving efficiency improvements can translate directly into cost advantage and AWS workload pull.",
            skeptical_note="The update may be optimization theater without broader ecosystem validation.",
            stack_layer="Training and inference systems",
            confidence=0.76,
            occurred_at=now - timedelta(hours=20),
        )
        filing_event = get_or_create_event(
            session,
            title="SkyBridge filing signals faster AI factory buildout",
            event_type="capex_signal",
            source_document=edgar_doc,
            summary="The filing points to larger GPU commitments and a wider infrastructure footprint.",
            why_it_matters="Capex acceleration can reprice cloud competition and shape partner risk.",
            skeptical_note="Capex guidance can lag actual demand quality.",
            stack_layer="Cloud / AI factories / GPU clouds",
            confidence=0.84,
            occurred_at=now - timedelta(days=3),
        )

        attach_event_entity(session, event=paper_event, entity=accelerant_paper, role="subject")
        attach_event_entity(session, event=repo_event, entity=fluxrouter, role="subject")
        attach_event_entity(session, event=product_event, entity=tensorforge, role="subject")
        attach_event_entity(session, event=filing_event, entity=skybridge, role="subject")

        upsert_event_score(
            session,
            event=paper_event,
            scores={
                "novelty_score": 8.8,
                "momentum_score": 7.1,
                "strategic_importance_score": 8.6,
                "aws_relevance_score": 7.9,
                "corpdev_score": 5.2,
                "confidence_score": 7.2,
                "radar_score": 7.85,
                "rationale_json": {"seeded": True, "driver": "inference economics shift"},
            },
        )
        upsert_event_score(
            session,
            event=repo_event,
            scores={
                "novelty_score": 7.4,
                "momentum_score": 8.7,
                "strategic_importance_score": 8.1,
                "aws_relevance_score": 8.3,
                "corpdev_score": 6.4,
                "confidence_score": 8.0,
                "radar_score": 7.91,
                "rationale_json": {"seeded": True, "driver": "gateway control point"},
            },
        )
        upsert_event_score(
            session,
            event=product_event,
            scores={
                "novelty_score": 7.1,
                "momentum_score": 8.2,
                "strategic_importance_score": 8.7,
                "aws_relevance_score": 8.8,
                "corpdev_score": 7.3,
                "confidence_score": 7.6,
                "radar_score": 8.02,
                "rationale_json": {"seeded": True, "driver": "serving efficiency and platform pull"},
            },
        )
        upsert_event_score(
            session,
            event=filing_event,
            scores={
                "novelty_score": 6.9,
                "momentum_score": 8.5,
                "strategic_importance_score": 9.0,
                "aws_relevance_score": 8.1,
                "corpdev_score": 6.7,
                "confidence_score": 8.5,
                "radar_score": 8.03,
                "rationale_json": {"seeded": True, "driver": "capex signal with competitive implications"},
            },
        )

        upsert_entity_score(
            session,
            entity=tensorforge,
            scores={
                "momentum_score": 8.3,
                "aws_relevance_score": 8.9,
                "corpdev_interest_score": 7.1,
                "entity_priority_score": 8.15,
                "rationale_json": {"seeded": True, "driver": "serving stack traction"},
            },
        )
        upsert_entity_score(
            session,
            entity=skybridge,
            scores={
                "momentum_score": 8.1,
                "aws_relevance_score": 7.8,
                "corpdev_interest_score": 6.3,
                "entity_priority_score": 7.74,
                "rationale_json": {"seeded": True, "driver": "capex expansion"},
            },
        )
        upsert_entity_score(
            session,
            entity=fluxrouter,
            scores={
                "momentum_score": 8.8,
                "aws_relevance_score": 8.4,
                "corpdev_interest_score": 7.5,
                "entity_priority_score": 8.28,
                "rationale_json": {"seeded": True, "driver": "routing control point"},
            },
        )
        upsert_entity_score(
            session,
            entity=accelerant_paper,
            scores={
                "momentum_score": 7.6,
                "aws_relevance_score": 7.7,
                "corpdev_interest_score": 4.5,
                "entity_priority_score": 7.08,
                "rationale_json": {"seeded": True, "driver": "research signal"},
            },
        )

        opportunity = session.scalar(select(Opportunity).where(Opportunity.title == "Partnership monitor: FluxRouter"))
        if opportunity is None:
            opportunity = Opportunity(
                entity_id=fluxrouter.id,
                theme_id=portability_theme.id,
                opportunity_type="partnership",
                title="Partnership monitor: FluxRouter",
                rationale="FluxRouter is becoming a routing-layer control point that could influence where inference spend lands.",
                risks="Unclear enterprise stickiness and low moat if cloud vendors replicate features quickly.",
                integration_notes="Investigate control-plane integration paths with AWS model access layers.",
                priority_score=7.6,
                status="open",
            )
            session.add(opportunity)
            session.flush()
        existing_opportunity_link = session.scalar(
            select(OpportunityEventLink).where(
                OpportunityEventLink.opportunity_id == opportunity.id,
                OpportunityEventLink.event_id == repo_event.id,
            )
        )
        if existing_opportunity_link is None:
            session.add(OpportunityEventLink(opportunity_id=opportunity.id, event_id=repo_event.id))

        watchlist = session.scalar(select(Watchlist).where(Watchlist.name == "Core radar names"))
        if watchlist is None:
            watchlist = Watchlist(
                name="Core radar names",
                description="Seeded watchlist covering entities and themes with immediate strategy relevance.",
                watchlist_type="mixed",
            )
            session.add(watchlist)
            session.flush()

        if session.scalar(select(WatchlistItem).where(WatchlistItem.watchlist_id == watchlist.id, WatchlistItem.entity_id == tensorforge.id)) is None:
            session.add(WatchlistItem(watchlist_id=watchlist.id, entity_id=tensorforge.id, notes="Serving stack signal"))
        if session.scalar(select(WatchlistItem).where(WatchlistItem.watchlist_id == watchlist.id, WatchlistItem.theme_id == portability_theme.id)) is None:
            session.add(WatchlistItem(watchlist_id=watchlist.id, theme_id=portability_theme.id, notes="Control plane theme"))

        brief = session.scalar(select(DailyBrief).where(DailyBrief.brief_date == date(2026, 3, 8)))
        if brief is None:
            brief = DailyBrief(
                brief_date=date(2026, 3, 8),
                title="AI Infrastructure Radar daily brief",
                summary="Inference efficiency and routing control points are the strongest signals in the current seed set.",
                aws_implications="AWS should monitor routing-layer leverage and serving efficiency gains that change workload placement economics.",
                possible_actions="Review partner map for routing vendors and compare serving stack exposure across priority entities.",
                skeptical_counterpoints="Most signals are early and single-source; durable adoption is not yet proven.",
                status="published",
                updated_at=datetime.now(timezone.utc),
                metadata_json={"seeded": True},
            )
            session.add(brief)
            session.flush()
        else:
            brief.updated_at = datetime.now(timezone.utc)

        existing_items = session.scalars(select(DailyBriefItem).where(DailyBriefItem.daily_brief_id == brief.id)).all()
        for item in existing_items:
            session.delete(item)

        session.add_all(
            [
                DailyBriefItem(
                    daily_brief_id=brief.id,
                    item_type="top_event",
                    rank=1,
                    title=filing_event.title,
                    summary=filing_event.summary or "",
                    event_id=filing_event.id,
                    metadata_json={"seeded": True},
                ),
                DailyBriefItem(
                    daily_brief_id=brief.id,
                    item_type="top_event",
                    rank=2,
                    title=product_event.title,
                    summary=product_event.summary or "",
                    event_id=product_event.id,
                    metadata_json={"seeded": True},
                ),
                DailyBriefItem(
                    daily_brief_id=brief.id,
                    item_type="emerging_entity",
                    rank=1,
                    title=fluxrouter.canonical_name,
                    summary="FluxRouter is becoming a routing-layer control point with clear partner relevance.",
                    entity_id=fluxrouter.id,
                    metadata_json={"seeded": True},
                ),
            ]
        )

        session.commit()
        print("Seeded demo data for AI Infrastructure Radar.")


if __name__ == "__main__":
    main()
