# Tutorial

## Defining a model

Schemap supports three approaches. All three produce identical schemas. Pick the one that fits your project.

**AutoBase**: inherit from the ready-made declarative base. Best for new projects where you have no existing base:

```python
from schemap import AutoBase
from sqlalchemy.orm import Mapped, mapped_column

class Product(AutoBase):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    price: Mapped[float] = mapped_column(nullable=True)
```

**SchemaMixin**: mix into your own declarative base. Best when you already have a custom `DeclarativeBase` and want to keep it:

```python
from schemap import SchemaMixin
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(SchemaMixin, DeclarativeBase):
    pass

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
```

**@auto_schema**: decorate any model without changing its base class. Best when you cannot change the model's base (third-party models, large codebases):

```python
from schemap import auto_schema, SchemaConfig
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

@auto_schema
class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]

# With configuration
@auto_schema(config=SchemaConfig(exclude_public=["price"]))
class Product(Base):
    ...
```

## Schema variants

| Variant | What it excludes |
|---|---|
| `.Schema` | Nothing |
| `.CreateSchema` | Primary keys, server_defaults, client defaults |
| `.UpdateSchema` | Primary keys (all fields become Optional with None) |
| `.PublicSchema` | Columns starting with `__` |

## Converting between ORM and schemas

```python
# ORM instance to schema
user = User(id=1, name="Alice")
schema = user.to_schema()
schema = user.to_schema(User.PublicSchema)  # Specific variant

# Schema to ORM instance
data = User.CreateSchema(name="Bob")
user = User.from_schema(data)
```

## Customizing schemas

Attach `SchemaConfig` to any model with `__schema_config__`:

```python
from sqlalchemy.orm import Mapped, mapped_column
from schemap import AutoBase, SchemaConfig

class User(AutoBase):
    __tablename__ = "users"
    __schema_config__ = SchemaConfig(
        exclude_public=["email", "phone"],
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]
    phone: Mapped[str]
```

### SchemaConfig options

- `exclude_always: list[str]`: excluded from all schemas.
- `exclude_create: list[str]`: excluded from CreateSchema only.
- `exclude_update: list[str]`: excluded from UpdateSchema only.
- `exclude_public: list[str]`: excluded from PublicSchema only.
- `field_overrides: dict[str, Any]`: override a field's Python type.
- `required_always: list[str]`: force fields to be required.
- `optional_always: list[str]`: force fields to be optional.
- `extra_validators: dict[str, Callable]`: custom validators per field.
- `public_exclude_prefix: tuple[str, ...]`: prefixes excluded from PublicSchema (default: `("__",)`).

Raises `ValueError` if a field appears in both `required_always` and `optional_always`, or if config references unknown column names.

### Custom validators

```python
def must_be_positive(v: float) -> float:
    if v <= 0:
        raise ValueError("Must be positive")
    return v

SchemaConfig(extra_validators={"price": must_be_positive})
```

Invalid values raise `pydantic.ValidationError`.
