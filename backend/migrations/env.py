from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool

from app.config import settings
from app.models import entities  # noqa: F401  (registers every table on Base.metadata)
from app.models.database import Base, UTCDateTime

config = context.config

# Only configure logging for the `alembic` command line, never inside the running server.
if config.cmd_opts is not None and config.config_file_name:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _url() -> str:
    return config.attributes.get("database_url") or settings.sqlalchemy_database_url


def _render_item(type_, obj, _autogen_context):
    if type_ == "type" and isinstance(obj, UTCDateTime):
        return "sa.DateTime(timezone=True)"
    return False


def _configure(**kwargs) -> None:
    context.configure(target_metadata=target_metadata, render_item=_render_item,
                      compare_type=True, **kwargs)


def run_migrations_offline() -> None:
    url = _url()
    _configure(url=url, literal_binds=True, render_as_batch=url.startswith("sqlite"))
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    engine = create_engine(_url(), poolclass=pool.NullPool)
    with engine.connect() as connection:
        _configure(connection=connection, render_as_batch=connection.dialect.name == "sqlite")
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
