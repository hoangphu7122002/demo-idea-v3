"""Seed service tests: exact counts for the fixed seed set (4 posts, 1 user), D002 reseed.

Run with ``uv run pytest app/seed`` (pyproject testpaths only covers ``tests``).
"""

import os
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest

# Never run against the dev DB: tests drop and recreate tables.
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
os.environ["DB_NULL_POOL"] = "1"

from sqlalchemy import func, select  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.content.split import split_blocks  # noqa: E402
from app.core.db import SyncSessionLocal, sync_engine  # noqa: E402
from app.models import Base, Paragraph, Post, User  # noqa: E402
from app.seed.service import reseed, seed_if_empty  # noqa: E402

SLUGS = [
    "demo-llm-api-usage",
    "side-docker-best-practices",
    "side-python-async",
    "side-sql-optimization",
]


@pytest.fixture(autouse=True)
def _clean_db() -> Iterator[None]:
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    yield


def _counts() -> tuple[int, int]:
    with SyncSessionLocal() as s:
        return (
            s.scalar(select(func.count()).select_from(Post)) or 0,
            s.scalar(select(func.count()).select_from(User)) or 0,
        )


def test_seed_if_empty_loads_exact_counts() -> None:
    assert seed_if_empty() is True
    assert _counts() == (4, 1)
    with SyncSessionLocal() as s:
        slugs = sorted(s.scalars(select(Post.slug)))
        author = s.scalars(select(User)).one()
        author_ids = set(s.scalars(select(Post.author_id)))
    assert slugs == SLUGS
    assert (author.id, author.email) == (1, "alex@example.com")
    assert author_ids == {1}


def test_seed_if_empty_skips_when_posts_exist() -> None:
    reseed()
    with SyncSessionLocal() as s, s.begin():
        s.delete(s.scalars(select(Post).where(Post.slug == SLUGS[0])).one())
    assert seed_if_empty() is False
    assert _counts() == (3, 1)


def test_reseed_discards_edits_and_restores_counts() -> None:
    reseed()
    with SyncSessionLocal() as s, s.begin():
        s.add(Post(slug="extra", title="x", body_md="x", author_id=1))
        s.scalars(select(Post).where(Post.slug == SLUGS[1])).one().title = "edited"
    assert _counts() == (5, 1)
    reseed()
    assert _counts() == (4, 1)
    with SyncSessionLocal() as s:
        titles = set(s.scalars(select(Post.title)))
    assert "edited" not in titles


def test_reseed_bad_seed_dir_keeps_data(tmp_path: Path) -> None:
    reseed()
    (tmp_path / "posts").mkdir()
    (tmp_path / "author.yaml").write_text("id: 1\nname: A\nemail: a@b.c\n")
    (tmp_path / "posts" / "bad.md").write_text("no front matter\n")
    with pytest.raises(ValueError):
        reseed(tmp_path)
    assert _counts() == (4, 1)


def _paragraphs(s: Session, post_id: int) -> list[Paragraph]:
    stmt = select(Paragraph).where(Paragraph.post_id == post_id).order_by(Paragraph.position)
    return list(s.scalars(stmt))


def test_paragraphs_created_for_each_post() -> None:
    seed_if_empty()
    with SyncSessionLocal() as s:
        posts = s.scalars(select(Post)).all()
        assert len(posts) == 4
        for post in posts:
            blocks = split_blocks(post.body_md)
            assert blocks
            assert len(_paragraphs(s, post.id)) == len(blocks), post.slug


def test_paragraph_positions_are_contiguous_from_zero() -> None:
    seed_if_empty()
    with SyncSessionLocal() as s:
        for post in s.scalars(select(Post)):
            positions = [p.position for p in _paragraphs(s, post.id)]
            assert positions == list(range(len(positions))), post.slug


def test_paragraph_ids_persisted_and_unique() -> None:
    seed_if_empty()
    with SyncSessionLocal() as s:
        ids = list(s.scalars(select(Paragraph.id)))
    assert ids
    assert all(isinstance(i, uuid.UUID) for i in ids)
    assert len(set(ids)) == len(ids)


def test_paragraph_source_matches_blocks_in_order() -> None:
    seed_if_empty()
    with SyncSessionLocal() as s:
        for post in s.scalars(select(Post)):
            sources = [p.source for p in _paragraphs(s, post.id)]
            assert sources == split_blocks(post.body_md), post.slug
