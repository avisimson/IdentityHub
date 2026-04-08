"""Pydantic request/response schemas for the Jira domain.

Matches the API contract defined in docs/backend_hld.md § 6.3.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# OAuth schemas
# ---------------------------------------------------------------------------


class AuthUrlResponse(BaseModel):
    """GET /jira/auth/url — authorization URL and CSRF state."""

    authorization_url: str
    state: str


# ---------------------------------------------------------------------------
# Connection status
# ---------------------------------------------------------------------------


class JiraStatusResponse(BaseModel):
    """GET /jira/status — always 200; `connected` distinguishes the states."""

    connected: bool
    cloud_id: str | None = None
    jira_site_url: str | None = None


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


class JiraProject(BaseModel):
    """Single Jira project summary."""

    id: str
    key: str
    name: str
    avatar_url: str | None = None


class ProjectsResponse(BaseModel):
    """GET /jira/projects — list of accessible Jira projects."""

    projects: list[JiraProject]


# ---------------------------------------------------------------------------
# Issue types
# ---------------------------------------------------------------------------


class JiraIssueType(BaseModel):
    """Single Jira issue type within a project."""

    id: str
    name: str
    is_default: bool


class IssueTypesResponse(BaseModel):
    """GET /jira/projects/{project_key}/issue-types."""

    issue_types: list[JiraIssueType]


# ---------------------------------------------------------------------------
# Ticket creation
# ---------------------------------------------------------------------------


class CreateTicketRequest(BaseModel):
    """POST /jira/tickets — request body."""

    project_key: str
    summary: str = Field(max_length=255)
    description: str | None = Field(default=None, max_length=32_000)
    issue_type: str = "Task"


# ---------------------------------------------------------------------------
# Ticket responses (shared between POST and GET /jira/tickets)
# ---------------------------------------------------------------------------


class TicketCreatedBy(BaseModel):
    """Embedded creator info inside a ticket response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    full_name: str


class TicketResponse(BaseModel):
    """Single ticket — used by both POST /jira/tickets (201) and
    GET /jira/tickets (200) so the frontend can do optimistic cache prepend
    without shape mismatches."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    jira_ticket_key: str
    jira_ticket_url: str
    summary: str
    issue_type: str
    source: str
    created_at: datetime
    created_by: TicketCreatedBy


class TicketsListResponse(BaseModel):
    """GET /jira/tickets — paginated list of recent tickets."""

    tickets: list[TicketResponse]
