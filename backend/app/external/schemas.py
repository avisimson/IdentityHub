"""Pydantic request/response schemas for the external API.

Matches the API contract defined in docs/backend_hld.md § 6.5.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ExternalCreateTicketRequest(BaseModel):
    """POST /api/v1/tickets — request body from external systems."""

    project_key: str
    summary: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=32_000)
    issue_type: str = "Task"


class ExternalTicketResponse(BaseModel):
    """POST /api/v1/tickets — 201 response."""

    model_config = ConfigDict(from_attributes=True)

    jira_ticket_key: str
    jira_ticket_url: str
    summary: str
    created_at: datetime
