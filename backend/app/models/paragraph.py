import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base
from app.models.job import _now


class Paragraph(Base):
    """One paragraph of a post's markdown source, addressable by a stable id.

    `position` is the 0-based order inside the post; (post_id, position) is unique.
    `source` is the raw markdown of the paragraph. Deleting a post deletes its paragraphs.
    """

    __tablename__ = "paragraphs"
    __table_args__ = (
        UniqueConstraint("post_id", "position", name="uq_paragraphs_post_id_position"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    post_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("posts.id", ondelete="CASCADE"), index=True
    )
    position: Mapped[int] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_now, onupdate=_now
    )
