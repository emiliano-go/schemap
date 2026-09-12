""" Automatic Pydantic schemas for SQLAlchemy models """

__version__ = "0.5.2"

from schemap.base import AutoBase, SchemaMixin
from schemap.builder import build_schema, SchemaType
from schemap.decorator import auto_schema
from schemap.types import extract_python_type, extract_column_metadata
from schemap.utils.likeness import ColumnLike
from schemap.config import SchemaConfig
from schemap.mixins import (
    ArchivableMixin,
    CreatedByMixin,
    IntPrimaryKeyMixin,
    SoftDeleteMixin,
    Status,
    StatusMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    UpdatedByMixin,
    VersionMixin,
)

__all__ = [
    "ArchivableMixin",
    "auto_schema",
    "AutoBase",
    "build_schema",
    "ColumnLike",
    "CreatedByMixin",
    "extract_column_metadata",
    "extract_python_type",
    "IntPrimaryKeyMixin",
    "SchemaConfig",
    "SchemaMixin",
    "SchemaType",
    "SoftDeleteMixin",
    "Status",
    "StatusMixin",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "UpdatedByMixin",
    "VersionMixin",
]
