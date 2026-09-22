from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class ApplicationCreate(BaseModel):
    full_name: str = Field(min_length=2)
    scheme_id: str = Field(pattern="^(NFST|NOS)$")
    applicant_id: Optional[str] = None
    gender: str = "F"
    category: str = "ST"
    tribe: Optional[str] = None
    is_pvtg: bool = False
    state: str = "Jharkhand"
    age: int = Field(default=25, ge=10, le=80)
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    institution: Optional[str] = None
    annual_income: float = Field(ge=0)
    marks_percentage: float = Field(ge=0, le=100)
    claimed_fee: float = Field(default=0, ge=0)


class ApplicationUpdate(BaseModel):
    full_name: Optional[str] = None
    gender: Optional[str] = None
    category: Optional[str] = None
    tribe: Optional[str] = None
    is_pvtg: Optional[bool] = None
    state: Optional[str] = None
    age: Optional[int] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    course: Optional[str] = None
    institution: Optional[str] = None
    annual_income: Optional[float] = None
    marks_percentage: Optional[float] = None
    claimed_fee: Optional[float] = None


class EvaluateRequest(BaseModel):
    annual_income: Optional[float] = None
    marks_percentage: Optional[float] = None
    age: Optional[int] = None
    category: Optional[str] = "ST"
    gender: Optional[str] = None
    is_pvtg: Optional[bool] = False
    documents: Optional[list[str]] = None


class ActionRequest(BaseModel):
    reason: str = Field(min_length=3)


class NSPImportRequest(BaseModel):
    count: int = Field(default=2, ge=1, le=10)
    scheme_id: Optional[str] = None


# ---------- serializers (plain dicts keep the MVP fast) ----------

def _iso(v: Any):
    if isinstance(v, datetime):
        if v.tzinfo is None:  # SQLite drops tzinfo; values are stored in UTC
            v = v.replace(tzinfo=timezone.utc)
        return v.isoformat()
    return v


def row_to_dict(obj, exclude: tuple = ()) -> dict:
    out = {}
    for col in obj.__table__.columns:
        if col.name in exclude:
            continue
        out[col.name] = _iso(getattr(obj, col.name))
    return out


def user_to_dict(u) -> dict:
    return row_to_dict(u, exclude=("hashed_password",))


def document_to_dict(d) -> dict:
    data = row_to_dict(d)
    data["download_url"] = f"/api/v1/documents/{d.id}/file"
    return data
