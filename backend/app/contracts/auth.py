from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)


class SessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: "CurrentUserResponse"


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    user_id: str
    username: str
    display_name: str
    role: Literal["admin", "doctor", "nurse"]