from backend.app.admin.configuration import DEFAULTS, update_typed_configuration


def test_alert_configuration_allowlist_is_bounded():
    assert {"critical_risk_threshold", "high_risk_threshold", "alert_rearm_threshold", "alert_cooldown_seconds"}.issubset(DEFAULTS)


def test_alert_configuration_rejects_bad_ordering():
    class Session:
        def query(self, _): return self
        def all(self): return []

    try:
        update_typed_configuration(Session(), {"critical_risk_threshold": "0.2", "high_risk_threshold": "0.3"})
    except ValueError:
        return
    raise AssertionError("invalid threshold ordering was accepted")