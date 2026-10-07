import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.job import _now


class Paragraph(Base):
    """One addressable block of a post's Markdown body.

    ``id`` is a stable uuid so comments/annotations can reference it. ``position`` is the
    0-based order inside the post and is unique per post. ``source`` is the block's raw
    Markdown. Deleting a post deletes its paragraphs. ``updated_at`` is refreshed on update.
    """

    __tablename__ = "paragraphs"
    __table_args__ = (UniqueConstraint("post_id", "position", name="uq_paragraphs_post_position"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
