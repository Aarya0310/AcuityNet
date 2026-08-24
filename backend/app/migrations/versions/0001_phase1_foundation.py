"""phase 1 foundation

Revision ID: 0001_phase1_foundation
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_phase1_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("patients", sa.Column("patient_id", sa.String(32), primary_key=True), sa.Column("display_name", sa.String(120), nullable=False))
    op.create_table("beds", sa.Column("bed_id", sa.String(32), primary_key=True), sa.Column("unit", sa.String(80), nullable=False), sa.Column("patient_id", sa.String(32), sa.ForeignKey("patients.patient_id"), nullable=False, unique=True))
    op.create_table("admissions", sa.Column("admission_id", sa.String(32), primary_key=True), sa.Column("patient_id", sa.String(32), sa.ForeignKey("patients.patient_id"), nullable=False, unique=True), sa.Column("admitted_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("nurses", sa.Column("nurse_id", sa.String(32), primary_key=True), sa.Column("display_name", sa.String(120), nullable=False), sa.Column("available", sa.Boolean(), nullable=False))
    op.create_table("histories", sa.Column("history_id", sa.String(32), primary_key=True), sa.Column("patient_id", sa.String(32), sa.ForeignKey("patients.patient_id"), nullable=False, unique=True), sa.Column("summary", sa.String(500), nullable=False))
    op.create_table("configurations", sa.Column("key", sa.String(80), primary_key=True), sa.Column("value", sa.String(200), nullable=False))
    op.create_table("vital_observations", sa.Column("observation_id", sa.Integer(), primary_key=True), sa.Column("patient_id", sa.String(32), sa.ForeignKey("patients.patient_id"), nullable=False), sa.Column("bed_id", sa.String(32), sa.ForeignKey("beds.bed_id"), nullable=False), sa.Column("sequence", sa.Integer(), nullable=False), sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False), sa.Column("received_at", sa.DateTime(timezone=True), nullable=False), sa.Column("spo2_percent", sa.Float(), nullable=False), sa.Column("heart_rate_bpm", sa.Float(), nullable=False), sa.Column("respiratory_rate_bpm", sa.Float(), nullable=False), sa.Column("systolic_bp_mmhg", sa.Float(), nullable=False), sa.Column("diastolic_bp_mmhg", sa.Float(), nullable=False), sa.Column("temperature_c", sa.Float(), nullable=False), sa.Column("source_kind", sa.String(32), nullable=False), sa.Column("source_name", sa.String(80), nullable=False), sa.Column("scenario_id", sa.String(80), nullable=False), sa.Column("scenario_version", sa.String(20), nullable=False), sa.UniqueConstraint("patient_id", "sequence", name="uq_observation_patient_sequence"))


def downgrade() -> None:
    op.drop_table("vital_observations")
    op.drop_table("configurations")
    op.drop_table("histories")
    op.drop_table("nurses")
    op.drop_table("admissions")
    op.drop_table("beds")
    op.drop_table("patients")
