"""monitoring alert evidence and audit persistence"""

from alembic import op
import sqlalchemy as sa

revision = "0003_monitoring_alerts_audit"
down_revision = "0002_identity_authorization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("prediction_evidence",
        sa.Column("evidence_id", sa.Integer(), primary_key=True), sa.Column("patient_id", sa.String(32), sa.ForeignKey("patients.patient_id"), nullable=False),
        sa.Column("observation_id", sa.Integer(), sa.ForeignKey("vital_observations.observation_id"), nullable=False, unique=True), sa.Column("observation_sequence", sa.Integer(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False), sa.Column("event", sa.String(120), nullable=False), sa.Column("level", sa.String(16), nullable=False), sa.Column("probability", sa.Float(), nullable=False), sa.Column("horizon_minutes", sa.Integer(), nullable=False),
        sa.Column("source_kind", sa.String(32), nullable=False), sa.Column("source_version", sa.String(40), nullable=False), sa.Column("fallback_reason", sa.String(200)), sa.Column("fallback_metadata", sa.String(500), nullable=False), sa.Column("prediction_contract_version", sa.String(40), nullable=False),
        sa.Column("synthetic_source_kind", sa.String(32), nullable=False), sa.Column("synthetic_source_name", sa.String(80), nullable=False), sa.Column("synthetic_scenario_id", sa.String(80), nullable=False), sa.Column("synthetic_scenario_version", sa.String(20), nullable=False), sa.Column("prototype_label", sa.String(160), nullable=False),
        sa.Column("effective_threshold", sa.Float(), nullable=False), sa.Column("rule_version", sa.String(40), nullable=False), sa.Column("server_timestamp", sa.DateTime(timezone=True), nullable=False))
    op.create_table("alerts",
        sa.Column("alert_id", sa.Integer(), primary_key=True), sa.Column("patient_id", sa.String(32), sa.ForeignKey("patients.patient_id"), nullable=False), sa.Column("bed_id", sa.String(32), sa.ForeignKey("beds.bed_id"), nullable=False), sa.Column("episode_key", sa.String(80), nullable=False), sa.Column("state", sa.String(20), nullable=False), sa.Column("priority", sa.String(16), nullable=False), sa.Column("evidence_id", sa.Integer(), sa.ForeignKey("prediction_evidence.evidence_id"), nullable=False), sa.Column("deduplication_status", sa.String(24), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("resolved_at", sa.DateTime(timezone=True)), sa.UniqueConstraint("patient_id", "episode_key", name="uq_alert_patient_episode"))
    op.create_table("alert_events", sa.Column("event_id", sa.Integer(), primary_key=True), sa.Column("alert_id", sa.Integer(), sa.ForeignKey("alerts.alert_id"), nullable=False), sa.Column("state", sa.String(20), nullable=False), sa.Column("outcome", sa.String(24), nullable=False), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("audit_events", sa.Column("audit_id", sa.Integer(), primary_key=True), sa.Column("actor_id", sa.String(32), sa.ForeignKey("users.user_id")), sa.Column("action", sa.String(80), nullable=False), sa.Column("resource_type", sa.String(40), nullable=False), sa.Column("resource_id", sa.String(80)), sa.Column("outcome", sa.String(24), nullable=False), sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False), sa.Column("details", sa.String(1000), nullable=False))
    op.create_index("ix_prediction_evidence_patient_sequence", "prediction_evidence", ["patient_id", "observation_sequence"])
    op.create_index("ix_alerts_patient_state", "alerts", ["patient_id", "state"])
    op.create_index("ix_alert_events_alert_order", "alert_events", ["alert_id", "event_id"])
    op.create_index("ix_audit_events_order", "audit_events", ["occurred_at", "audit_id"])


def downgrade() -> None:
    for index, table in [("ix_audit_events_order", "audit_events"), ("ix_alert_events_alert_order", "alert_events"), ("ix_alerts_patient_state", "alerts"), ("ix_prediction_evidence_patient_sequence", "prediction_evidence")]:
        op.drop_index(index, table_name=table)
    op.drop_table("audit_events")
    op.drop_table("alert_events")
    op.drop_table("alerts")
    op.drop_table("prediction_evidence")