"""paragraphs table

Revision ID: c3a1f0d2b9e4
Revises: afad6ea87a2a
Create Date: 2026-10-07 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3a1f0d2b9e4"
down_revision: str | Sequence[str] | None = "afad6ea87a2a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "paragraphs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("post_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("source", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["post_id"], ["posts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("post_id", "position", name="uq_paragraphs_post_position"),
    )
    op.create_index(op.f("ix_paragraphs_post_id"), "paragraphs", ["post_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_paragraphs_post_id"), table_name="paragraphs")
    op.drop_table("paragraphs")
