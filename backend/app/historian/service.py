from datetime import datetime, timezone

from sqlalchemy import select

from backend.app.audit.repository import AuditRepository
from backend.app.contracts.historian import (
    AnnotationResponse,
    HistorianFact,
    HistorianResponse,
    RuleEvaluation,
    TimelineEntry,
)
from backend.app.contracts.predictions import PredictionResponse
from backend.app.contracts.patients import PatientSummary
from backend.app.contracts.vitals import SyntheticProvenance, VitalObservationResponse, resolve_freshness
from backend.app.persistence.models import (
    Admission,
    Alert,
    Bed,
    HistorianRuleDefinition,
    HistorianRuleEvaluation,
    Configuration,
    Patient,
    PatientContextFact,
    PredictionEvidence,
    TimelineAnnotation,
    VitalObservation,
)

REQUIRED_CATEGORIES = ("diagnosis", "medication", "lab", "icu_event")


def _utc(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


class HistorianService:
    def __init__(self, clock, alert_service, audit_service):
        self.clock = clock
        self.alert_service = alert_service
        self.audit_service = audit_service

    def project(self, session, patient_id: str) -> HistorianResponse:
        patient = session.get(Patient, patient_id)
        admission = session.scalar(select(Admission).where(Admission.patient_id == patient_id))
        bed = session.scalar(select(Bed).where(Bed.patient_id == patient_id))
        evidence = session.scalar(select(PredictionEvidence).where(PredictionEvidence.patient_id == patient_id).order_by(PredictionEvidence.evidence_id.desc()))
        if patient is None or admission is None or bed is None or evidence is None:
            raise LookupError("Historian context unavailable")
        observation = session.get(VitalObservation, evidence.observation_id)
        if observation is None:
            raise LookupError("Historian observation unavailable")

        facts = list(session.scalars(select(PatientContextFact).where(PatientContextFact.patient_id == patient_id).order_by(PatientContextFact.effective_at.asc(), PatientContextFact.fact_id.asc())))
        rules = list(session.scalars(select(HistorianRuleDefinition).order_by(HistorianRuleDefinition.rule_key.asc())))
        freshness_limit = int(session.get(Configuration, "historian_context_fresh_seconds").value)
        current_time = _utc(self.clock())
        facts_by_category = {
            category: next((fact for fact in facts if fact.category == category and fact.is_complete and (current_time - _utc(fact.effective_at)).total_seconds() <= freshness_limit), None)
            for category in REQUIRED_CATEGORIES
        }
        missing = [category for category in REQUIRED_CATEGORIES if facts_by_category[category] is None]
        evaluations = []
        for rule in rules:
            fact = facts_by_category.get(rule.category)
            if fact is None or not rule.required:
                continue
            evaluation = HistorianRuleEvaluation(
                patient_id=patient_id,
                evidence_id=evidence.evidence_id,
                rule_id=rule.rule_id,
                fact_id=fact.fact_id,
                rule_key=rule.rule_key,
                rule_version=rule.version,
                delta=rule.delta,
                explanation=rule.explanation,
                evaluated_at=self.clock(),
            )
            session.add(evaluation)
            evaluations.append((rule, fact, evaluation))
        session.flush()
        baseline = max(0.0, min(1.0, evidence.score))
        contextual = None if missing else max(0.0, min(1.0, baseline + sum(rule.delta for rule, _fact, _evaluation in evaluations)))
        current_prediction = PredictionResponse(
            patient_id=patient_id,
            bed_id=bed.bed_id,
            event=evidence.event,
            probability=evidence.probability,
            score=evidence.score,
            level=evidence.level,
            horizon_minutes=evidence.horizon_minutes,
            timestamp=_utc(observation.observed_at),
            current_vitals=self._vitals_response(observation, patient, bed),
            provenance=SyntheticProvenance(source_kind=evidence.synthetic_source_kind, source_name=evidence.synthetic_source_name, scenario_id=evidence.synthetic_scenario_id, scenario_version=evidence.synthetic_scenario_version, is_live_bedside_feed=False),
            prototype_label=evidence.prototype_label,
            contract_version=evidence.prediction_contract_version,
            source_kind=evidence.source_kind,
            source_version=evidence.source_version,
            fallback_reason=evidence.fallback_reason,
        )

    def _vitals_response(self, observation, patient, bed):
        return VitalObservationResponse(
            patient_id=observation.patient_id,
            patient=PatientSummary(patient_id=patient.patient_id, display_name=patient.display_name, bed_id=bed.bed_id, unit=bed.unit),
            bed_id=observation.bed_id,
            unit=bed.unit,
            sequence=observation.sequence,
            observed_at=_utc(observation.observed_at),
            received_at=_utc(observation.received_at),
            spo2_percent=observation.spo2_percent,
            heart_rate_bpm=observation.heart_rate_bpm,
            respiratory_rate_bpm=observation.respiratory_rate_bpm,
            systolic_bp_mmhg=observation.systolic_bp_mmhg,
            diastolic_bp_mmhg=observation.diastolic_bp_mmhg,
            temperature_c=observation.temperature_c,
            provenance=SyntheticProvenance(source_kind="synthetic", source_name="acuitynet-simulator", scenario_id=observation.scenario_id, scenario_version=observation.scenario_version, is_live_bedside_feed=False),
            freshness=resolve_freshness(observation.received_at, self.clock()),
            prototype_label="Research prototype: simulated ICU data, not clinical advice.",
        )
        annotations = list(session.scalars(select(TimelineAnnotation).where(TimelineAnnotation.patient_id == patient_id).order_by(TimelineAnnotation.created_at.asc(), TimelineAnnotation.annotation_id.asc())))
        alert = session.scalar(select(Alert).where(Alert.patient_id == patient_id).order_by(Alert.alert_id.desc()))
        timeline = self.timeline(session, patient_id, facts, evidence, alert, annotations, evaluations)
        return HistorianResponse(
            patient_id=patient_id,
            patient_name=patient.display_name,
            admission_id=admission.admission_id,
            admitted_at=_utc(admission.admitted_at),
            bed_id=bed.bed_id,
            unit=bed.unit,
            current_prediction=current_prediction,
            baseline_score=round(baseline, 6),
            contextual_status="incomplete" if missing else "complete",
            contextual_score=None if contextual is None else round(contextual, 6),
            facts=[HistorianFact.model_validate(fact, from_attributes=True) for fact in facts],
            rule_evaluations=[RuleEvaluation(rule_key=rule.rule_key, rule_name=rule.name, rule_version=rule.version, category=rule.category, fact_id=fact.fact_id, delta=rule.delta, explanation=rule.explanation, evaluated_at=_utc(evaluation.evaluated_at)) for rule, fact, evaluation in evaluations],
            missing_evidence=missing,
            annotations=[AnnotationResponse.model_validate(annotation, from_attributes=True) for annotation in annotations],
            alert=None if alert is None else self.alert_service.to_response(session, alert, alert.deduplication_status),
            timeline=timeline,
            prototype_label=evidence.prototype_label,
            provenance="research-prototype",
        )

    def timeline(self, session, patient_id, facts, evidence, alert, annotations, evaluations):
        entries = [TimelineEntry(entry_id=f"fact:{fact.fact_id}", entry_type="fact", occurred_at=_utc(fact.effective_at), title=fact.category, detail=f"{fact.label}: {fact.value or ''}".strip()) for fact in facts]
        entries.append(TimelineEntry(entry_id=f"prediction:{evidence.evidence_id}", entry_type="prediction", occurred_at=_utc(evidence.server_timestamp), title="Baseline prediction", detail=f"{evidence.event} ({evidence.score:.2f})"))
        if alert is not None:
            entries.append(TimelineEntry(entry_id=f"alert:{alert.alert_id}", entry_type="alert", occurred_at=_utc(alert.created_at), title="Alert generated", detail=alert.priority))
        entries.extend(
            TimelineEntry(entry_id=f"rule:{evaluation.evaluation_id}", entry_type="fact", occurred_at=_utc(evaluation.evaluated_at), title=rule.rule_key, detail=f"delta {rule.delta:+.2f}")
            for rule, _fact, evaluation in evaluations
        )
        for event in AuditRepository(session).list_for_patient(patient_id):
            entries.append(TimelineEntry(entry_id=f"audit:{event.audit_id}", entry_type="audit", occurred_at=_utc(event.occurred_at), title=event.action, detail=event.outcome))
        entries.extend( TimelineEntry(entry_id=f"annotation:{annotation.annotation_id}", entry_type="annotation", occurred_at=_utc(annotation.created_at), title="Doctor annotation", detail=annotation.text) for annotation in annotations)
        return sorted(entries, key=lambda entry: (entry.occurred_at, entry.entry_id))

    def annotate(self, session, patient_id, actor, text):
        annotation = TimelineAnnotation(patient_id=patient_id, author_id=actor.user_id, text=text, created_at=self.clock(), source_label="doctor-authored")
        session.add(annotation)
        session.flush()
        self.audit_service.record(session, actor_id=actor.user_id, action="annotation.created", resource_type="patient", resource_id=patient_id, outcome="success", details={"patient_id": patient_id, "annotation_id": annotation.annotation_id}, occurred_at=annotation.created_at)
        return AnnotationResponse.model_validate(annotation, from_attributes=True)