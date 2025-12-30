"""init database schema

Revision ID: a2d1b5c2795c
Revises: 
Create Date: 2025-12-29 22:38:28.258705

"""
from typing import Sequence, Union, Tuple
from alembic import op
import sqlalchemy as sa
from kennweb.ragflow import logger


# revision identifiers, used by Alembic.
revision: str = 'a2d1b5c2795c'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def create_updated_at_trigger() -> None:
    logger.info('Create Trigger -> `update_updated_at_column`')
    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS
        $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        """
    )


def timestamps(indexed: bool = False) -> Tuple[sa.Column, sa.Column]:
    return (
        sa.Column(
            "created_at", 
            sa.TIMESTAMP(timezone=True), 
            server_default=sa.func.now(), 
            nullable=False, index=indexed
        ),
        sa.Column(
            "updated_at", 
            sa.TIMESTAMP(timezone=True), 
            server_default=sa.func.now(), 
            nullable=False, 
            index=indexed
        )
    )


def create_policies_table():
    op.create_table(
        "policies",
        sa.Column("policy_id", sa.String(64), primary_key=True),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("policy_type", sa.String(100), nullable=False),
        sa.Column("state", sa.String(2), nullable=False),
        sa.Column("effective_date", sa.Date, nullable=False),
        sa.Column("expiration_date", sa.Date, nullable=False),
        sa.Column("premium", sa.Numeric(12, 2), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        *timestamps()
    )

    op.execute(
        """
        CREATE TRIGGER update_policies_modtime
            BEFORE UPDATE
            ON policies
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )

    op.create_index(
        "ix_policies_customer_name",
        "policies",
        ["customer_name"]
    )

def create_file_metadata_table():
    op.create_table(
        "file_metadata",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_hash", sa.String(128), nullable=False),
        sa.Column("storage_path", sa.Text, nullable=False),
        sa.Column("upload_time", sa.DateTime(timezone=True), nullable=False),
        *timestamps()
    )

    op.execute(
        """
        CREATE TRIGGER update_file_metadata_modtime
            BEFORE UPDATE
            ON file_metadata
            FOR EACH ROW
        EXECUTE PROCEDURE update_updated_at_column();
        """
    )

    op.create_index(
        "ix_file_metadata_file_name",
        "file_metadata",
        ["file_name"],
    )

    op.create_unique_constraint(
        "uq_file_metadata_file_hash",
        "file_metadata",
        ["file_hash"]
    )

    op.create_index(
        "ix_file_metadata_file_name_file_hash",
        "file_metadata",
        ["file_name", "file_hash"]
    )


def upgrade() -> None:
    """Upgrade schema."""
    logger.info("Migrating Application Database schema")
    create_updated_at_trigger()
    create_policies_table()
    create_file_metadata_table()
    logger.info("Database schema migration completed")


def downgrade() -> None:
    """Downgrade schema."""
    logger.info("Downgrading Application Database schema")
    
    # Drop indexes
    op.drop_index("ix_file_metadata_file_name_file_hash", table_name="file_metadata")
    op.drop_index("ix_file_metadata_file_name", table_name="file_metadata")
    op.drop_index("ix_policies_customer_name", table_name="policies")
    
    # Drop tables
    op.drop_table("file_metadata")
    op.drop_table("policies")
    
    # Drop triggers and function
    op.execute("DROP TRIGGER IF EXISTS update_file_metadata_modtime ON file_metadata CASCADE;")
    op.execute("DROP TRIGGER IF EXISTS update_policies_modtime ON policies CASCADE;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;")
    
    logger.info("Database schema downgrading completed")