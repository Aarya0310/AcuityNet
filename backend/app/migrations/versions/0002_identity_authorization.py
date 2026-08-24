"""identity and authorization foundation

Revision ID: 0002_identity_authorization
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_identity_authorization"
down_revision = "0001_phase1_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.String(32), primary_key=True),
        sa.Column("username", sa.String(80), nullable=False, unique=True),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("role", sa.String(16), nullable=False),
        sa.Column("password_digest", sa.String(256), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
    )
    op.add_column("nurses", sa.Column("user_id", sa.String(32), nullable=True))
    with op.batch_alter_table("nurses") as batch_op:
        batch_op.create_foreign_key("fk_nurses_user_id", "users", ["user_id"], ["user_id"])
    with op.batch_alter_table("nurses") as batch_op:
        batch_op.create_unique_constraint("uq_nurses_user_id", ["user_id"])


def downgrade() -> None:
    with op.batch_alter_table("nurses") as batch_op:
        batch_op.drop_constraint("uq_nurses_user_id", type_="unique")
    with op.batch_alter_table("nurses") as batch_op:
        batch_op.drop_constraint("fk_nurses_user_id", type_="foreignkey")
    op.drop_column("nurses", "user_id")
    op.drop_table("users")