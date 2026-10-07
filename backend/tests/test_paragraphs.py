import uuid
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.db import sync_engine
from app.models import Base, Paragraph, Post, User


@pytest.fixture
def session() -> Iterator[Session]:
    with Session(sync_engine) as s:
        yield s


@pytest.fixture
def post(session: Session) -> Post:
    user = User(name="Ada", email="ada@example.com")
    session.add(user)
    session.flush()
    p = Post(slug="hello", title="Hello", body_md="a\n\nb", author_id=user.id)
    session.add(p)
    session.commit()
    return p


def test_insert_paragraph(session: Session, post: Post) -> None:
    session.add(Paragraph(post_id=post.id, position=0, source="First block"))
    session.commit()

    row = session.scalars(select(Paragraph)).one()
    assert isinstance(row.id, uuid.UUID)
    assert (row.post_id, row.position, row.source) == (post.id, 0, "First block")
    assert row.updated_at is not None


def test_unique_post_position(session: Session, post: Post) -> None:
    session.add(Paragraph(post_id=post.id, position=0, source="a"))
    session.commit()

    session.add(Paragraph(post_id=post.id, position=0, source="dup"))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    # Same position in a different post is fine.
    other = Post(slug="other", title="O", body_md="x", author_id=post.author_id)
    session.add(other)
    session.flush()
    session.add(Paragraph(post_id=other.id, position=0, source="ok"))
    session.commit()
    assert len(session.scalars(select(Paragraph)).all()) == 2


def test_cascade_delete_with_post(session: Session, post: Post) -> None:
    session.add_all([Paragraph(post_id=post.id, position=i, source=f"p{i}") for i in range(3)])
    session.commit()
    assert len(session.scalars(select(Paragraph)).all()) == 3

    session.delete(post)
    session.commit()

    assert session.scalars(select(Paragraph)).all() == []


def test_alembic_upgrade_head_on_empty_db() -> None:
    """Migrations alone (no create_all) build users, posts and paragraphs; downgrade undoes it."""
    Base.metadata.drop_all(sync_engine)
    with sync_engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
    cfg = Config("alembic.ini")
    try:
        command.upgrade(cfg, "head")
        tables = set(inspect(sync_engine).get_table_names())
        assert {"users", "posts", "paragraphs"} <= tables
        uniques = inspect(sync_engine).get_unique_constraints("paragraphs")
        assert [u["column_names"] for u in uniques] == [["post_id", "position"]]
        command.downgrade(cfg, "afad6ea87a2a")
        assert not {"users", "posts", "paragraphs"} & set(inspect(sync_engine).get_table_names())
    finally:
        Base.metadata.drop_all(sync_engine)
        with sync_engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS alembic_version"))
