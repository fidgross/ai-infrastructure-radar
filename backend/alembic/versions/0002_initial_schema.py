"""Create initial milestone 1 schema."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0002_initial_schema"
down_revision = "0001_enable_pgvector"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("documents_seen", sa.Integer(), server_default="0", nullable=False),
        sa.Column("documents_created", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    )
    op.create_index("ix_ingestion_runs_source_type", "ingestion_runs", ["source_type"])

    op.create_table(
        "source_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingestion_runs.id", ondelete="SET NULL")),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("source_external_id", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("normalized_text", sa.Text(), nullable=True),
        sa.Column("fingerprint", sa.String(length=255), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.UniqueConstraint("fingerprint", name="uq_source_documents_fingerprint"),
    )
    op.create_index("ix_source_documents_source_type", "source_documents", ["source_type"])
    op.create_index("ix_source_documents_published_at", "source_documents", ["published_at"])

    op.create_table(
        "source_payloads",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("ingestion_run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("ingestion_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("source_documents.id", ondelete="CASCADE"), nullable=True),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("payload_hash", sa.String(length=255), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("payload_hash", name="uq_source_payloads_payload_hash"),
    )
    op.create_index("ix_source_payloads_source_type", "source_payloads", ["source_type"])

    op.create_table(
        "entities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("entity_type", sa.String(length=64), nullable=False),
        sa.Column("canonical_name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("website", sa.String(length=500), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("slug", name="uq_entities_slug"),
    )
    op.create_index("ix_entities_entity_type", "entities", ["entity_type"])
    op.create_index("ix_entities_canonical_name", "entities", ["canonical_name"])

    op.create_table(
        "entity_aliases",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("alias", sa.String(length=255), nullable=False),
        sa.Column("confidence", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("is_manual", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    )
    op.create_index("ix_entity_aliases_alias", "entity_aliases", ["alias"])

    op.create_table(
        "themes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.UniqueConstraint("slug", name="uq_themes_slug"),
    )

    op.create_table(
        "entity_theme_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("theme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("themes.id", ondelete="CASCADE"), nullable=False),
        sa.Column("confidence", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("is_manual", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.UniqueConstraint("entity_id", "theme_id", name="uq_entity_theme_links_entity_theme"),
    )

    op.create_table(
        "events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("why_it_matters", sa.Text(), nullable=True),
        sa.Column("skeptical_note", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("source_documents.id", ondelete="SET NULL")),
        sa.Column("stack_layer", sa.String(length=100), nullable=True),
        sa.Column("confidence", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="candidate", nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    )
    op.create_index("ix_events_event_type", "events", ["event_type"])
    op.create_index("ix_events_occurred_at", "events", ["occurred_at"])
    op.create_index("ix_events_stack_layer", "events", ["stack_layer"])

    op.create_table(
        "event_entity_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=True),
        sa.Column("confidence", sa.Float(), server_default="1.0", nullable=False),
        sa.UniqueConstraint("event_id", "entity_id", "role", name="uq_event_entity_links_event_entity_role"),
    )

    op.create_table(
        "event_scores",
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column("novelty_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("momentum_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("strategic_importance_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("aws_relevance_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("corpdev_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("confidence_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("radar_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("scoring_version", sa.String(length=32), nullable=False),
        sa.Column("rationale_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    )
    op.create_index("ix_event_scores_radar_score", "event_scores", ["radar_score"])

    op.create_table(
        "entity_scores",
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column("momentum_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("aws_relevance_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("corpdev_interest_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("entity_priority_score", sa.Float(), server_default="0.0", nullable=False),
        sa.Column("scoring_version", sa.String(length=32), nullable=False),
        sa.Column("rationale_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    )
    op.create_index("ix_entity_scores_priority", "entity_scores", ["entity_priority_score"])

    op.create_table(
        "watchlists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("watchlist_type", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    op.create_table(
        "watchlist_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("watchlist_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("watchlists.id", ondelete="CASCADE"), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("theme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("themes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    op.create_table(
        "opportunities",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("theme_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("themes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("opportunity_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("risks", sa.Text(), nullable=True),
        sa.Column("integration_notes", sa.Text(), nullable=True),
        sa.Column("priority_score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="open", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_opportunities_priority_score", "opportunities", ["priority_score"])

    op.create_table(
        "opportunity_event_links",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="CASCADE"), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("opportunity_id", "event_id", name="uq_opportunity_event_links_opportunity_event"),
    )

    op.create_table(
        "daily_briefs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("brief_date", sa.Date(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("aws_implications", sa.Text(), nullable=True),
        sa.Column("possible_actions", sa.Text(), nullable=True),
        sa.Column("skeptical_counterpoints", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), server_default="published", nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.UniqueConstraint("brief_date", name="uq_daily_briefs_brief_date"),
    )

    op.create_table(
        "daily_brief_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("daily_brief_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("daily_briefs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_type", sa.String(length=64), nullable=False),
        sa.Column("rank", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id", ondelete="SET NULL"), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
    )

    op.create_table(
        "analyst_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("opportunity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("note_type", sa.String(length=64), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    op.create_table(
        "embedding_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("source_document_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("source_documents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("entities.id", ondelete="SET NULL"), nullable=True),
        sa.Column("event_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("events.id", ondelete="SET NULL"), nullable=True),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.create_index("ix_embedding_chunks_chunk_index", "embedding_chunks", ["chunk_index"])


def downgrade() -> None:
    op.drop_index("ix_embedding_chunks_chunk_index", table_name="embedding_chunks")
    op.drop_table("embedding_chunks")
    op.drop_table("analyst_notes")
    op.drop_table("daily_brief_items")
    op.drop_table("daily_briefs")
    op.drop_table("opportunity_event_links")
    op.drop_index("ix_opportunities_priority_score", table_name="opportunities")
    op.drop_table("opportunities")
    op.drop_table("watchlist_items")
    op.drop_table("watchlists")
    op.drop_index("ix_entity_scores_priority", table_name="entity_scores")
    op.drop_table("entity_scores")
    op.drop_index("ix_event_scores_radar_score", table_name="event_scores")
    op.drop_table("event_scores")
    op.drop_table("event_entity_links")
    op.drop_index("ix_events_stack_layer", table_name="events")
    op.drop_index("ix_events_occurred_at", table_name="events")
    op.drop_index("ix_events_event_type", table_name="events")
    op.drop_table("events")
    op.drop_table("entity_theme_links")
    op.drop_table("themes")
    op.drop_index("ix_entity_aliases_alias", table_name="entity_aliases")
    op.drop_table("entity_aliases")
    op.drop_index("ix_entities_canonical_name", table_name="entities")
    op.drop_index("ix_entities_entity_type", table_name="entities")
    op.drop_table("entities")
    op.drop_index("ix_source_payloads_source_type", table_name="source_payloads")
    op.drop_table("source_payloads")
    op.drop_index("ix_source_documents_published_at", table_name="source_documents")
    op.drop_index("ix_source_documents_source_type", table_name="source_documents")
    op.drop_table("source_documents")
    op.drop_index("ix_ingestion_runs_source_type", table_name="ingestion_runs")
    op.drop_table("ingestion_runs")
