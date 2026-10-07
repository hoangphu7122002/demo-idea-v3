"""Demo routes: reset the database to the seed set (D006), only when DEMO_MODE is on."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.seed.service import reseed

router = APIRouter(prefix="/demo", tags=["demo"])


class DemoSettings(BaseSettings):
    """``DEMO_MODE`` flag (env or .env); off by default so production never exposes reset."""

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    demo_mode: bool = False


@lru_cache
def get_demo_settings() -> DemoSettings:
    """Return the cached demo settings; tests override this dependency."""
    return DemoSettings()


def require_demo_mode(settings: Annotated[DemoSettings, Depends(get_demo_settings)]) -> None:
    """Raise 404 (route looks absent) unless DEMO_MODE is on."""
    if not settings.demo_mode:
        raise HTTPException(404, "not found")


class ResetOut(BaseModel):
    status: str


@router.post(
    "/reset",
    response_model=ResetOut,
    dependencies=[Depends(require_demo_mode)],
    responses={404: {"description": "DEMO_MODE is off"}},
)
def reset_demo() -> ResetOut:
    """Truncate posts and users and reload the seed files (``reseed``).

    Output: ``{"status": "reset"}``. Errors: 404 when DEMO_MODE is off.
    """
    reseed()
    return ResetOut(status="reset")
