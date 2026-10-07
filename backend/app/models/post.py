import uuid

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Post(Base):
    """Blog post. Minimal stub: only what `Paragraph.post_id` needs to reference.

    Extend (title body, timestamps, ...) in the posts feature; keep `id` as uuid.
    """

    __tablename__ = "posts"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(200), unique=True)
