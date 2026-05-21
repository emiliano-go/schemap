from .utils.mapping import TYPE_MAP
from .utils.likeness import ColumnLike

from sqlalchemy import types as sa_types, inspect
from sqlalchemy.sql.schema import Column
from sqlalchemy.orm.attributes import InstrumentedAttribute
from typing import Union, Any


def extract_python_type(column : ColumnLike) -> tuple[type, bool]:
    """
    Extract Python type and optional flag from a SQLAlchemy column.
    
    Args:
        column: A SQLAlchemy Column or InstrumentedAttribute
        
    Returns:
        tuple[type, bool]: (python_type, is_optional)
        
    Example:
        >>> from sqlalchemy import Integer, String
        >>> from sqlalchemy.orm import Mapped, mapped_column
        >>> 
        >>> # Simulating Mapped[int]
        >>> extract_python_type(Integer()) 
        (int, False)
    """
    # If passed a TypeEngine directly (like Integer()), use it as-is
    if isinstance(column, sa_types.TypeEngine):
        sql_type = type(column)
        return TYPE_MAP.get(sql_type, (Any, False)), False
    
    sql_type = type(column.type)
    return TYPE_MAP.get(sql_type, (Any, False)), False
    
def extract_column_metadata(column : ColumnLike) -> dict[str, Any]:
    """
    Extract all metadata from column for Pydantic Field construction.
    
    Returns dict with keys:
        - "python_type": the Python type from extract_python_type
        - "is_optional": boolean
        - "max_length": int | None (from String, Text)
        - "ge": int | None (minimum value for numeric)
        - "le": int | None (maximum value for numeric)
        - "default": Any | None (from column.default)
        - "primary_key": bool
        
    Args:
        column: SQLAlchemy Column object
        
    Returns:
        dict with above keys
    """

    return{
        "name": column.name,
        "python_type": extract_python_type(column)[0],
        "is_optional": column.nullable,
        "primary_key": column.primary_key,
        "max_length": getattr(column.type, 'length', None),
        "default": column.default.arg if column.default else None,
        "server_default" : column.server_default,
    }