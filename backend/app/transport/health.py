from backend.app.contracts.metadata import HealthResponse, SafetyMetadata
from backend.app.safety.labels import PROTOTYPE_LABEL


def health_response() -> HealthResponse:
    return HealthResponse(
        status="ok",
        metadata=SafetyMetadata(prototype_label=PROTOTYPE_LABEL),
    )