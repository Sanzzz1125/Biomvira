"""Run Alembic migrations programmatically (on server start and from the CLI)."""
from pathlib import Path
from typing import Optional

from alembic import command
from alembic.config import Config

BACKEND_DIR = Path(__file__).resolve().parents[1]


def alembic_config(database_url: Optional[str] = None) -> Config:
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_DIR / "migrations"))
    if database_url:
        config.attributes["database_url"] = database_url
    return config


def run_migrations(database_url: Optional[str] = None) -> None:
    command.upgrade(alembic_config(database_url), "head")
