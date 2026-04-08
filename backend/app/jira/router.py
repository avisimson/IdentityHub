"""Jira router — OAuth flow, project browsing, and ticket management.

Implements the 8 Jira endpoints defined in docs/backend_hld.md § 6.3.
The ``/jira/auth/callback`` endpoint does NOT require Bearer auth; the user
is identified from the HMAC-signed ``state`` parameter instead.
"""

import logging
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import MessageResponse
from app.database import get_db
from app.dependencies import get_current_user
from app.jira.schemas import (
    AuthUrlResponse,
    CreateTicketRequest,
    IssueTypesResponse,
    JiraStatusResponse,
    ProjectsResponse,
    TicketResponse,
    TicketsListResponse,
)
from app.jira.service import (
    JiraAPIError,
    JiraNotConnectedError,
    JiraOAuthError,
    JiraService,
)
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jira", tags=["Jira"])

_FRONTEND_CALLBACK_BASE = "http://localhost:3000/jira/connected"


# ---------------------------------------------------------------------------
# 1. GET /jira/auth/url
# ---------------------------------------------------------------------------


@router.get("/auth/url", response_model=AuthUrlResponse)
async def get_auth_url(
    current_user: User = Depends(get_current_user),
) -> AuthUrlResponse:
    """Return the Atlassian OAuth authorization URL for the current user."""
    authorization_url, state_value = JiraService.generate_auth_url(
        str(current_user.id)
    )
    return AuthUrlResponse(authorization_url=authorization_url, state=state_value)


# ---------------------------------------------------------------------------
# 2. GET /jira/auth/callback  (NO Bearer auth — user from state param)
# ---------------------------------------------------------------------------


@router.get("/auth/callback")
async def auth_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
) -> RedirectResponse:
    """Atlassian OAuth redirect callback.

    Exchanges the authorization code for tokens and redirects the browser
    back to the React frontend with a status query parameter.
    """
    try:
        await JiraService.handle_callback(code, state, db)
    except (JiraOAuthError, JiraAPIError) as exc:
        logger.warning("Jira OAuth callback failed: %s", exc)
        params = urlencode({"status": "error", "message": str(exc)})
        return RedirectResponse(
            url=f"{_FRONTEND_CALLBACK_BASE}?{params}",
            status_code=status.HTTP_302_FOUND,
        )
    except Exception as exc:
        logger.exception("Unexpected error during Jira OAuth callback")
        params = urlencode({"status": "error", "message": "An unexpected error occurred during Jira authentication"})
        return RedirectResponse(
            url=f"{_FRONTEND_CALLBACK_BASE}?{params}",
            status_code=status.HTTP_302_FOUND,
        )

    return RedirectResponse(
        url=f"{_FRONTEND_CALLBACK_BASE}?status=success",
        status_code=status.HTTP_302_FOUND,
    )


# ---------------------------------------------------------------------------
# 3. GET /jira/status
# ---------------------------------------------------------------------------


@router.get("/status", response_model=JiraStatusResponse)
async def get_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> JiraStatusResponse:
    """Check whether the current user has a connected Jira account.

    Always returns 200 — the ``connected`` boolean distinguishes the states.
    """
    return await JiraService.get_status(str(current_user.id), db)


# ---------------------------------------------------------------------------
# 4. DELETE /jira/connection
# ---------------------------------------------------------------------------


@router.delete("/connection", response_model=MessageResponse)
async def delete_connection(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> MessageResponse:
    """Disconnect the current user's Jira account."""
    await JiraService.disconnect(str(current_user.id), db)
    return MessageResponse(detail="Jira connection removed")


# ---------------------------------------------------------------------------
# 5. GET /jira/projects
# ---------------------------------------------------------------------------


@router.get("/projects", response_model=ProjectsResponse)
async def get_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectsResponse:
    """List accessible Jira projects for the connected user."""
    try:
        projects = await JiraService.get_projects(str(current_user.id), db)
    except JiraNotConnectedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Jira not connected",
            headers={"X-Error-Code": "JIRA_NOT_CONNECTED"},
        )
    except JiraAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Jira API error: {exc}",
            headers={"X-Error-Code": "JIRA_API_ERROR"},
        )
    return ProjectsResponse(projects=projects)


# ---------------------------------------------------------------------------
# 6. GET /jira/projects/{project_key}/issue-types
# ---------------------------------------------------------------------------


@router.get(
    "/projects/{project_key}/issue-types",
    response_model=IssueTypesResponse,
)
async def get_issue_types(
    project_key: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> IssueTypesResponse:
    """List available issue types for a Jira project."""
    try:
        issue_types = await JiraService.get_issue_types(
            str(current_user.id), project_key, db
        )
    except JiraNotConnectedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Jira not connected",
            headers={"X-Error-Code": "JIRA_NOT_CONNECTED"},
        )
    except JiraAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Jira API error: {exc}",
            headers={"X-Error-Code": "JIRA_API_ERROR"},
        )
    return IssueTypesResponse(issue_types=issue_types)


# ---------------------------------------------------------------------------
# 7. POST /jira/tickets
# ---------------------------------------------------------------------------


@router.post(
    "/tickets",
    response_model=TicketResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_ticket(
    body: CreateTicketRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketResponse:
    """Create a Jira ticket. Sets ``source="ui"``."""
    try:
        return await JiraService.create_ticket(
            str(current_user.id), body, "ui", db
        )
    except JiraNotConnectedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Jira not connected",
            headers={"X-Error-Code": "JIRA_NOT_CONNECTED"},
        )
    except JiraAPIError as exc:
        detail = str(exc)
        if "404" in detail or "not found" in detail.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project {body.project_key} not found",
                headers={"X-Error-Code": "JIRA_PROJECT_NOT_FOUND"},
            )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Jira API error: {exc}",
            headers={"X-Error-Code": "JIRA_API_ERROR"},
        )


# ---------------------------------------------------------------------------
# 8. GET /jira/tickets
# ---------------------------------------------------------------------------


@router.get("/tickets", response_model=TicketsListResponse)
async def get_tickets(
    project_key: str = Query(...),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TicketsListResponse:
    """Return recent tickets created through this app for a project."""
    tickets = await JiraService.get_recent_tickets(project_key, limit, db)
    return TicketsListResponse(tickets=tickets)
