import json
from datetime import timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.admin.configuration import effective_settings
from backend.app.contracts.alerts import AlertResponse
from backend.app.persistence.models import Alert, AlertEvent, PredictionEvidence, VitalObservation
from backend.app.alerts.repository import AlertRepository


class AlertService:
    def __init__(self, adapter, clock):
        self.adapter = adapter
        self.clock = clock

    def evaluate_prediction(self, session: Session, observation: VitalObservation, vitals, settings=None):
        settings = settings or effective_settings(session)
        repository = AlertRepository(session)
        existing_evidence = repository.evidence_for_observation(observation.observation_id)
        if existing_evidence is not None:
            active = repository.active_alert(observation.patient_id)
            return None if active is None else self.to_response(session, active, "reused_active")
        prediction = self.adapter.predict(observation, vitals, settings)
        evidence = PredictionEvidence(patient_id=observation.patient_id, observation_id=observation.observation_id, observation_sequence=observation.sequence, score=prediction.score, event=prediction.event, level=prediction.level, probability=prediction.probability, horizon_minutes=prediction.horizon_minutes, source_kind=prediction.source_kind, source_version=prediction.source_version, fallback_reason=prediction.fallback_reason, fallback_metadata=json.dumps({}), prediction_contract_version=prediction.contract_version, synthetic_source_kind=prediction.provenance.source_kind, synthetic_source_name=prediction.provenance.source_name, synthetic_scenario_id=prediction.provenance.scenario_id, synthetic_scenario_version=prediction.provenance.scenario_version, prototype_label=prediction.prototype_label, effective_threshold=float(settings["critical_risk_threshold"]), rule_version=str(settings["research_rules_version"]), server_timestamp=self.clock())
        session.add(evidence)
        session.flush()
        prior = repository.prior_evidence(observation.patient_id, observation.sequence)
        threshold = float(settings["critical_risk_threshold"])
        active = repository.active_alert(observation.patient_id)
        if active is not None:
            return self.to_response(session, active, "reused_active")
        if prior is None or not prior.score < threshold <= prediction.score:
            return None
        status = "new_alert"
        resolved = repository.latest_resolved(observation.patient_id)
        now = self.clock()
        if resolved is not None and resolved.resolved_at is not None:
            resolved_at = resolved.resolved_at.replace(tzinfo=timezone.utc) if resolved.resolved_at.tzinfo is None else resolved.resolved_at
            elapsed = (now - resolved_at).total_seconds()
            cooldown = int(settings["alert_cooldown_seconds"])
            if elapsed <= cooldown:
                return self.to_response(session, resolved, "suppressed_cooldown")
            if prior.score <= float(settings["alert_rearm_threshold"]):
                status = "rearmed"
        alert = Alert(patient_id=observation.patient_id, bed_id=observation.bed_id, episode_key=f"{observation.patient_id}:{observation.sequence}", state="generated", priority="critical" if prediction.level == "critical" else "high", evidence_id=evidence.evidence_id, deduplication_status=status, created_at=now)
        session.add(alert)
        try:
            session.flush()
        except IntegrityError:
            session.rollback()
            active = AlertRepository(session).active_alert(observation.patient_id)
            if active is None:
                raise
            return self.to_response(session, active, "reused_active")
        session.add(AlertEvent(alert_id=alert.alert_id, state="generated", outcome=status, occurred_at=alert.created_at))
        return self.to_response(session, alert, status)

    def to_response(self, session, alert, status):
        evidence = AlertRepository(session).evidence_for(alert)
        alert.deduplication_status = status
        return AlertResponse(alert_id=alert.alert_id, patient_id=alert.patient_id, bed_id=alert.bed_id, priority=alert.priority, state=alert.state, risk_score=evidence.score, risk_level=evidence.level, event=evidence.event, probability=evidence.probability, horizon_minutes=evidence.horizon_minutes, observation_sequence=evidence.observation_sequence, timestamp=evidence.server_timestamp, provenance={"source_kind": evidence.synthetic_source_kind, "source_name": evidence.synthetic_source_name, "scenario_id": evidence.synthetic_scenario_id, "scenario_version": evidence.synthetic_scenario_version, "is_live_bedside_feed": False}, prototype_label=evidence.prototype_label, prediction_source_kind=evidence.source_kind, prediction_source_version=evidence.source_version, fallback_reason=evidence.fallback_reason, prediction_contract_version=evidence.prediction_contract_version, effective_threshold=evidence.effective_threshold, rule_version=evidence.rule_version, deduplication_status=status, created_at=alert.created_at)