from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class UserCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=80)
    display_name: str = Field(min_length=1, max_length=120)
    role: Literal["admin", "doctor", "nurse"]
    password: str = Field(min_length=12, max_length=200)


class UserResponse(BaseModel):
    user_id: str; username: str; display_name: str; role: str; active: bool


class KpiValue(BaseModel):
    status: Literal["known", "zero", "not_yet_available"]
    value: float | int | None = None
    source: str


class AdminKpiResponse(BaseModel):
    occupancy: KpiValue; monitored_patients: KpiValue; active_nurses: KpiValue; critical_high_risk_patients: KpiValue; alerts: KpiValue; predictions: KpiValue; response_time: KpiValue; acknowledgement_rate: KpiValue; system_status: KpiValue