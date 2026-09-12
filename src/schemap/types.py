"""Type extraction utilities for SQLAlchemy columns."""

from .utils.mapping import TYPE_MAP
from .utils.likeness import ColumnLike

from sqlalchemy import types as sa_types
from typing import Any


def extract_python_type(column: ColumnLike) -> tuple[type, bool]:
    """Extract Python type and optional flag from a SQLAlchemy column.

    Example::

        from sqlalchemy import Column, Integer, String

        extract_python_type(Column("age", Integer))
        # (int, False)

        extract_python_type(Column("name", String(100)))
        # (str, False)

    Args:
        column: A SQLAlchemy ``Column`` or ``InstrumentedAttribute``.

    Returns:
        ``(python_type, is_optional)`` tuple.
    """
    if isinstance(column, sa_types.TypeEngine):
        sql_type = type(column)
    else:
        sql_type = type(column.type)

    # Enum columns: use the concrete Python enum class, not abstract enum.Enum
    if sql_type is sa_types.Enum:
        enum_class = getattr(column.type, "enum_class", None)
        if enum_class is not None:
            return enum_class, False

    return TYPE_MAP.get(sql_type, (Any, False)), False


def extract_column_metadata(column: ColumnLike) -> dict[str, Any]:
    """Extract all metadata from a column for Pydantic ``Field`` construction.

    Example::

        from sqlalchemy import Column, Integer, String

        col = Column("name", String(100), nullable=False)
        meta = extract_column_metadata(col)
        # {'name': 'name', 'python_type': str, 'is_optional': False,
        #  'primary_key': False, 'max_length': 100, ...}

    Args:
        column: SQLAlchemy ``Column`` object.

    Returns:
        Dict with keys: ``name``, ``python_type``, ``is_optional``,
        ``primary_key``, ``max_length``, ``precision``, ``scale``,
        ``default``, ``default_factory``, ``server_default``.
    """
    default_value = None
    default_factory = None
    if column.default is not None:
        arg = column.default.arg
        if callable(arg):
            # SQLAlchemy wraps callable defaults to receive a context argument,
            # but Pydantic's default_factory calls with no arguments.
            # Wrap to ignore any arguments.
            default_factory = lambda _a=arg, *_a2, **_kw: _a(None)
        else:
            default_value = arg

    return {
        "name": column.name,
        "python_type": extract_python_type(column)[0],
        "is_optional": column.nullable,
        "primary_key": column.primary_key,
        "max_length": getattr(column.type, "length", None) if not isinstance(column.type, sa_types.Enum) else None,
        "precision": getattr(column.type, "precision", None),
        "scale": getattr(column.type, "scale", None),
        "default": default_value,
        "default_factory": default_factory,
        "server_default": column.server_default,
    }
