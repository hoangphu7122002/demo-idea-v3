"""Seed service: loads ``backend/seed`` (one author, Markdown posts) into the database.

Used by the CLI (``python -m app.seed``) and the DEMO_MODE reset API (D002: truncate + reseed).
"""

from pathlib import Path

from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.core.db import SyncSessionLocal
from app.models import Post, User

SEED_DIR = Path(__file__).resolve().parents[2] / "seed"


def _parse_pairs(lines: list[str]) -> dict[str, str]:
    """Parse flat ``key: value`` lines into a dict (values stay strings)."""
    pairs: dict[str, str] = {}
    for line in lines:
        key, sep, value = line.partition(":")
        if sep and key.strip():
            pairs[key.strip()] = value.strip()
    return pairs


def _read_post(path: Path) -> tuple[dict[str, str], str]:
    """Split a post file into front-matter fields and the Markdown body.

    Raises ValueError if the file has no ``---`` front matter or lacks ``slug``/``title``.
    """
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        raise ValueError(f"{path.name}: missing front matter")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise ValueError(f"{path.name}: unterminated front matter") from None
    meta = _parse_pairs(lines[1:end])
    if "slug" not in meta or "title" not in meta:
        raise ValueError(f"{path.name}: front matter needs slug and title")
    return meta, "\n".join(lines[end + 1 :]).strip() + "\n"


def _load(session: Session, seed_dir: Path) -> None:
    """Insert the author and all posts from ``seed_dir`` (tables must be empty)."""
    author = _parse_pairs((seed_dir / "author.yaml").read_text(encoding="utf-8").splitlines())
    user = User(id=int(author["id"]), name=author["name"], email=author["email"])
    session.add(user)
    session.flush()
    for path in sorted((seed_dir / "posts").glob("*.md")):
        meta, body = _read_post(path)
        session.add(Post(slug=meta["slug"], title=meta["title"], body_md=body, author_id=user.id))


def reseed(seed_dir: Path = SEED_DIR) -> None:
    """Truncate ``posts`` and ``users`` (ids restart) and load the seed files, atomically.

    Input: directory with ``author.yaml`` and ``posts/*.md``. Errors: OSError/ValueError/KeyError
    on bad seed files; the transaction rolls back, so existing data is kept.
    """
    with SyncSessionLocal() as session, session.begin():
        session.execute(text("TRUNCATE TABLE posts, users RESTART IDENTITY CASCADE"))
        _load(session, seed_dir)


def seed_if_empty(seed_dir: Path = SEED_DIR) -> bool:
    """Seed only when ``posts`` has no rows. Returns True if it seeded, False if it skipped."""
    with SyncSessionLocal() as session:
        count = session.scalar(select(func.count()).select_from(Post))
    if count:
        return False
    reseed(seed_dir)
    return True
