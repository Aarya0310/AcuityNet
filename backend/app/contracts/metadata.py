from typing import Literal

from pydantic import BaseModel

from backend.app.safety.labels import (
    PROTOTYPE_LABEL,
    SYNTHETIC_SOURCE_KIND,
    SYNTHETIC_SOURCE_NAME,
)


class SafetyMetadata(BaseModel):
    prototype_label: Literal[PROTOTYPE_LABEL] = PROTOTYPE_LABEL
    source_kind: Literal[SYNTHETIC_SOURCE_KIND] = SYNTHETIC_SOURCE_KIND
    source_name: Literal[SYNTHETIC_SOURCE_NAME] = SYNTHETIC_SOURCE_NAME
    is_live_bedside_feed: Literal[False] = False


class HealthResponse(BaseModel):
    status: Literal["ok"]
    metadata: SafetyMetadata