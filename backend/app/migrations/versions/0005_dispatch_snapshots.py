"""dispatch operational inputs and immutable evaluation decisions"""

from alembic import op
import sqlalchemy as sa

revision = "0005_dispatch_snapshots"
down_revision = "0004_historian_context"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for name, column in (
        ("status_updated_at", sa.Column("status_updated_at", sa.DateTime(timezone=True))),
        ("workload_updated_at", sa.Column("workload_updated_at", sa.DateTime(timezone=True))),
        ("proximity_updated_at", sa.Column("proximity_updated_at", sa.DateTime(timezone=True))),
        ("acuity_updated_at", sa.Column("acuity_updated_at", sa.DateTime(timezone=True))),
        ("proximity_km", sa.Column("proximity_km", sa.Float())),
        ("workload_active", sa.Column("workload_active", sa.Integer())),
        ("workload_capacity", sa.Column("workload_capacity", sa.Integer())),
        ("acuity_compatibility", sa.Column("acuity_compatibility", sa.Float())),
    ):
        op.add_column("nurses", column)
    op.create_table(
        "dispatch_evaluations",
        sa.Column("evaluation_id", sa.String(40), primary_key=True),
        sa.Column("patient_id", sa.String(32), sa.ForeignKey("patients.patient_id"), nullable=False),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.alert_id"), nullable=False),
        sa.Column("evidence_id", sa.Integer(), sa.ForeignKey("prediction_evidence.evidence_id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("alert_fresh_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("candidate_fresh_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("recommendation_nurse_id", sa.String(32)),
        sa.Column("weights", sa.Text(), nullable=False),
        sa.Column("candidates", sa.Text(), nullable=False),
        sa.Column("exclusions", sa.Text(), nullable=False),
        sa.Column("source_fingerprint", sa.String(120), nullable=False),
        sa.Column("recommendation_context", sa.String(240), nullable=False),
        sa.Column("prototype_label", sa.String(160), nullable=False),
    )
    op.create_table(
        "dispatch_decisions",
        sa.Column("decision_id", sa.Integer(), primary_key=True),
        sa.Column("evaluation_id", sa.String(40), sa.ForeignKey("dispatch_evaluations.evaluation_id"), nullable=False),
        sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.alert_id"), nullable=False),
        sa.Column("actor_id", sa.String(32), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("decision_type", sa.String(16), nullable=False),
        sa.Column("selected_nurse_id", sa.String(32), nullable=False),
        sa.Column("reason", sa.String(240), nullable=False),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_dispatch_evaluations_patient_created", "dispatch_evaluations", ["patient_id", "created_at"])
    op.create_index("ix_dispatch_evaluations_alert_created", "dispatch_evaluations", ["alert_id", "created_at"])
    op.create_index("ix_dispatch_decisions_alert_created", "dispatch_decisions", ["alert_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_dispatch_decisions_alert_created", table_name="dispatch_decisions")
    op.drop_index("ix_dispatch_evaluations_alert_created", table_name="dispatch_evaluations")
    op.drop_index("ix_dispatch_evaluations_patient_created", table_name="dispatch_evaluations")
    op.drop_table("dispatch_decisions")
    op.drop_table("dispatch_evaluations")
    for name in ("acuity_compatibility", "workload_capacity", "workload_active", "proximity_km", "acuity_updated_at", "proximity_updated_at", "workload_updated_at", "status_updated_at"):
        op.drop_column("nurses", name)