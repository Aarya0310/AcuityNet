from typing import Literal

from pydantic import BaseModel


RefreshInterval = Literal[5, 10, 30, "manual"]


class RefreshConfiguration(BaseModel):
    supported_intervals: tuple[RefreshInterval, ...]
    default_interval: Literal[5, 10, 30]