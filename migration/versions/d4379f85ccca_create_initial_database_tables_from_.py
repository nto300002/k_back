"""Create initial database tables from models

Revision ID: d4379f85ccca
Revises: 
Create Date: 2025-07-24 11:15:30.518385

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'd4379f85ccca'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


staff_role_enum = sa.Enum(
    "employee",
    "manager",
    "service_administrator",
    name="staffrole",
    create_type=False
)

office_type_enum = sa.Enum(
    "transition_to_employment",
    "type_B_office",
    "type_A_office",
    name="officetype",
    create_type=False
)

billing_status_enum = sa.Enum(
    "free",
    "active",
    "past_due",
    "canceled",
    name="billingstatus",
    create_type=False
)

def upgrade() -> None:
    op.create_table(
        "staffs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("role", staff_role_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        schema="public"
    )

    op.create_table(
        "offices",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("is_group", sa.Boolean(), nullable=False),
        sa.Column("office_type", office_type_enum, nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("last_modified_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("billing_status", billing_status_enum, nullable=False),
        sa.Column("stripe_customer_id", sa.String(length=255), unique=True, nullable=True),
        sa.Column("stripe_subscription_id", sa.String(length=255), unique=True, nullable=True),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        schema="public"
    )

    op.create_table(
        "office_staffs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("staff_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("office_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["staff_id"], ["staffs.id"]),
        sa.ForeignKeyConstraint(["office_id"], ["offices.id"]),
        sa.PrimaryKeyConstraint("id"),
        schema="public",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("office_staffs", schema="public")
    op.drop_table("offices", schema="public")
    op.drop_table("staffs", schema="public")
    staff_role_enum.drop(op.get_bind(), checkfirst=True)
    office_type_enum.drop(op.get_bind(), checkfirst=True)
    billing_status_enum.drop(op.get_bind(), checkfirst=True)
