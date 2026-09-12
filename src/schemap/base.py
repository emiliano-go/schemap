"""Base classes for automatic schemap generation."""

from __future__ import annotations

from typing import Any, Self, TypeVar

from cached_classproperty import cached_classproperty
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase

from .builder import build_schema
from .utils.schema import from_schema as _from_schema_shared

T = TypeVar("T", bound=BaseModel)


class SchemaMixin:
    """Mixin that adds auto-generated Pydantic schemas as class attributes.

    Provides four schema variants as cached class properties, plus
    ``from_schema()`` and ``to_schema()`` for conversion.

    Used by ``AutoBase`` and the ``@auto_schema`` decorator::

        class User(AutoBase):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]
    """

    @cached_classproperty
    def Schema(cls) -> type[BaseModel]:
        """Full schema with all columns.

        Includes every mapped column with its original type and nullability::

            User.Schema.model_fields
            # {'id': FieldInfo(annotation=int, required=True),
            #  'name': FieldInfo(annotation=str, required=True)}
        """
        config = getattr(cls, "__schema_config__", None)
        return build_schema(cls, schema_type="full", config=config)

    @cached_classproperty
    def CreateSchema(cls) -> type[BaseModel]:
        """Schema for creating new instances.

        Excludes primary keys, server defaults, and columns with client-side
        defaults::

            User.CreateSchema.model_fields
            # {'name': FieldInfo(annotation=str, required=True)}
        """
        config = getattr(cls, "__schema_config__", None)
        return build_schema(cls, schema_type="create", config=config)

    @cached_classproperty
    def UpdateSchema(cls) -> type[BaseModel]:
        """Schema for partial updates (all fields optional).

        Every field is ``Optional[T]`` with a default of ``None``::

            User.UpdateSchema.model_fields
            # {'name': FieldInfo(annotation=Optional[str], required=False)}
        """
        config = getattr(cls, "__schema_config__", None)
        return build_schema(cls, schema_type="update", config=config)

    @cached_classproperty
    def PublicSchema(cls) -> type[BaseModel]:
        """Public-facing schema (excludes sensitive fields).

        Excludes columns matching ``public_exclude_prefix`` (default: ``"__"``)::

            User.PublicSchema.model_fields
            # {'id': ..., 'name': ...}  # __internal__ excluded
        """
        config = getattr(cls, "__schema_config__", None)
        return build_schema(cls, schema_type="public", config=config)

    @classmethod
    def from_schema(cls, schema_obj: BaseModel | dict[str, Any]) -> Self:
        """Create an ORM instance from a Pydantic schema or dict.

        Accepts a Pydantic model instance or a plain dict. Unset fields
        are dropped (not passed to the constructor). Unknown keys in dicts
        are silently ignored (only mapped columns are used)::

            # From a schema
            data = User.CreateSchema(name="alice")
            user = User.from_schema(data)

            # From a dict
            user = User.from_schema({"name": "bob"})
        """
        return _from_schema_shared(cls, schema_obj)

    def to_schema(self, schema_cls: type[BaseModel] | None = None) -> BaseModel:
        """Convert this ORM instance to a Pydantic schema.

        Defaults to ``self.Schema`` (the full schema)::

            user = User(id=1, name="alice")
            schema = user.to_schema()
            schema.model_dump()  # {'id': 1, 'name': 'alice'}

            # Use a specific schema variant:
            schema = user.to_schema(User.PublicSchema)
        """
        if schema_cls is None:
            schema_cls = self.Schema
        return schema_cls.model_validate(self)


class AutoBase(SchemaMixin, DeclarativeBase):
    """Base class for all models. Inherit from this to get auto-schemas.

    Example::

        from schemap import AutoBase
        from sqlalchemy.orm import Mapped, mapped_column

        class User(AutoBase):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]

        # Schemas are available immediately:
        User.Schema.model_fields
        User.CreateSchema.model_fields

        # Conversion:
        user = User.from_schema({"name": "alice"})
        schema = user.to_schema()
    """

    pass
