from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.persistence.models import Alert, AlertEvent, PredictionEvidence


class AlertRepository:
    def __init__(self, session: Session):
        self.session = session

    def prior_evidence(self, patient_id: str, sequence: int):
        return self.session.scalar(select(PredictionEvidence).where(PredictionEvidence.patient_id == patient_id, PredictionEvidence.observation_sequence < sequence).order_by(PredictionEvidence.observation_sequence.desc()))

    def evidence_for_observation(self, observation_id: int):
        return self.session.scalar(select(PredictionEvidence).where(PredictionEvidence.observation_id == observation_id))

    def active_alert(self, patient_id: str):
        return self.session.scalar(select(Alert).where(Alert.patient_id == patient_id, Alert.state != "resolved").order_by(Alert.alert_id.desc()))

    def latest_resolved(self, patient_id: str):
        return self.session.scalar(select(Alert).where(Alert.patient_id == patient_id, Alert.state == "resolved").order_by(Alert.resolved_at.desc(), Alert.alert_id.desc()))

    def evidence_for(self, alert: Alert):
        return self.session.get(PredictionEvidence, alert.evidence_id)

    def events_for(self, alert_id: int):
        return list(self.session.scalars(select(AlertEvent).where(AlertEvent.alert_id == alert_id).order_by(AlertEvent.occurred_at.asc(), AlertEvent.event_id.asc())))