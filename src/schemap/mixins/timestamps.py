"""Timestamp mixin for created_at/updated_at fields."""

from datetime import datetime, timezone
from sqlalchemy.orm import Mapped, mapped_column

class TimestampMixin:
    """Adds created_at and updated_at timestamp columns."""
    
    created_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )