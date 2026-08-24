from sqlalchemy import func, select
from backend.app.contracts.admin import AdminKpiResponse, KpiValue
from backend.app.persistence.models import Alert, Bed, Nurse, Patient, VitalObservation


def get_admin_kpis(session):
    count = lambda model: session.scalar(select(func.count()).select_from(model)) or 0
    known = lambda value, source: KpiValue(status="known" if value else "zero", value=value, source=source)
    unavailable = lambda source: KpiValue(status="not_yet_available", source=source)
    alert_count = count(Alert)
    critical_count = session.scalar(select(func.count()).select_from(Alert).where(Alert.priority.in_(("high", "critical")), Alert.state != "resolved")) or 0
    return AdminKpiResponse(occupancy=known(count(Bed), "beds"), monitored_patients=known(count(Patient), "patients"), active_nurses=known(session.scalar(select(func.count()).select_from(Nurse).where(Nurse.available.is_(True))) or 0, "nurses"), critical_high_risk_patients=known(critical_count, "active alert rows"), alerts=known(alert_count, "alerts"), predictions=known(count(VitalObservation), "observations"), response_time=unavailable("Phase 4 response workflow"), acknowledgement_rate=unavailable("Phase 4 response workflow"), system_status=known(1, "database and synthetic scenario"))