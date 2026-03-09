"""Add pipeline freshness bookkeeping columns."""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0003_pipeline_bookkeeping"
down_revision = "0002_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("source_documents", sa.Column("normalized_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("source_documents", sa.Column("normalization_version", sa.String(length=64), nullable=True))
    op.add_column(
        "event_scores",
        sa.Column("scored_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.add_column(
        "entity_scores",
        sa.Column("scored_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )
    op.add_column(
        "daily_briefs",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
    )

    op.execute(
        sa.text(
            """
            UPDATE source_documents
            SET normalized_at = detected_at,
                normalization_version = COALESCE(metadata_json ->> 'normalization_version', 'v1_seed')
            WHERE EXISTS (
                SELECT 1 FROM events WHERE events.source_document_id = source_documents.id
            )
            """
        )
    )
    op.execute(sa.text("UPDATE event_scores SET scored_at = NOW()"))
    op.execute(sa.text("UPDATE entity_scores SET scored_at = NOW()"))
    op.execute(sa.text("UPDATE daily_briefs SET updated_at = NOW()"))

    op.alter_column("event_scores", "scored_at", server_default=None)
    op.alter_column("entity_scores", "scored_at", server_default=None)
    op.alter_column("daily_briefs", "updated_at", server_default=None)


def downgrade() -> None:
    op.drop_column("daily_briefs", "updated_at")
    op.drop_column("entity_scores", "scored_at")
    op.drop_column("event_scores", "scored_at")
    op.drop_column("source_documents", "normalization_version")
    op.drop_column("source_documents", "normalized_at")
