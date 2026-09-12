"""Status and archivable mixins for state management."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class Status(str, Enum):
    """Status values for ``StatusMixin``.

    Members:
        ACTIVE: ``"active"``
        INACTIVE: ``"inactive"``
    """

    ACTIVE = "active"
    """``"active"`` status value."""

    INACTIVE = "inactive"
    """``"inactive"`` status value."""


class StatusMixin:
    """Adds a ``status`` column with ``activate()`` and ``deactivate()`` methods.

    The column defaults to ``Status.ACTIVE`` and stores a string value.

    Example::

        class Ticket(AutoBase, StatusMixin):
            __tablename__ = "tickets"
            id: Mapped[int] = mapped_column(primary_key=True)
            title: Mapped[str]

        ticket = Ticket(title="Bug fix")
        ticket.status  # 'active'
        ticket.deactivate()
        ticket.status  # 'inactive'
        ticket.activate()
        ticket.status  # 'active'
    """

    status: Mapped[str] = mapped_column(String(50), default=Status.ACTIVE)

    def activate(self) -> None:
        """Set status to ``Status.ACTIVE``."""
        self.status = Status.ACTIVE

    def deactivate(self) -> None:
        """Set status to ``Status.INACTIVE``."""
        self.status = Status.INACTIVE


class ArchivableMixin:
    """Adds an ``archived_at`` timestamp column with ``archive()`` and ``restore()``.

    ``archived_at`` is ``None`` when the record is active, and set to
    the current UTC time when archived.

    Example::

        class Article(AutoBase, ArchivableMixin):
            __tablename__ = "articles"
            id: Mapped[int] = mapped_column(primary_key=True)
            title: Mapped[str]

        article = Article(title="Draft")
        article.archived_at  # None
        article.archive()
        article.archived_at  # datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
        article.restore()
        article.archived_at  # None
    """

    archived_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def archive(self) -> None:
        """Set ``archived_at`` to the current UTC time."""
        self.archived_at = datetime.now(timezone.utc)

    def restore(self) -> None:
        """Clear ``archived_at`` (set to ``None``)."""
        self.archived_at = None
