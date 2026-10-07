import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.job import _now


class Paragraph(Base):
    """One block of a post's Markdown body, addressable by a stable id.

    ``post_id`` references ``posts.id`` with ``ON DELETE CASCADE``; ``position`` is the
    0-based order in the post and is unique per post. ``source`` is the raw block text.
    """

    __tablename__ = "paragraphs"
    __table_args__ = (UniqueConstraint("post_id", "position", name="uq_paragraphs_post_position"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    position: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
