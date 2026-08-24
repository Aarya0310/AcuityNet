from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Patient(Base):
    __tablename__ = "patients"
    patient_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)


class Bed(Base):
    __tablename__ = "beds"
    bed_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    unit: Mapped[str] = mapped_column(String(80), nullable=False)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), unique=True)


class User(Base):
    __tablename__ = "users"
    user_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    username: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    password_digest: Mapped[str] = mapped_column(String(256), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    nurse: Mapped["Nurse | None"] = relationship(back_populates="user", uselist=False)


class Admission(Base):
    __tablename__ = "admissions"
    admission_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), unique=True)
    admitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class Nurse(Base):
    __tablename__ = "nurses"
    nurse_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(120), nullable=False)
    available: Mapped[bool] = mapped_column(Boolean, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), unique=True)
    user: Mapped[User | None] = relationship(back_populates="nurse")


class History(Base):
    __tablename__ = "histories"
    history_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), unique=True)
    summary: Mapped[str] = mapped_column(String(500), nullable=False)


class Configuration(Base):
    __tablename__ = "configurations"
    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str] = mapped_column(String(200), nullable=False)


class VitalObservation(Base):
    __tablename__ = "vital_observations"
    __table_args__ = (UniqueConstraint("patient_id", "sequence", name="uq_observation_patient_sequence"),)
    observation_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[str] = mapped_column(ForeignKey("patients.patient_id"), nullable=False)
    bed_id: Mapped[str] = mapped_column(ForeignKey("beds.bed_id"), nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    spo2_percent: Mapped[float] = mapped_column(Float, nullable=False)
    heart_rate_bpm: Mapped[float] = mapped_column(Float, nullable=False)
    respiratory_rate_bpm: Mapped[float] = mapped_column(Float, nullable=False)
    systolic_bp_mmhg: Mapped[float] = mapped_column(Float, nullable=False)
    diastolic_bp_mmhg: Mapped[float] = mapped_column(Float, nullable=False)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    source_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    source_name: Mapped[str] = mapped_column(String(80), nullable=False)
    scenario_id: Mapped[str] = mapped_column(String(80), nullable=False)
    scenario_version: Mapped[str] = mapped_column(String(20), nullable=False)
