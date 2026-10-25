from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

Role = Literal["admin", "analyst", "viewer"]
AssetKind = Literal["laptop", "desktop", "server", "network", "other"]
AssetStatus = Literal["active", "maintenance", "retired"]
Severity = Literal["low", "medium", "high", "critical"]
IncidentStatus = Literal["open", "investigating", "resolved"]


class Model(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)
    password: str = Field(min_length=12, max_length=128)
    role: Role = "viewer"


class UserOut(Model):
    id: int
    email: EmailStr
    full_name: str
    role: Role
    created_at: datetime


class AssetCreate(BaseModel):
    tag: str = Field(min_length=2, max_length=40, pattern=r"^[a-zA-Z0-9_.-]+$")
    name: str = Field(min_length=2, max_length=120)
    kind: AssetKind
    status: AssetStatus = "active"
    assigned_to: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=120)

    @field_validator("tag")
    @classmethod
    def normalize_tag(cls, v: str) -> str:
        return v.upper()


class AssetUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    kind: AssetKind | None = None
    status: AssetStatus | None = None
    assigned_to: str | None = Field(default=None, max_length=120)
    location: str | None = Field(default=None, max_length=120)


class AssetOut(Model):
    id: int
    tag: str
    name: str
    kind: AssetKind
    status: AssetStatus
    assigned_to: str | None
    location: str | None
    created_at: datetime
    updated_at: datetime


class IncidentCreate(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    description: str = Field(min_length=5, max_length=4000)
    severity: Severity = "medium"
    asset_id: int | None = Field(default=None, gt=0)
    assigned_to: str | None = Field(default=None, max_length=120)


class IncidentUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=180)
    description: str | None = Field(default=None, min_length=5, max_length=4000)
    severity: Severity | None = None
    status: IncidentStatus | None = None
    asset_id: int | None = Field(default=None, gt=0)
    assigned_to: str | None = Field(default=None, max_length=120)


class IncidentOut(Model):
    id: int
    title: str
    description: str
    severity: Severity
    status: IncidentStatus
    asset_id: int | None
    created_by_id: int
    assigned_to: str | None
    created_at: datetime
    updated_at: datetime


class AuditOut(Model):
    id: int
    actor_email: str
    action: str
    resource_type: str
    resource_id: int
    details: str
    created_at: datetime


class DashboardOut(BaseModel):
    total_assets: int
    active_assets: int
    open_incidents: int
    critical_incidents: int
    recent_incidents: list[IncidentOut]
    recent_audit: list[AuditOut]
