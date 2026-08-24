from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RefreshInterval = Literal[5, 10, 30, "manual"]


class RefreshConfiguration(BaseModel):
    supported_intervals: tuple[RefreshInterval, ...]
    default_interval: Literal[5, 10, 30]


class RefreshSettingsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    default_interval: Literal[5, 10, 30]


class RiskThresholdsUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    critical_risk_threshold: float = Field(ge=0, le=1)
    high_risk_threshold: float = Field(ge=0, le=1)


class ResearchRulesUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    research_rules_version: str = Field(min_length=1, max_length=40)