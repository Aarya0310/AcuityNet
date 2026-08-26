"""historian context facts, rules, evaluations, and annotations"""

from alembic import op
import sqlalchemy as sa

revision = "0004_historian_context"
down_revision = "0003_monitoring_alerts_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "patient_context_facts",
        sa.Column("fact_id", sa.String(40), primary_key=True),
        sa.Column("patient_id", sa.String(32), sa.ForeignKey("patients.patient_id"), nullable=False),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("label", sa.String(160), nullable=False),
        sa.Column("value", sa.String(120)),
        sa.Column("unit", sa.String(32)),
        sa.Column("source_kind", sa.String(32), nullable=False),
        sa.Column("source_name", sa.String(80), nullable=False),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_complete", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "historian_rule_definitions",
        sa.Column("rule_id", sa.String(40), primary_key=True),
        sa.Column("rule_key", sa.String(80), nullable=False, unique=True),
        sa.Column("category", sa.String(20), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("version", sa.String(40), nullable=False),
        sa.Column("delta", sa.Float(), nullable=False),
        sa.Column("explanation", sa.String(240), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "historian_rule_evaluations",
        sa.Column("evaluation_id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.String(32), sa.ForeignKey("patients.patient_id"), nullable=False),
        sa.Column("evidence_id", sa.Integer(), sa.ForeignKey("prediction_evidence.evidence_id"), nullable=False),
        sa.Column("rule_id", sa.String(40), sa.ForeignKey("historian_rule_definitions.rule_id"), nullable=False),
        sa.Column("fact_id", sa.String(40), sa.ForeignKey("patient_context_facts.fact_id")),
        sa.Column("rule_key", sa.String(80), nullable=False),
        sa.Column("rule_version", sa.String(40), nullable=False),
        sa.Column("delta", sa.Float(), nullable=False),
        sa.Column("explanation", sa.String(240), nullable=False),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "timeline_annotations",
        sa.Column("annotation_id", sa.Integer(), primary_key=True),
        sa.Column("patient_id", sa.String(32), sa.ForeignKey("patients.patient_id"), nullable=False),
        sa.Column("author_id", sa.String(32), sa.ForeignKey("users.user_id"), nullable=False),
        sa.Column("text", sa.String(500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source_label", sa.String(80), nullable=False),
    )
    op.create_index("ix_patient_context_facts_patient_effective", "patient_context_facts", ["patient_id", "effective_at"])
    op.create_index("ix_historian_rule_evaluations_patient_evaluated", "historian_rule_evaluations", ["patient_id", "evaluated_at"])
    op.create_index("ix_timeline_annotations_patient_created", "timeline_annotations", ["patient_id", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_timeline_annotations_patient_created", table_name="timeline_annotations")
    op.drop_index("ix_historian_rule_evaluations_patient_evaluated", table_name="historian_rule_evaluations")
    op.drop_index("ix_patient_context_facts_patient_effective", table_name="patient_context_facts")
    op.drop_table("timeline_annotations")
    op.drop_table("historian_rule_evaluations")
    op.drop_table("historian_rule_definitions")
    op.drop_table("patient_context_facts")