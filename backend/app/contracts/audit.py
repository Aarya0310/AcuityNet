from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class AuditEventResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    audit_id: int
    sequence: int
    actor_id: str | None
    action: str = Field(min_length=1, max_length=80)
    category: Literal["alert", "configuration", "access", "assignment", "lifecycle"]
    resource_type: str
    resource_id: str | None
    outcome: Literal["success", "denied", "rejected"]
    resulting_state: str | None
    occurred_at: datetime
    correlation_id: str
    details: dict


class AuditEventListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    events: list[AuditEventResponse]