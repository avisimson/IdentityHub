"""External API router — programmatic ticket creation via API key.

Implements ``POST /api/v1/tickets`` per docs/backend_hld.md § 6.5.
Authentication uses the ``X-API-Key`` header (§ 5.3, § 10.3).
Rate-limited to 20 req/min per API key (§ 7).
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.api_keys.service import ApiKeyService
from app.database import get_db
from app.external.schemas import ExternalCreateTicketRequest, ExternalTicketResponse
from app.jira.schemas import CreateTicketRequest
from app.jira.service import JiraAPIError, JiraNotConnectedError, JiraService
from app.rate_limit import get_api_key_or_ip, limiter
from app.models.api_key import ApiKey
from app.models.user import User

logger = logging.getLogger(__name__)

external_api_key_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)

router = APIRouter(prefix="/api/v1", tags=["External API"])


async def _validate_api_key(
    api_key_header: str | None = Security(external_api_key_scheme),
    db: AsyncSession = Depends(get_db),
) -> tuple[ApiKey, User]:
    """Dependency that validates the X-API-Key header.

    Delegates to ``ApiKeyService.validate_api_key`` which raises 401 with
    ``INVALID_API_KEY`` or ``API_KEY_REVOKED`` as appropriate.
    """
    if api_key_header is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
            headers={"X-Error-Code": "INVALID_API_KEY"},
        )
    return await ApiKeyService.validate_api_key(api_key_header, db)


@router.post(
    "/tickets",
    response_model=ExternalTicketResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"description": "Invalid or revoked API key"},
        403: {"description": "API key owner has no Jira connection"},
        429: {"description": "Rate limit exceeded (20 req/min per API key)"},
        502: {"description": "Upstream Jira API failure"},
    },
)
@limiter.limit("20/minute", key_func=get_api_key_or_ip)
async def create_ticket_external(
    request: Request,
    body: ExternalCreateTicketRequest,
    key_and_user: tuple[ApiKey, User] = Depends(_validate_api_key),
    db: AsyncSession = Depends(get_db),
) -> ExternalTicketResponse:
    """Create a Jira ticket on behalf of the API key owner.

    The ticket is created under the key owner's Jira identity.
    """
    _api_key, user = key_and_user

    jira_payload = CreateTicketRequest(
        project_key=body.project_key,
        summary=body.summary,
        description=body.description,
        issue_type=body.issue_type,
    )

    try:
        ticket = await JiraService.create_ticket(
            str(user.id), jira_payload, "api", db
        )
    except JiraNotConnectedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API key owner has no Jira connection",
            headers={"X-Error-Code": "JIRA_NOT_CONNECTED"},
        )
    except JiraAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Jira API error: {exc}",
            headers={"X-Error-Code": "JIRA_API_ERROR"},
        )

    return ExternalTicketResponse(
        jira_ticket_key=ticket.jira_ticket_key,
        jira_ticket_url=ticket.jira_ticket_url,
        summary=ticket.summary,
        created_at=ticket.created_at,
    )
