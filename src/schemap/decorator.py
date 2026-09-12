"""Decorator for attaching auto-generated schemas to SQLAlchemy models."""

from __future__ import annotations

from typing import Any, Callable, TypeVar, overload

from pydantic import BaseModel

from .builder import build_schema
from .config import SchemaConfig
from .utils.schema import from_schema as _from_schema_shared

T = TypeVar("T")


def _to_schema(self: Any, schema_cls: type[BaseModel] | None = None) -> BaseModel:
    if schema_cls is None:
        schema_cls = self.Schema
    return schema_cls.model_validate(self)


def _apply_auto_schema(cls: type, config: SchemaConfig | None) -> type:
    cfg = config or SchemaConfig()
    cls.Schema = build_schema(cls, "full", cfg)
    cls.CreateSchema = build_schema(cls, "create", cfg)
    cls.UpdateSchema = build_schema(cls, "update", cfg)
    cls.PublicSchema = build_schema(cls, "public", cfg)
    cls.from_schema = classmethod(_from_schema_shared)
    cls.to_schema = _to_schema
    return cls


@overload
def auto_schema(cls: type[T]) -> type[T]: ...


@overload
def auto_schema(
    cls: None = None,
    *,
    config: SchemaConfig | None = None,
) -> Callable[[type[T]], type[T]]: ...


def auto_schema(cls: type[T] | None = None, *, config: SchemaConfig | None = None) -> type[T] | Callable[[type[T]], type[T]]:
    """Decorator that attaches auto-generated Pydantic schemas to a SQLAlchemy model.

    Attaches ``Schema``, ``CreateSchema``, ``UpdateSchema``, ``PublicSchema``,
    ``from_schema()``, and ``to_schema()`` to the decorated class.

    Can be used bare, with parentheses, or with a ``SchemaConfig``::

        from schemap import auto_schema, SchemaConfig

        # Bare decorator
        @auto_schema
        class User(Base):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]

        # With parentheses
        @auto_schema()
        class User(Base):
            ...

        # With config
        @auto_schema(config=SchemaConfig(exclude_public=["email"]))
        class User(Base):
            ...

    After decoration, use the attached schemas::

        User.Schema.model_fields          # all fields
        User.CreateSchema.model_fields    # no PK, no server defaults
        User.UpdateSchema.model_fields    # all optional
        User.PublicSchema.model_fields    # excludes sensitive fields

        user = User.from_schema({"name": "alice"})
        schema = user.to_schema()
    """
    if cls is not None:
        return _apply_auto_schema(cls, config=config)

    def decorator(klass: type[T]) -> type[T]:
        return _apply_auto_schema(klass, config=config)

    return decorator
