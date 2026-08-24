from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class RealtimeInvalidation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event: Literal["alert.invalidated"]
    patient_id: str = Field(min_length=1, max_length=32)
    alert_id: int | None = Field(default=None, ge=1)
    audit_id: int | None = Field(default=None, ge=1)