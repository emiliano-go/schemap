"""Schema builder — constructs Pydantic models from SQLAlchemy columns."""

from typing import Any, Literal

from sqlalchemy.exc import NoInspectionAvailable
from sqlalchemy.orm import DeclarativeBase, configure_mappers
from sqlalchemy import inspect
from pydantic import BaseModel, create_model, ConfigDict, field_validator

from .config import SchemaConfig
from .types import extract_column_metadata
from .utils.schema import should_include, transform_for_schema, _get_mapped_keys

_mappers_configured = False

SchemaType = Literal["full", "create", "update", "public"]
"""Schema variant to build.

- ``"full"``: All columns with original types and nullability.
- ``"create"``: Excludes PKs, server defaults, client defaults.
- ``"update"``: All fields ``Optional[T]`` with ``None`` default.
- ``"public"``: Excludes columns matching ``public_exclude_prefix``.
"""


def build_schema(
    model: type[DeclarativeBase],
    schema_type: SchemaType = "full",
    config: SchemaConfig | None = None,
) -> type[BaseModel]:
    """Build a Pydantic schema class for a SQLAlchemy model.

    Only mapped columns are included. Relationships, hybrid properties,
    and column properties are not supported.

    Example::

        from schemap import build_schema
        from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

        class Base(DeclarativeBase):
            pass

        class User(Base):
            __tablename__ = "users"
            id: Mapped[int] = mapped_column(primary_key=True)
            name: Mapped[str]

        UserSchema = build_schema(User, "full")
        UserSchema.model_fields  # {'id': ..., 'name': ...}

        UserCreate = build_schema(User, "create")
        UserCreate.model_fields  # {'name': ...}  (no id)

    Args:
        model: The SQLAlchemy model class (e.g., ``User``).
        schema_type: Which schema variant to build.
        config: Optional ``SchemaConfig`` for customization.

    Returns:
        A Pydantic model class.

    Raises:
        TypeError: If model is not a SQLAlchemy mapped class.
        ValueError: If schema_type is not a valid variant.
        ValueError: If config references unrecognized column names.
    """
    global _mappers_configured

    try:
        inspector = inspect(model)
    except NoInspectionAvailable:
        if not _mappers_configured:
            configure_mappers()
            _get_mapped_keys.cache_clear()
            _mappers_configured = True
        try:
            inspector = inspect(model)
        except NoInspectionAvailable:
            raise TypeError(
                f"build_schema requires a SQLAlchemy mapped class, got {model.__name__!r}"
            ) from None

    columns_meta = []
    actual_names: set[str] = set()

    # Detect polymorphic discriminator column
    polymorphic_on_key = None
    mapper = inspector.mapper
    if mapper.polymorphic_on is not None:
        polymorphic_on_key = mapper.polymorphic_on.key

    for col in inspector.columns:
        meta = extract_column_metadata(col)
        actual_names.add(meta["name"])
        if polymorphic_on_key and meta["name"] == polymorphic_on_key:
            if config is not None and config.polymorphic_exclude:
                meta["polymorphic_on"] = True
        if should_include(schema_type, meta, config):
            columns_meta.append(meta)

    if config is not None:
        _validate_config(config, actual_names, model.__name__)

    fields: dict[str, Any] = {}

    for col_meta in columns_meta:
        field_type, field_kwargs = transform_for_schema(col_meta, schema_type, config)
        fields[col_meta["name"]] = (field_type, field_kwargs)

    # Sanitize class name: strip "<locals>" segments from __qualname__
    # to produce valid schema names like "ClassNameFullSchema"
    class_name = model.__qualname__
    if "<locals>" in class_name:
        class_name = model.__name__

    schema_name = f"{class_name}{schema_type.capitalize()}Schema"

    validators = {}
    if config and config.extra_validators:
        for field_name, validator_func in config.extra_validators.items():
            if field_name in fields:
                validators[f"validate_{field_name}"] = field_validator(
                    field_name
                )(_wrap_validator(validator_func))

    schema_class = create_model(
        schema_name,
        __config__=ConfigDict(from_attributes=True, populate_by_name=True),
        __validators__=validators or None,
        **fields,
    )
    return schema_class


def _validate_config(config: SchemaConfig, actual_columns: set[str], model_name: str) -> None:
    """Raise ValueError if config references columns that don't exist."""
    all_names = set()
    all_names.update(config.exclude_always)
    all_names.update(config.exclude_create)
    all_names.update(config.exclude_update)
    all_names.update(config.exclude_public)
    all_names.update(config.field_overrides)
    all_names.update(config.required_always)
    all_names.update(config.optional_always)
    all_names.update(config.extra_validators)

    unknown = all_names - actual_columns
    if unknown:
        raise ValueError(
            f"SchemaConfig for {model_name!r} references unknown columns: {unknown}"
        )


def _wrap_validator(validator):
    """Wrap a user validator to pass through None values.

    Pydantic calls validators on all values including None for optional
    fields. Most validators don't handle None, causing TypeError. This
    wrapper skips the validator when the value is None.
    """
    def wrapper(v):
        if v is None:
            return v
        return validator(v)
    return wrapper
