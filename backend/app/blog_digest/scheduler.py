"""APScheduler configuration for the NHI Blog Digest cron job.

Runs ``BlogDigestService.run_digest()`` daily at 09:00 UTC by default.
See docs/backend_hld.md § 9.
"""

from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.blog_digest.service import BlogDigestService
from app.database import async_session_factory

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _run_digest_job() -> None:
    """Wrapper executed by APScheduler on each trigger.

    Opens its own DB session so the job is fully self-contained.
    """
    logger.info("Blog digest cron job triggered")
    async with async_session_factory() as db:
        await BlogDigestService.run_digest(db)
    logger.info("Blog digest cron job finished")


def start_scheduler() -> None:
    """Add the blog-digest job and start the scheduler."""
    scheduler.add_job(
        _run_digest_job,
        trigger=CronTrigger(hour=9, minute=0, timezone="UTC"),
        id="blog_digest",
        name="NHI Blog Digest",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Blog digest scheduler started (daily 09:00 UTC)")


def stop_scheduler() -> None:
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        logger.info("Blog digest scheduler stopped")


def get_schedule() -> dict:
    """Return the current cron trigger config from the live scheduler."""
    job = scheduler.get_job("blog_digest")
    if job is None:
        return {"hour": 9, "minute": 0, "timezone": "UTC", "enabled": False}

    trigger = job.trigger
    hour = trigger.fields[5].expressions[0].first
    minute = trigger.fields[6].expressions[0].first
    timezone = str(trigger.timezone)
    enabled = job.next_run_time is not None

    return {"hour": hour, "minute": minute, "timezone": timezone, "enabled": enabled}


def update_schedule(hour: int, minute: int, timezone: str, enabled: bool) -> None:
    """Reschedule / pause / resume the blog_digest job at runtime."""
    scheduler.reschedule_job(
        "blog_digest",
        trigger=CronTrigger(hour=hour, minute=minute, timezone=timezone),
    )
    if enabled:
        scheduler.resume_job("blog_digest")
    else:
        scheduler.pause_job("blog_digest")
    logger.info(
        "Blog digest schedule updated: %02d:%02d %s (enabled=%s)",
        hour, minute, timezone, enabled,
    )
