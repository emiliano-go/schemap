""" Automatic Pydantic schemas for SQLAlchemy models """

__version__ = "0.3.0"

from schemap.base import AutoBase, SchemaMixin
from schemap.builder import build_schema
from schemap.types import extract_python_type, extract_column_metadata
from schemap.utils.likeness import ColumnLike
from schemap.config import SchemaConfig
from schemap.mixins import TimestampMixin, SoftDeleteMixin

__all__ = [
    "AutoBase",
    "SchemaMixin",
    "build_schema",
    "extract_python_type",
    "extract_column_metadata",
    "ColumnLike",
    "SchemaConfig",
    "TimestampMixin",
    "SoftDeleteMixin",
]