""" Automatic Pydantic schemas for SQLAlchemy models """

__version__ = "0.5.2"

from schemap.base import AutoBase, SchemaMixin
from schemap.builder import build_schema
from schemap.decorator import auto_schema
from schemap.types import extract_python_type, extract_column_metadata
from schemap.utils.likeness import ColumnLike
from schemap.config import SchemaConfig
from schemap.mixins import (
    ArchivableMixin,
    CreatedByMixin,
    IntPrimaryKeyMixin,
    SoftDeleteMixin,
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
    "CreatedByMixin",
    "IntPrimaryKeyMixin",
    "SchemaConfig",
    "SchemaMixin",
    "SoftDeleteMixin",
    "StatusMixin",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    "UpdatedByMixin",
    "VersionMixin",
]
