from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str


class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6)
    role: str = "USER"


class UserLogin(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class SessionCreate(BaseModel):
    user_id: Optional[int] = None
    session_name: Optional[str] = None


class EventCreate(BaseModel):
    session_id: Optional[int] = None
    event_type: str = "warning"
    drowsiness_level: str = "ALERT"
    eye_status: str = "OPEN"
    ear: Optional[float] = None
    blink_count: Optional[int] = None
    yawn_count: Optional[int] = None
    head_direction: Optional[str] = None
    safety_score: Optional[int] = None
