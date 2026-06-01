# API Reference

## Public imports

```python
from schemap import (
    AutoBase,
    SchemaMixin,
    SchemaConfig,
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
from schemap import build_schema
```

## AutoBase

Ready-to-use declarative base with auto-generated schemas.

```python
class AutoBase(SchemaMixin, DeclarativeBase)
```

## SchemaMixin

Mixin that adds four schema class properties and two conversion methods.

**Class properties:**

- `Schema` -- Full schema with all columns.
- `CreateSchema` -- Excludes PKs, server_defaults, defaults.
- `UpdateSchema` -- All fields Optional with None default.
- `PublicSchema` -- Excludes `__`-prefixed columns.

Schemas are cached per class via `cached_classproperty`.

**Methods:**

- `from_schema(cls, schema_obj)` -- Create ORM instance from Pydantic schema. Uses `model_dump(exclude_none=True)`.
- `to_schema(self, schema_cls=None)` -- Convert ORM instance to schema. Defaults to `.Schema`.

**Configuration:**

Set `__schema_config__ = SchemaConfig(...)` on any model class to customize its schemas.

## SchemaConfig

Dataclass for per-model schema customization. All fields are optional.

- `exclude_always: list[str] = []`
- `exclude_create: list[str] = []`
- `exclude_update: list[str] = []`
- `exclude_public: list[str] = []`
- `field_overrides: dict[str, Any] = {}`
- `required_always: list[str] = []`
- `optional_always: list[str] = []`
- `extra_validators: dict[str, Callable] = {}`

## build_schema

```python
def build_schema(
    model: type[DeclarativeBase],
    schema_type: str = "default",
    config: SchemaConfig | None = None,
) -> type[BaseModel]
```

Build a Pydantic schema class for any SQLAlchemy model without using `AutoBase`.

**schema_type values:** `"default"`, `"create"`, `"update"`, `"public"`.

```python
from schemap import build_schema, SchemaConfig

UserSchema = build_schema(User, "default")
UserCreateSchema = build_schema(User, "create", config=SchemaConfig(exclude_create=["internal_id"]))
```

## Type mapping

| SQLAlchemy type | Python type |
|---|---|
| `Integer`, `SmallInteger`, `BigInteger` | `int` |
| `Float`, `REAL` | `float` |
| `Numeric`, `DECIMAL` | `Decimal` |
| `String`, `Text`, `Unicode`, `CHAR`, `VARCHAR` | `str` |
| `Boolean` | `bool` |
| `DateTime`, `TIMESTAMP` | `datetime` |
| `Date` | `date` |
| `Time` | `time` |
| `LargeBinary`, `BLOB` | `bytes` |
| `JSON` | `dict` |
| `UUID` | `uuid.UUID` |
| `ARRAY` | `list` |
