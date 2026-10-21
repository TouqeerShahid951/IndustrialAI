from enum import Enum
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class Capability(str, Enum):
    fire = 'fire'
    smoke = 'smoke'
    smoking = 'smoking'
    no_helmet = 'no_helmet'
    intrusion = 'intrusion'


class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)


class Login(StrictModel):
    password: str = Field(min_length=1, max_length=256)


class Zone(StrictModel):
    name: str = Field(min_length=1, max_length=80)
    points: list[tuple[float, float]] = Field(min_length=3, max_length=32)


class Analysis(StrictModel):
    request_id: UUID
    capabilities: list[Capability] = Field(min_length=1, max_length=5)
    zones: list[Zone] = Field(default_factory=list, max_length=8)
    device: Literal['mps', 'cpu'] = 'mps'
    camera: str = Field(default='', max_length=100)


class Review(StrictModel):
    request_id: UUID
    decision: Literal['confirmed', 'false_alarm', 'uncertain']
    note: str = Field(default='', max_length=1000)
    expected_version: int = Field(ge=0)


class InitialReview(StrictModel):
    decision: Literal['confirmed', 'uncertain']
    note: str = Field(default='', max_length=1000)


class ManualIncident(StrictModel):
    request_id: UUID
    kind: Capability
    start: float = Field(ge=0)
    end: float = Field(ge=0)
    initial_review: InitialReview


class Export(StrictModel):
    request_id: UUID
    format: Literal['csv', 'json', 'mp4']
    incident_id: UUID | None = None
