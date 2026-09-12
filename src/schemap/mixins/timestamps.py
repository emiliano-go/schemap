"""Timestamp mixin for created_at/updated_at fields."""

from datetime import datetime, timezone

from sqlalchemy.orm import Mapped, mapped_column


class TimestampMixin:
    """Adds ``created_at`` and ``updated_at`` timestamp columns.

    ``created_at`` is set to the current UTC time on creation.
    ``updated_at`` is set on creation and updated automatically on each save.

    Example::

        class Article(AutoBase, TimestampMixin):
            __tablename__ = "articles"
            id: Mapped[int] = mapped_column(primary_key=True)
            title: Mapped[str]

        article = Article(title="Hello")
        article.created_at   # datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
        article.updated_at   # datetime(2025, 1, 1, 12, 0, tzinfo=UTC)
    """

    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
