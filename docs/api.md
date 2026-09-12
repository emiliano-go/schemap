# API Reference

## Public imports

```python
from schemap import (
    auto_schema,
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

- `Schema`: full schema with all columns.
- `CreateSchema`: excludes PKs, server_defaults, defaults.
- `UpdateSchema`: all fields Optional with None default.
- `PublicSchema`: excludes `__`-prefixed columns.

Schemas are cached per class via `cached_classproperty`.

**Methods:**

- `from_schema(cls, schema_obj)`: create ORM instance from Pydantic schema. Uses `model_dump(exclude_unset=True)`.
- `to_schema(self, schema_cls=None)`: convert ORM instance to schema. Defaults to `.Schema`.

**Configuration:**

Set `__schema_config__ = SchemaConfig(...)` on any model class to customize its schemas.

## auto_schema

Decorator that attaches generated schemas to any SQLAlchemy model without changing its base class.

```python
def auto_schema(
    cls: type[T] | None = None,
    *,
    config: SchemaConfig | None = None,
) -> type[T]
```

**Usage:**

```python
from schemap import auto_schema, SchemaConfig

# Bare decorator, all defaults
@auto_schema
class User(Base):
    __tablename__ = "users"
    ...

# With config
@auto_schema(config=SchemaConfig(exclude_public=["email"]))
class User(Base):
    ...
```

Attaches `.Schema`, `.CreateSchema`, `.UpdateSchema`, `.PublicSchema`, `.from_schema()`, and `.to_schema()` to the decorated class. Works with any `DeclarativeBase` subclass. All three approaches (`AutoBase`, `SchemaMixin`, `@auto_schema`) produce identical schemas.

**Schema types:** `"full"` (all columns), `"create"` (excludes PKs and defaults), `"update"` (all optional), `"public"` (excludes `__`-prefixed columns).

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
- `public_exclude_prefix: tuple[str, ...] = ("__",)`

## build_schema

```python
def build_schema(
    model: type[DeclarativeBase],
    schema_type: Literal["full", "create", "update", "public"] = "full",
    config: SchemaConfig | None = None,
) -> type[BaseModel]
```

Build a Pydantic schema class for any SQLAlchemy model without using `AutoBase`.

**schema_type values:** `"full"`, `"create"`, `"update"`, `"public"`.

```python
from schemap import build_schema, SchemaConfig

UserSchema = build_schema(User, "full")
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
| `Enum` | `enum.Enum` |
| `ARRAY` | `list` |
