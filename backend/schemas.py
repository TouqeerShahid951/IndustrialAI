from enum import Enum
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from typing import Any


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


class FramePreview(BaseModel):
    source: float
    artifact_id: str


class MediaMetadata(BaseModel):
    fps: float = 0
    width: int = 0
    height: int = 0
    frames: int = 0
    duration: float
    frame_map: list[tuple[float,float]] = Field(default_factory=list)
    frames_preview: list[FramePreview] = Field(default_factory=list)
    preview_id: str | None = None
    thumbnail_id: str | None = None


class JobConfiguration(BaseModel):
    model_config = ConfigDict(extra='allow')
    capabilities: list[Capability] = Field(default_factory=list)
    zones: list[Zone] = Field(default_factory=list)
    camera: str = ''
    device: Literal['mps','cpu'] = 'mps'
    profile: dict[str,Any] = Field(default_factory=dict)
    models: dict[str,str] = Field(default_factory=dict)


class CapabilityResult(BaseModel):
    status: Literal['pending','completed','failed','disabled']
    assessability: str
    error: str | None = None


class Assessment(BaseModel):
    model_config = ConfigDict(extra='allow')
    person_observations: int
    eligible_smoking_observations: int
    smoking: str
    no_helmet: str
    intrusion: str


class JobResult(BaseModel):
    model_config = ConfigDict(extra='allow')
    capabilities: dict[str,CapabilityResult] = Field(default_factory=dict)
    incident_count: int | None = None
    assessment: Assessment | None = None
    artifact_id: str | None = None
    manifest_id: str | None = None


class IncidentEvidence(BaseModel):
    model_config = ConfigDict(extra='allow')
    label: str = ''
    level: str = ''
    track: int | None = None
    zone: str | None = None
    entry: str | None = None


class JobRecord(BaseModel):
    id: str
    upload_id: str
    kind: Literal['prepare_upload','analyze','export']
    status: Literal['queued','running','completed','partial','failed','cancelled','interrupted']
    config: JobConfiguration
    result: JobResult
    stage: str
    processed: int
    expected: int
    cancel: int
    error: str | None
    request_id: str
    created: str
    updated: str


class UploadRecord(BaseModel):
    id: str
    name: str
    sha256: str
    bytes: int
    metadata: MediaMetadata
    status: Literal['preparing','ready','failed','cancelled','deleting']
    created: str
    jobs: list[JobRecord]


class IncidentRecord(BaseModel):
    id: str
    job_id: str
    kind: Capability
    origin: Literal['model','manual']
    start: float
    end: float
    evidence: IncidentEvidence
    decision: Literal['confirmed','false_alarm','uncertain'] | None
    note: str | None
    version: int | None
    created: str
    reviewed_at: str | None
