"""Pydantic schemas for the Blog Digest UI API."""

from __future__ import annotations

from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field, field_validator


class BlogDigestTriggerResponse(BaseModel):
    detail: str
    ticket_key: str | None = None


class ScheduleResponse(BaseModel):
    hour: int
    minute: int
    timezone: str
    enabled: bool


class ScheduleUpdateRequest(BaseModel):
    hour: int = Field(ge=0, le=23)
    minute: int = Field(ge=0, le=59)
    timezone: str = "UTC"
    enabled: bool = True

    @field_validator("timezone")
    @classmethod
    def _validate_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (KeyError, ValueError) as exc:
            raise ValueError(f"Invalid IANA timezone: {value}") from exc
        return value
