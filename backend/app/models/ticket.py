import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    jira_connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("jira_connections.id"),
        nullable=False,
    )
    jira_ticket_key: Mapped[str] = mapped_column(String(50), nullable=False)
    jira_ticket_url: Mapped[str] = mapped_column(String(500), nullable=False)
    project_key: Mapped[str] = mapped_column(String(20), nullable=False)
    summary: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    issue_type: Mapped[str] = mapped_column(
        String(50), nullable=False, server_default=text("'Task'")
    )
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # -- Relationships --
    user = relationship("User", back_populates="tickets")
    jira_connection = relationship("JiraConnection", back_populates="tickets")

    # -- Composite index: powers "recent 10 tickets by project" query --
    __table_args__ = (
        Index(
            "ix_tickets_project_key_created",
            "project_key",
            created_at.desc(),
        ),
    )
