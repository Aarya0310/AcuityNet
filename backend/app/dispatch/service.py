import hashlib
import json
from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import select

from backend.app.admin.configuration import effective_settings
from backend.app.contracts.dispatch import DispatchEvaluationResponse
from backend.app.persistence.models import Alert, DispatchDecision, DispatchEvaluation, Nurse, PredictionEvidence
from backend.app.safety.labels import PROTOTYPE_LABEL


WEIGHTS = {"availability": 0.40, "proximity": 0.30, "workload": 0.20, "acuity_compatibility": 0.10}


class DispatchConflict(ValueError):
    pass


class DispatchService:
    def __init__(self, clock, lifecycle_service, alert_service, audit_service):
        self.clock = clock
        self.lifecycle_service = lifecycle_service
        self.alert_service = alert_service
        self.audit_service = audit_service

    def _utc(self, value):
        return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value

    def _settings(self, session):
        settings = effective_settings(session)
        settings.setdefault("dispatch_status_fresh_seconds", "60")
        settings.setdefault("dispatch_workload_fresh_seconds", "60")
        settings.setdefault("dispatch_proximity_fresh_seconds", "300")
        settings.setdefault("dispatch_alert_fresh_seconds", "300")
        return settings

    def _alert(self, session, patient_id):
        alert = session.scalar(select(Alert).where(Alert.patient_id == patient_id, Alert.state != "resolved").order_by(Alert.alert_id.desc()))
        if alert is None:
            raise LookupError("Alert unavailable")
        evidence = session.get(PredictionEvidence, alert.evidence_id)
        if evidence is None:
            raise LookupError("Alert evidence unavailable")
        return alert, evidence

    def _candidate_data(self, session, nurse, now, settings):
        reasons = []
        if not nurse.user_id or not nurse.user or not nurse.user.active:
            reasons.append("missing active nurse identity")
        if nurse.status_updated_at is None:
            reasons.append("missing status freshness")
        elif (now - self._utc(nurse.status_updated_at)).total_seconds() > int(settings["dispatch_status_fresh_seconds"]):
            reasons.append("stale status")
        if not nurse.available:
            reasons.append("unavailable")
        for field, label in (("workload_active", "workload"), ("workload_capacity", "workload capacity"), ("proximity_km", "proximity"), ("acuity_compatibility", "acuity compatibility")):
            if getattr(nurse, field) is None:
                reasons.append(f"missing {label}")
        if nurse.workload_capacity is not None and nurse.workload_capacity <= 0:
            reasons.append("invalid workload capacity")
        if nurse.workload_updated_at is None:
            reasons.append("missing workload freshness")
        elif (now - self._utc(nurse.workload_updated_at)).total_seconds() > int(settings["dispatch_workload_fresh_seconds"]):
            reasons.append("stale workload")
        if nurse.proximity_updated_at is None:
            reasons.append("missing proximity freshness")
        elif (now - self._utc(nurse.proximity_updated_at)).total_seconds() > int(settings["dispatch_proximity_fresh_seconds"]):
            reasons.append("stale proximity")
        if nurse.acuity_updated_at is None:
            reasons.append("missing acuity freshness")
        if reasons:
            return {
                "nurse_id": nurse.nurse_id,
                "display_name": nurse.display_name,
                "eligible": False,
                "exclusion_reasons": reasons,
                "rank": None,
                "score": None,
                "components": {},
                "contributions": {},
                "proximity_km": nurse.proximity_km,
                "workload_active": nurse.workload_active,
                "workload_capacity": nurse.workload_capacity,
                "acuity_compatibility": nurse.acuity_compatibility,
                "freshness": {"status": nurse.status_updated_at, "workload": nurse.workload_updated_at, "proximity": nurse.proximity_updated_at, "acuity": nurse.acuity_updated_at},
            }
        components = {
            "availability": 1.0 if nurse.available else 0.0,
            "proximity": max(0.0, min(1.0, float(nurse.proximity_km))),
            "workload": max(0.0, min(1.0, 1 - (float(nurse.workload_active) / float(nurse.workload_capacity)))),
            "acuity_compatibility": max(0.0, min(1.0, float(nurse.acuity_compatibility))),
        }
        contributions = {key: round(components[key] * WEIGHTS[key], 6) for key in WEIGHTS}
        return {
            "nurse_id": nurse.nurse_id,
            "display_name": nurse.display_name,
            "eligible": True,
            "exclusion_reasons": [],
            "rank": None,
            "score": round(sum(contributions.values()), 6),
            "components": components,
            "contributions": contributions,
            "proximity_km": nurse.proximity_km,
            "workload_active": nurse.workload_active,
            "workload_capacity": nurse.workload_capacity,
            "acuity_compatibility": nurse.acuity_compatibility,
            "freshness": {"status": nurse.status_updated_at, "workload": nurse.workload_updated_at, "proximity": nurse.proximity_updated_at, "acuity": nurse.acuity_updated_at},
        }

    def _source_fingerprint(self, alert, evidence, candidates):
        payload = {"alert_id": alert.alert_id, "state": alert.state, "evidence_id": evidence.evidence_id, "evidence_timestamp": self._utc(evidence.server_timestamp).isoformat(), "candidates": candidates}
        return hashlib.sha256(json.dumps(payload, default=str, sort_keys=True).encode()).hexdigest()

    def _alert_is_fresh(self, evidence, now, settings):
        return (now - self._utc(evidence.server_timestamp)).total_seconds() <= int(settings["dispatch_alert_fresh_seconds"])

    def _response(self, snapshot):
        values = {
            "evaluation_id": snapshot.evaluation_id,
            "patient_id": snapshot.patient_id,
            "alert_id": snapshot.alert_id,
            "evidence_id": snapshot.evidence_id,
            "created_at": snapshot.created_at,
            "alert_fresh_at": snapshot.alert_fresh_at,
            "candidate_fresh_at": snapshot.candidate_fresh_at,
            "status": snapshot.status,
            "recommendation_nurse_id": snapshot.recommendation_nurse_id,
            "weights": json.loads(snapshot.weights),
            "candidates": json.loads(snapshot.candidates),
            "exclusions": json.loads(snapshot.exclusions),
            "recommendation_context": snapshot.recommendation_context,
            "prototype_label": snapshot.prototype_label,
        }
        return DispatchEvaluationResponse.model_validate(values)

    def evaluate(self, session, patient_id, actor=None, retry=False):
        alert, evidence = self._alert(session, patient_id)
        now = self._utc(self.clock())
        settings = self._settings(session)
        all_candidates = [self._candidate_data(session, nurse, now, settings) for nurse in session.scalars(select(Nurse).order_by(Nurse.nurse_id))]
        eligible = [item for item in all_candidates if item["eligible"]]
        eligible.sort(key=lambda item: (-item["score"], -item["components"]["availability"], -item["components"]["proximity"], -item["components"]["workload"], -item["components"]["acuity_compatibility"], item["nurse_id"]))
        for rank, item in enumerate(eligible, start=1):
            item["rank"] = rank
        exclusions = [item for item in all_candidates if not item["eligible"]]
        fresh_times = [item["freshness"][key] for item in eligible for key in ("status", "workload", "proximity", "acuity") if item["freshness"][key] is not None]
        candidate_fresh_at = min([self._utc(value) for value in fresh_times], default=now)
        alert_fresh = self._alert_is_fresh(evidence, now, settings)
        status = "ready" if eligible and alert_fresh else "blocked" if not alert_fresh else "no_eligible_candidate"
        recommendation = eligible[0]["nurse_id"] if status == "ready" else None
        snapshot_candidates = sorted(eligible + exclusions, key=lambda item: item["nurse_id"])
        fingerprint = self._source_fingerprint(alert, evidence, snapshot_candidates)
        snapshot = DispatchEvaluation(
            evaluation_id=f"DPE-{uuid4().hex[:24]}", patient_id=patient_id, alert_id=alert.alert_id, evidence_id=evidence.evidence_id, created_at=now,
            alert_fresh_at=self._utc(evidence.server_timestamp), candidate_fresh_at=candidate_fresh_at, status=status,
            recommendation_nurse_id=recommendation, weights=json.dumps(WEIGHTS, sort_keys=True), candidates=json.dumps(eligible, default=str, sort_keys=True), exclusions=json.dumps(exclusions, default=str, sort_keys=True), source_fingerprint=fingerprint,
            recommendation_context="Ranked synthetic prototype recommendation; human confirmation required." if recommendation else "No eligible candidate or fresh alert evidence; alert remains generated and unassigned.", prototype_label=PROTOTYPE_LABEL,
        )
        session.add(snapshot)
        session.flush()
        if self.audit_service:
            self.audit_service.record(session, actor_id=None if actor is None else actor.user_id, action="dispatch.retry" if retry else "dispatch.evaluated", resource_type="alert", resource_id=str(alert.alert_id), outcome="blocked" if not eligible else "success", details={"patient_id": patient_id, "evaluation_id": snapshot.evaluation_id, "status": status, "retry": retry}, occurred_at=now)
        return self._response(snapshot)

    def decide(self, session, patient_id, request, actor, decision_type):
        if actor.role not in {"admin", "doctor"}:
            raise PermissionError("Forbidden")
        snapshot = session.get(DispatchEvaluation, request.evaluation_id)
        if snapshot is None or snapshot.patient_id != patient_id:
            raise LookupError("Evaluation unavailable")
        alert, evidence = self._alert(session, patient_id)
        if alert.alert_id != snapshot.alert_id or alert.state != "generated" or evidence.evidence_id != snapshot.evidence_id:
            raise DispatchConflict("Evaluation is stale; recompute before deciding")
        if not self._alert_is_fresh(evidence, self._utc(self.clock()), self._settings(session)):
            raise DispatchConflict("Alert evidence is stale; recompute before deciding")
        current = self.evaluate_inputs(session, alert, evidence)
        if current != snapshot.source_fingerprint:
            raise DispatchConflict("Evaluation is stale; recompute before deciding")
        candidates = json.loads(snapshot.candidates)
        selected = next((item for item in candidates if item["nurse_id"] == request.nurse_id), None)
        if selected is None or not selected["eligible"]:
            raise DispatchConflict("Selected nurse is no longer eligible")
        reason = request.reason.strip()
        if len(reason) < 3:
            raise ValueError("Reason is required")
        evidence_summary = {"evaluation_id": snapshot.evaluation_id, "decision_type": decision_type, "selected_nurse_id": request.nurse_id, "rank": selected["rank"], "score": selected["score"], "components": selected["components"], "weights": json.loads(snapshot.weights), "alert_fresh_at": snapshot.alert_fresh_at.isoformat(), "candidate_fresh_at": snapshot.candidate_fresh_at.isoformat(), "recommendation_context": snapshot.recommendation_context, "reason": reason}
        compact = json.dumps({"evaluation_id": snapshot.evaluation_id, "decision_type": decision_type, "selected_nurse_id": request.nurse_id, "reason": reason}, separators=(",", ":"))
        if len(compact) > 240:
            raise ValueError("Reason is too long for assignment evidence")
        from backend.app.contracts.alerts import AlertLifecycleCommand
        self.lifecycle_service.transition(session, alert, AlertLifecycleCommand(action="assign", assignment_id=request.nurse_id, assignment_evidence=compact), actor)
        decision = DispatchDecision(evaluation_id=snapshot.evaluation_id, alert_id=alert.alert_id, actor_id=actor.user_id, decision_type=decision_type, selected_nurse_id=request.nurse_id, reason=reason, evidence=json.dumps(evidence_summary, default=str, sort_keys=True), created_at=self._utc(self.clock()))
        session.add(decision)
        session.flush()
        self.audit_service.record(session, actor_id=actor.user_id, action=f"dispatch.{decision_type}", resource_type="alert", resource_id=str(alert.alert_id), outcome="success", details={"evaluation_id": snapshot.evaluation_id, "decision_type": decision_type, "selected_nurse_id": request.nurse_id, "reason": reason}, occurred_at=decision.created_at)
        return alert

    def evaluate_inputs(self, session, alert, evidence):
        now = self._utc(self.clock())
        settings = self._settings(session)
        all_candidates = [self._candidate_data(session, nurse, now, settings) for nurse in session.scalars(select(Nurse).order_by(Nurse.nurse_id))]
        eligible = [item for item in all_candidates if item["eligible"]]
        eligible.sort(key=lambda item: (-item["score"], -item["components"]["availability"], -item["components"]["proximity"], -item["components"]["workload"], -item["components"]["acuity_compatibility"], item["nurse_id"]))
        for rank, item in enumerate(eligible, start=1):
            item["rank"] = rank
        exclusions = [item for item in all_candidates if not item["eligible"]]
        snapshot_candidates = sorted(eligible + exclusions, key=lambda item: item["nurse_id"])
        return self._source_fingerprint(alert, evidence, snapshot_candidates)
