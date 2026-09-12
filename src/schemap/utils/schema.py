from typing import Any, Optional

from pydantic import BaseModel, Field
from sqlalchemy import inspect

from ..config import SchemaConfig

_mapped_keys_cache: dict[type, set[str]] = {}


def from_schema(cls: type, schema_obj: BaseModel | dict[str, Any]) -> Any:
    """Create an ORM instance from a Pydantic schema or dict."""
    if isinstance(schema_obj, dict):
        mapped = _mapped_keys_cache.get(cls)
        if mapped is None:
            mapped = {c.key for c in inspect(cls).columns}
            _mapped_keys_cache[cls] = mapped
        data = {k: v for k, v in schema_obj.items() if k in mapped and v is not ...}
        return cls(**data)
    return cls(**schema_obj.model_dump(exclude_unset=True))


def should_include(schema_type: str, metadata: dict[str, Any], config: SchemaConfig | None = None) -> bool:
    """Determine if a column should be included in the schema."""

    if config is not None:
        if metadata["name"] in config.exclude_always:
            return False
        if schema_type == "public" and metadata["name"] in config.exclude_public:
            return False
        if schema_type == "create" and metadata["name"] in config.exclude_create:
            return False
        if schema_type == "update" and metadata["name"] in config.exclude_update:
            return False

    if schema_type == "full":
        return True

    elif schema_type == "create":
        if metadata["primary_key"]:
            return False
        # Exclude server_default columns, but only if they apply to INSERT
        server_default = metadata.get("server_default")
        if server_default is not None:
            if not getattr(server_default, "for_update", False):
                return False
        # Exclude columns with client-side defaults
        if metadata.get("default") is not None or metadata.get("default_factory") is not None:
            return False
        return True

    elif schema_type == "update":
        if metadata["primary_key"]:
            return False
        return True

    elif schema_type == "public":
        prefix = config.public_exclude_prefix if config else ("__",)
        if any(metadata["name"].startswith(p) for p in prefix):
            return False
        return True

    else:
        raise ValueError(f"Unknown schema_type: {schema_type}")


def transform_for_schema(metadata: dict, schema_type: str, config: SchemaConfig | None) -> tuple[type, Any]:
    """Transform column metadata into (field_type, Field(...)) for create_model."""

    field_name = metadata["name"]

    config_defaults = _get_config_defaults(config, field_name)

    type_info = _resolve_type_and_nullability(metadata, config_defaults)

    field_def = _apply_schema_rules(type_info, schema_type)

    return field_def


def _get_config_defaults(config: SchemaConfig | None, field_name: str) -> dict:
    """Extract config defaults or provide empty fallbacks."""
    if config is None:
        return {
            "override_type": None,
            "is_required_forced": False,
            "is_optional_forced": False,
        }

    return {
        "override_type": config.field_overrides.get(field_name),
        "is_required_forced": field_name in config.required_always,
        "is_optional_forced": field_name in config.optional_always,
    }


def _resolve_type_and_nullability(metadata: dict, config_defaults: dict) -> dict:
    """Determine final Python type and whether field is optional."""
    base_type = config_defaults["override_type"] or metadata["python_type"]

    if config_defaults["is_required_forced"]:
        is_optional = False
        has_default = False
        default_value = None
        default_factory = None
    elif config_defaults["is_optional_forced"]:
        is_optional = True
        has_default = True
        default_value = None
        default_factory = None
    else:
        is_optional = metadata["is_optional"]
        has_default = metadata.get("default") is not None or metadata.get("default_factory") is not None
        default_value = metadata.get("default")
        default_factory = metadata.get("default_factory")

    return {
        "base_type": base_type,
        "is_optional": is_optional,
        "has_default": has_default,
        "default_value": default_value,
        "default_factory": default_factory,
        "max_length": metadata.get("max_length"),
    }


def _apply_schema_rules(type_info: dict, schema_type: str) -> tuple[type, Any]:
    """Apply schema-specific rules (update/create/full)."""
    base_type = type_info["base_type"]
    is_optional = type_info["is_optional"]
    has_default = type_info["has_default"]
    default_value = type_info["default_value"]
    default_factory = type_info.get("default_factory")

    field_kwargs: dict[str, Any] = {}
    if type_info["max_length"] is not None:
        field_kwargs["max_length"] = type_info["max_length"]

    # Update schema: all fields Optional with None default
    if schema_type == "update":
        field_kwargs["default"] = None
        return (Optional[base_type], Field(**field_kwargs) if field_kwargs else ...)

    # Create and Full/Public schemas: same logic (create already filtered server_defaults)
    if has_default:
        if default_factory is not None:
            field_kwargs["default_factory"] = default_factory
        else:
            field_kwargs["default"] = default_value
        return (base_type, Field(**field_kwargs) if field_kwargs else ...)
    elif is_optional:
        field_kwargs["default"] = None
        return (Optional[base_type], Field(**field_kwargs) if field_kwargs else ...)
    else:
        return (base_type, Field(**field_kwargs) if field_kwargs else ...)
