# Tutorial

## Defining a model

Extend `AutoBase` to get schemas automatically on every model:

```python
from schemap import AutoBase
from sqlalchemy.orm import Mapped, mapped_column

class Product(AutoBase):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    price: Mapped[float] = mapped_column(nullable=True)
```

Use `SchemaMixin` if you already have a custom declarative base:

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

## State of .gitignore

Make sure `.gitignore` excludes `site/` (the zensical build output) alongside the usual Python entries:

```
site/
__pycache__/
*.pyc
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

- `exclude_always: list[str]` -- Excluded from all schemas.
- `exclude_create: list[str]` -- Excluded from CreateSchema only.
- `exclude_update: list[str]` -- Excluded from UpdateSchema only.
- `exclude_public: list[str]` -- Excluded from PublicSchema only.
- `field_overrides: dict[str, Any]` -- Override a field's Python type.
- `required_always: list[str]` -- Force fields to be required.
- `optional_always: list[str]` -- Force fields to be optional.
- `extra_validators: dict[str, Callable]` -- Custom validators per field.

### Custom validators

```python
def must_be_positive(v: float) -> float:
    if v <= 0:
        raise ValueError("Must be positive")
    return v

SchemaConfig(extra_validators={"price": must_be_positive})
```

Invalid values raise `pydantic.ValidationError`.
