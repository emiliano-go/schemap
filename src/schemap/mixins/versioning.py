"""Version mixin for optimistic locking."""

from sqlalchemy.orm import Mapped, mapped_column


class VersionMixin:
    """Adds a ``version`` column for optimistic locking.

    The column defaults to ``1`` and is incremented by calling
    ``increment_version()``.

    Example::

        class Document(AutoBase, VersionMixin):
            __tablename__ = "documents"
            id: Mapped[int] = mapped_column(primary_key=True)
            title: Mapped[str]

        doc = Document(title="RFC")
        doc.version  # 1
        doc.increment_version()
        doc.version  # 2
    """

    version: Mapped[int] = mapped_column(default=1)

    def increment_version(self) -> None:
        """Increment the ``version`` field by 1."""
        self.version += 1
