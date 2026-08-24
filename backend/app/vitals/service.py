from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.persistence.models import VitalObservation
from backend.app.vitals.scenario import P1042Scenario


class ObservationService:
    def __init__(self, scenario: P1042Scenario):
        self.scenario = scenario

    def advance(
        self,
        session: Session,
        patient_id: str,
        tick: int,
        timestamp: datetime,
    ) -> VitalObservation:
        if patient_id != "P-1042":
            raise ValueError("Unsupported scenario patient")
        existing = session.scalar(
            select(VitalObservation).where(
                VitalObservation.patient_id == patient_id,
                VitalObservation.sequence == tick,
            )
        )
        if existing is not None:
            return existing

        values = self.scenario.values_for(tick)
        observation = VitalObservation(
            patient_id=patient_id,
            bed_id="ICU-12",
            sequence=tick,
            observed_at=timestamp,
            received_at=timestamp,
            spo2_percent=values[0],
            heart_rate_bpm=values[1],
            respiratory_rate_bpm=values[2],
            systolic_bp_mmhg=values[3],
            diastolic_bp_mmhg=values[4],
            temperature_c=values[5],
            source_kind="synthetic",
            source_name="acuitynet-simulator",
            scenario_id=self.scenario.scenario_id,
            scenario_version=self.scenario.scenario_version,
        )
        session.add(observation)
        session.flush()
        return observation