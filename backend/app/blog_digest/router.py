"""Blog Digest router — manual trigger and schedule management.

Exposes endpoints for the frontend to trigger a one-shot blog digest run
and to view / update the cron schedule at runtime.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.blog_digest.schemas import (
    BlogDigestTriggerResponse,
    ScheduleResponse,
    ScheduleUpdateRequest,
)
from app.blog_digest.scheduler import get_schedule, update_schedule
from app.blog_digest.service import BlogDigestError, BlogDigestService
from app.database import get_db
from app.dependencies import get_current_user
from app.jira.service import JiraAPIError, JiraNotConnectedError
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/blog-digest", tags=["Blog Digest"])


@router.post("/trigger", response_model=BlogDigestTriggerResponse)
async def trigger_digest(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BlogDigestTriggerResponse:
    """Manually run the blog digest pipeline using the current user's Jira connection."""
    try:
        ticket_key = await BlogDigestService.run_digest(
            db, user_id=str(current_user.id)
        )
    except JiraNotConnectedError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Jira not connected — connect Jira in Settings first",
            headers={"X-Error-Code": "JIRA_NOT_CONNECTED"},
        )
    except JiraAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Jira API error: {exc}",
            headers={"X-Error-Code": "JIRA_API_ERROR"},
        )
    except BlogDigestError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
            headers={"X-Error-Code": "BLOG_DIGEST_FAILED"},
        )

    if ticket_key is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Blog digest failed — check server logs",
            headers={"X-Error-Code": "BLOG_DIGEST_FAILED"},
        )

    return BlogDigestTriggerResponse(
        detail="Blog digest completed", ticket_key=ticket_key
    )


@router.get("/schedule", response_model=ScheduleResponse)
async def get_digest_schedule(
    current_user: User = Depends(get_current_user),
) -> ScheduleResponse:
    """Return the current blog digest cron schedule."""
    return ScheduleResponse(**get_schedule())


@router.put("/schedule", response_model=ScheduleResponse)
async def update_digest_schedule(
    body: ScheduleUpdateRequest,
    current_user: User = Depends(get_current_user),
) -> ScheduleResponse:
    """Update the blog digest cron schedule at runtime."""
    update_schedule(body.hour, body.minute, body.timezone, body.enabled)
    return ScheduleResponse(
        hour=body.hour,
        minute=body.minute,
        timezone=body.timezone,
        enabled=body.enabled,
    )
