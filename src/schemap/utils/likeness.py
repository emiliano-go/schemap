"""Protocol for objects that behave like SQLAlchemy columns."""

from typing import Protocol, Optional, Any
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.sql.schema import (
    ColumnDefault,
    DefaultClause,
)


class ColumnLike(Protocol):
    """Protocol for objects that behave like a SQLAlchemy ``Column``.

    Used internally for type-hinting column-like objects::

        def my_func(col: ColumnLike) -> None:
            print(col.name, col.type)

    Any object with ``name``, ``type``, ``nullable``, ``default``,
    ``server_default``, and ``primary_key`` attributes satisfies this
    protocol.
    """

    # --- Identity ---
    name: str

    # --- Type ---
    type: TypeEngine[Any]

    # --- Nullability / defaults ---
    nullable: bool
    default: Optional[ColumnDefault]
    server_default: Optional[DefaultClause]

    # --- Keys ---
    primary_key: bool
