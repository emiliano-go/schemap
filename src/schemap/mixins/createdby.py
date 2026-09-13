"""Audit mixins for tracking which user created or updated a record."""

from typing import Optional

from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship
from sqlalchemy.schema import ForeignKey


class CreatedByMixin:
    """Adds ``created_by_id`` FK column.

    By default, the FK points to the ``users`` table. Override
    ``user_table`` on subclasses to use a different table.

    Example::

        class Article(AutoBase, CreatedByMixin):
            __tablename__ = "articles"
            id: Mapped[int] = mapped_column(primary_key=True)
            title: Mapped[str]

        # With a different user table:
        class Article(AutoBase, CreatedByMixin):
            __tablename__ = "articles"
            user_table = "authors"
            ...

    Note:
        This mixin only provides the FK column. To add a ``created_by``
        relationship, define it on your model::

            created_by: Mapped[Optional[User]] = relationship()
    """

    user_table: str = "users"

    @declared_attr
    def created_by_id(cls) -> Mapped[Optional[int]]:
        return mapped_column(ForeignKey(f"{cls.user_table}.id"))


class UpdatedByMixin:
    """Adds ``updated_by_id`` FK column.

    By default, the FK points to the ``users`` table. Override
    ``user_table`` on subclasses to use a different table.

    Example::

        class Article(AutoBase, UpdatedByMixin):
            __tablename__ = "articles"
            id: Mapped[int] = mapped_column(primary_key=True)
            title: Mapped[str]

        # With a different user table:
        class Article(AutoBase, UpdatedByMixin):
            __tablename__ = "articles"
            user_table = "authors"
            ...

    Note:
        This mixin only provides the FK column. To add an ``updated_by``
        relationship, define it on your model::

            updated_by: Mapped[Optional[User]] = relationship()
    """

    user_table: str = "users"

    @declared_attr
    def updated_by_id(cls) -> Mapped[Optional[int]]:
        return mapped_column(ForeignKey(f"{cls.user_table}.id"))
