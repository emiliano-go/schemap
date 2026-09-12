# API Reference

## Public imports

```python
from schemap import (
    auto_schema,
    AutoBase,
    SchemaMixin,
    SchemaConfig,
    SchemaType,
    Status,
    ArchivableMixin,
    CreatedByMixin,
    IntPrimaryKeyMixin,
    SoftDeleteMixin,
    StatusMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
    UpdatedByMixin,
    VersionMixin,
    build_schema,
    extract_python_type,
    extract_column_metadata,
    ColumnLike,
)
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

- `from_schema(cls, schema_obj)`: create ORM instance from Pydantic schema or dict. Uses `model_dump(exclude_unset=True)`. Unknown dict keys are silently ignored.
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

## SchemaConfig

Dataclass for per-model schema customization. All fields are optional.

```python
from schemap import SchemaConfig

config = SchemaConfig(
    exclude_always=["internal_id"],
    exclude_create=["notes"],
    exclude_update=["created_at"],
    exclude_public=["email", "phone"],
    field_overrides={"score": Decimal},
    required_always=["email"],
    optional_always=["bio"],
    extra_validators={"price": my_validator},
    public_exclude_prefix=("_secret",),
)
```

- `exclude_always: list[str] = []` — excluded from all schemas.
- `exclude_create: list[str] = []` — excluded from CreateSchema only.
- `exclude_update: list[str] = []` — excluded from UpdateSchema only.
- `exclude_public: list[str] = []` — excluded from PublicSchema only.
- `field_overrides: dict[str, Any] = {}` — override a field's Python type.
- `required_always: list[str] = []` — force fields to be required.
- `optional_always: list[str] = []` — force fields to be optional.
- `extra_validators: dict[str, Callable] = {}` — custom validators per field.
- `public_exclude_prefix: tuple[str, ...] = ("__",)` — prefixes excluded from PublicSchema.

Raises `ValueError` if a field appears in both `required_always` and `optional_always`, or if config references unknown column names.

## SchemaType

```python
SchemaType = Literal["full", "create", "update", "public"]
```

Type alias for the four schema variants:

- `"full"`: all columns with original types and nullability.
- `"create"`: excludes PKs, server defaults, client defaults.
- `"update"`: all fields `Optional[T]` with `None` default.
- `"public"`: excludes columns matching `public_exclude_prefix`.

## Status

```python
class Status(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
```

Enum for use with `StatusMixin`. Inherits from `str` so it compares directly with string values.

## build_schema

```python
def build_schema(
    model: type[DeclarativeBase],
    schema_type: SchemaType = "full",
    config: SchemaConfig | None = None,
) -> type[BaseModel]
```

Build a Pydantic schema class for any SQLAlchemy model without using `AutoBase`.

```python
from schemap import build_schema, SchemaConfig

UserSchema = build_schema(User, "full")
UserCreateSchema = build_schema(User, "create", config=SchemaConfig(exclude_create=["internal_id"]))
```

Raises `TypeError` if model is not a SQLAlchemy mapped class. Raises `ValueError` if config references unknown column names.

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
| `JSON` | `Any` |
| `UUID` | `uuid.UUID` |
| `Enum` | Concrete enum class (e.g. `Color`) |
| `ARRAY` | `list` |
