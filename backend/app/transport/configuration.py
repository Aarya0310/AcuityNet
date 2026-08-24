from sqlalchemy.orm import Session

from backend.app.contracts.configuration import RefreshConfiguration
from backend.app.persistence.models import Configuration


def refresh_configuration(session: Session) -> RefreshConfiguration:
    row = session.get(Configuration, "refresh_intervals")
    if row is None:
        raise ValueError("Refresh configuration unavailable")
    intervals = tuple(
        int(value) if value.isdigit() else value
        for value in row.value.split(",")
    )
    return RefreshConfiguration(supported_intervals=intervals, default_interval=10)