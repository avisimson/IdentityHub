"""BlogDigestService — scrape the Oasis Security blog, summarise via LLM, create a Jira ticket.

Implements the NHI Blog Digest automation per docs/backend_hld.md § 9.
"""

from __future__ import annotations

import logging
import uuid

import httpx
from bs4 import BeautifulSoup
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.jira.schemas import CreateTicketRequest
from app.jira.service import JiraService, JiraNotConnectedError
from app.models.user import User


class BlogDigestError(Exception):
    """Raised when the blog digest pipeline fails with a user-facing message."""

logger = logging.getLogger(__name__)

_BLOG_INDEX_URL = "https://oasis.security/blog"

_SUMMARY_SYSTEM_PROMPT = (
    "You are a cybersecurity analyst specialising in Non-Human Identity (NHI) "
    "security. Summarise the following blog post in 3-5 concise paragraphs. "
    "Focus on key NHI-related findings, risks, and recommendations. "
    "Keep the tone professional and suitable for a Jira ticket description."
)


class BlogDigestService:
    """Stateless service that orchestrates the blog-digest pipeline."""

    @staticmethod
    async def scrape_latest_post() -> tuple[str, str]:
        """Scrape the blog index page and return ``(title, url)`` of the most recent post.

        Raises ``RuntimeError`` if no posts are found or the page cannot be fetched.
        """
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.get(_BLOG_INDEX_URL)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        link_tag = soup.select_one("a[href*='/blog/']")
        if link_tag is None:
            raise RuntimeError("Could not find any blog post links on the index page")

        href: str = link_tag.get("href", "")
        if href.startswith("/"):
            href = f"https://oasis.security{href}"

        title_tag = link_tag.find(["h1", "h2", "h3", "h4", "h5", "h6"])
        title = title_tag.get_text(strip=True) if title_tag else link_tag.get_text(strip=True)
        if not title:
            title = "Untitled Post"

        return title, href

    @staticmethod
    async def _fetch_post_content(url: str) -> str:
        """Fetch a blog post page and extract the main text content."""
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.get(url)
            resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        article = soup.find("article") or soup.find("main") or soup.find("body")
        if article is None:
            raise RuntimeError(f"Could not extract content from {url}")

        text = article.get_text(separator="\n", strip=True)
        max_chars = 12_000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n…[truncated]"

        return text

    @staticmethod
    async def generate_summary(post_content: str) -> str:
        """Call the local Ollama LLM (OpenAI-compatible API) to produce a summary."""
        client = AsyncOpenAI(
            base_url=settings.LLM_BASE_URL,
            api_key="ollama",
        )

        response = await client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": _SUMMARY_SYSTEM_PROMPT},
                {"role": "user", "content": post_content},
            ],
            temperature=0.3,
            max_tokens=1024,
        )

        return response.choices[0].message.content or ""

    @staticmethod
    async def _run_pipeline(db: AsyncSession, user_id: str) -> str:
        """Core pipeline: scrape → summarise → create Jira ticket.

        Returns the created ``jira_ticket_key``.
        Raises on failure — callers decide whether to swallow or propagate.
        """
        # Fail fast if the user has no Jira connection
        await JiraService._require_connection(user_id, db)

        title, post_url = await BlogDigestService.scrape_latest_post()
        logger.info("Scraped latest blog post: %s (%s)", title, post_url)

        post_content = await BlogDigestService._fetch_post_content(post_url)
        logger.info("Fetched post content (%d chars)", len(post_content))

        try:
            summary = await BlogDigestService.generate_summary(post_content)
        except Exception as exc:
            raise BlogDigestError(
                f"LLM unavailable — is Ollama running at {settings.LLM_BASE_URL}?"
            ) from exc
        logger.info("Generated LLM summary (%d chars)", len(summary))

        description = f"{summary}\n\nOriginal post: {post_url}"

        result = await db.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        target_user = result.scalar_one_or_none()
        if target_user is None:
            raise BlogDigestError(f"User {user_id} not found")

        payload = CreateTicketRequest(
            project_key=settings.BLOG_DIGEST_PROJECT_KEY,
            summary=f"[NHI Blog Digest] {title}",
            description=description,
            issue_type="Task",
        )

        ticket = await JiraService.create_ticket(
            user_id=str(target_user.id),
            payload=payload,
            source="blog_digest",
            db=db,
        )
        logger.info("Blog digest ticket created: %s", ticket.jira_ticket_key)
        return ticket.jira_ticket_key

    @staticmethod
    async def run_digest(db: AsyncSession, *, user_id: str | None = None) -> str | None:
        """Full pipeline: scrape → summarise → create Jira ticket.

        When *user_id* is provided (manual trigger from the UI), exceptions
        are **propagated** so the router can return proper HTTP error codes.
        When called from the scheduler (no *user_id*), errors are swallowed
        to avoid crashing the application.

        Returns the created ``jira_ticket_key`` on success.
        """
        if user_id is None:
            if not settings.BLOG_DIGEST_USER_EMAIL:
                logger.warning("BLOG_DIGEST_USER_EMAIL not configured — skipping digest")
                return None
            # Resolve the system user email to an ID
            result = await db.execute(
                select(User).where(User.email == settings.BLOG_DIGEST_USER_EMAIL)
            )
            system_user = result.scalar_one_or_none()
            if system_user is None:
                logger.error(
                    "System user '%s' not found — cannot create digest ticket",
                    settings.BLOG_DIGEST_USER_EMAIL,
                )
                return None
            resolved_user_id = str(system_user.id)
        else:
            resolved_user_id = user_id

        if user_id is not None:
            # Manual trigger — let exceptions propagate to the router
            return await BlogDigestService._run_pipeline(db, resolved_user_id)

        # Scheduler path — swallow all errors
        try:
            return await BlogDigestService._run_pipeline(db, resolved_user_id)
        except Exception:
            logger.exception("Blog digest run failed")
            return None
