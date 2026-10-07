"""POST /demo/reset tests: gated by DEMO_MODE, set explicitly (never from the ambient .env).

Run with ``uv run pytest app/api`` (pyproject testpaths only covers ``tests``).
"""

import os
from collections.abc import Iterator

import pytest

# Never run against the dev DB: tests drop and recreate tables.
os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
os.environ["DB_NULL_POOL"] = "1"

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import func, select  # noqa: E402

from app.api.main import app  # noqa: E402
from app.api.routes.demo import DemoSettings, get_demo_settings  # noqa: E402
from app.core.db import SyncSessionLocal, sync_engine  # noqa: E402
from app.models import Base, Post, User  # noqa: E402


@pytest.fixture(autouse=True)
def _clean_db() -> Iterator[None]:
    Base.metadata.drop_all(sync_engine)
    Base.metadata.create_all(sync_engine)
    yield
    app.dependency_overrides.pop(get_demo_settings, None)


def _set_demo_mode(value: bool) -> None:
    app.dependency_overrides[get_demo_settings] = lambda: DemoSettings(demo_mode=value)


def _counts() -> tuple[int, int]:
    with SyncSessionLocal() as s:
        return (
            s.scalar(select(func.count()).select_from(Post)) or 0,
            s.scalar(select(func.count()).select_from(User)) or 0,
        )


def test_reset_404_when_demo_mode_off() -> None:
    _set_demo_mode(False)
    r = TestClient(app).post("/demo/reset")
    assert r.status_code == 404
    assert _counts() == (0, 0)  # reseed was not called


def test_reset_reseeds_when_demo_mode_on() -> None:
    _set_demo_mode(True)
    client = TestClient(app)
    for _ in range(2):  # idempotent: second reset truncates and reloads
        r = client.post("/demo/reset")
        assert r.status_code == 200
        assert r.json() == {"status": "reset"}
        assert _counts() == (4, 1)


def test_demo_mode_defaults_to_off() -> None:
    assert DemoSettings(_env_file=None).demo_mode is False


def test_404_declared_in_openapi() -> None:
    responses = app.openapi()["paths"]["/demo/reset"]["post"]["responses"]
    assert "404" in responses
