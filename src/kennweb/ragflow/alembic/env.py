from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
from kennweb.core.configs.ragflow import DATABASE_URL
from kennweb.ragflow import logger

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None

def run_migrations_offline() -> None:
    logger.info(f"Target Database Engine for Migration: {DATABASE_URL}")
    context.configure(
        url=DATABASE_URL
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    logger.info(f"Target Database Engine for Migration: {DATABASE_URL}")
    config.set_main_option("sqlalchemy.url", DATABASE_URL)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()