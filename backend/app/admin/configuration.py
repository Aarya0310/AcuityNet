from backend.app.persistence.models import Configuration


DEFAULTS = {"critical_risk_threshold": "0.7", "high_risk_threshold": "0.5", "alert_rearm_threshold": "0.1", "alert_cooldown_seconds": "300", "research_rules_version": "rules.v1"}


def effective_settings(session):
    values = {row.key: row.value for row in session.query(Configuration).all()}
    return {**DEFAULTS, **values}


def update_typed_configuration(session, values: dict[str, str]):
    merged = effective_settings(session) | {key: str(value) for key, value in values.items()}
    try:
        critical, high, rearm = (float(merged[key]) for key in ("critical_risk_threshold", "high_risk_threshold", "alert_rearm_threshold"))
        cooldown = int(merged["alert_cooldown_seconds"])
    except (KeyError, TypeError, ValueError) as error:
        raise ValueError("Invalid alert configuration") from error
    if not (0 <= rearm <= high <= critical <= 1) or not 0 <= cooldown <= 86400:
        raise ValueError("Invalid alert configuration")
    for key, value in values.items():
        if key not in DEFAULTS: raise ValueError("Unsupported configuration")
        row = session.get(Configuration, key)
        if row is None: session.add(Configuration(key=key, value=value))
        else: row.value = value
    session.flush()
    return effective_settings(session)