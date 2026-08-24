from backend.app.persistence.models import Configuration


DEFAULTS = {"critical_risk_threshold": "0.7", "high_risk_threshold": "0.5", "research_rules_version": "rules.v1"}


def effective_settings(session):
    values = {row.key: row.value for row in session.query(Configuration).all()}
    return {**DEFAULTS, **values}


def update_typed_configuration(session, values: dict[str, str]):
    for key, value in values.items():
        if key not in DEFAULTS: raise ValueError("Unsupported configuration")
        row = session.get(Configuration, key)
        if row is None: session.add(Configuration(key=key, value=value))
        else: row.value = value
    session.flush()
    return effective_settings(session)