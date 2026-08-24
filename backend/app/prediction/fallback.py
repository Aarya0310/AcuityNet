from backend.app.contracts.predictions import PredictionResponse


def deterministic_prediction(observation, vitals, threshold: float = 0.7) -> PredictionResponse:
    score = round(min(1.0, max(0.0, (100 - observation.spo2_percent) / 100 + observation.respiratory_rate_bpm / 200)), 4)
    level = "critical" if score >= threshold else "high" if score >= threshold * 0.75 else "moderate" if score >= threshold * 0.5 else "low"
    return PredictionResponse(patient_id=observation.patient_id, bed_id=observation.bed_id, event="respiratory deterioration", probability=score, score=score, level=level, horizon_minutes=30, timestamp=observation.observed_at, current_vitals=vitals, provenance=vitals.provenance, prototype_label=vitals.prototype_label, contract_version="prediction.v1", source_kind="deterministic_fallback", source_version="rules.v1", fallback_reason="ML provider unavailable")