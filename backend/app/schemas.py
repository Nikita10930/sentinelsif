from datetime import date as date_type, datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_validator

# ─── Health check schema ──────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    service: str


# ─── User schemas ─────────────────────────────────────────────────────────────
class UserBase(BaseModel):
    name: str
    email: str
    role: str

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    user_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Report schemas ───────────────────────────────────────────────────────────
class ReportBase(BaseModel):
    date: date_type
    department: str
    location: str
    description: str
    hazard_type: Optional[str] = None
    severity: Optional[str] = None
    risk_score: Optional[float] = 0.0

class ReportCreate(ReportBase):
    pass

class ReportResponse(ReportBase):
    report_id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ─── Classify schemas ─────────────────────────────────────────────────────────
class ClassifyRequest(BaseModel):
    description: str

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v or len(v.strip()) < 5:
            raise ValueError("Description must be at least 5 characters long and non-empty.")
        return v.strip()


class ClassifyResponse(BaseModel):
    hazard_type: str
    hazard_confidence: float
    severity: str
    severity_confidence: float
    used_fallback: bool
    top_keywords: Optional[List[str]] = None


# ─── Report Upload schemas ────────────────────────────────────────────────────
class ReportUploadRequest(BaseModel):
    department: str
    location: str
    description: str
    date: Optional[date_type] = None

    @field_validator("department", "location")
    @classmethod
    def validate_non_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must not be empty.")
        return v.strip()

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        if not v or len(v.strip()) < 5:
            raise ValueError("Description must be at least 5 characters long and non-empty.")
        return v.strip()

class ReportUpdateRequest(BaseModel):
    department: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    date: Optional[date_type] = None

    @field_validator("department", "location")
    @classmethod
    def validate_non_empty(cls, v: Optional[str], info) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError(f"{info.field_name} must not be empty if provided.")
        return v.strip() if v is not None else v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.strip()) < 5:
            raise ValueError("Description must be at least 5 characters long if provided.")
        return v.strip() if v is not None else v


class ReportUploadResponse(BaseModel):
    report_id: int
    date: date_type
    department: str
    location: str
    description: str
    hazard_type: Optional[str] = None
    severity: Optional[str] = None
    risk_score: Optional[float] = 0.0
    created_at: datetime
    possible_duplicate_of: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


# ─── Analytics schemas ────────────────────────────────────────────────────────
class RiskSummaryItem(BaseModel):
    department: str
    location: str
    risk_score: float
    risk_level: str
    report_count: int


class AlertItem(BaseModel):
    department: str
    location: str
    risk_score: float
    report_count: int
    most_recent_report_date: Optional[date_type] = None


# ─── Auth schemas ──────────────────────────────────────────────────────────
class UserRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str  # "worker", "safety_officer", or "admin"

    @field_validator("name", "email")
    @classmethod
    def validate_non_empty(cls, v: str, info) -> str:
        if not v or not v.strip():
            raise ValueError(f"{info.field_name} must not be empty.")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not v or len(v) < 6:
            raise ValueError("Password must be at least 6 characters long.")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"worker", "safety_officer", "admin"}
        if v.strip().lower() not in allowed:
            raise ValueError(f"Role must be one of: {', '.join(allowed)}")
        return v.strip().lower()


class UserLoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str
    role: str