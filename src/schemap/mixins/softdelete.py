"""Soft delete mixin for marking rows as deleted without removing them."""

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Mapped, mapped_column


class SoftDeleteMixin:
    """Adds soft delete capability with a ``deleted_at`` timestamp.

    Call ``soft_delete()`` to mark a record as deleted. Use
    ``active()`` as a query filter to exclude deleted records.

    Example::

        class Post(AutoBase, SoftDeleteMixin):
            __tablename__ = "posts"
            id: Mapped[int] = mapped_column(primary_key=True)
            title: Mapped[str]

        post = Post(title="Draft")
        post.deleted_at  # None
        post.soft_delete()
        post.deleted_at  # datetime(2025, 1, 1, 12, 0, tzinfo=UTC)

        # Query active records:
        session.execute(select(Post).filter(Post.active()))
    """

    deleted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True)

    def soft_delete(self) -> None:
        """Mark this instance as deleted by setting ``deleted_at`` to now (UTC)."""
        self.deleted_at = datetime.now(timezone.utc)

    @classmethod
    def active(cls):
        """Return a query filter for undeleted records.

        Use in ``select().filter()`` to exclude soft-deleted rows::

            session.execute(select(Post).filter(Post.active()))
        """
        return cls.deleted_at.is_(None)
