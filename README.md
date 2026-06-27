<p align="center">
  <h1 align="center">schemap</h1>
</p>

<p align="center">
  <strong>Automatic Pydantic v2 schemas from SQLAlchemy 2.0 ORM models. Define your model once. The schemas come automatically.</strong>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white&style=for-the-badge" alt="Python">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/License-MIT-10AC84?style=for-the-badge" alt="License">
  </a>
  <a href="https://deepwiki.com/emiliano-go/schemap/">
    <img src="https://img.shields.io/badge/DeepWiki-8A2BE2?logo=readthedocs&logoColor=white&style=for-the-badge" alt="DeepWiki">
  </a>
</p>

```bash
pip install schemap
```

## Why Schemap

Writing Pydantic schemas for SQLAlchemy models is repetitive work. You maintain four schemas per model: full, create, update, and public. Each schema must stay synchronized with column changes, nullability updates, and new constraints. Schemap eliminates this duplication by generating all four schemas directly from your model definition.

The library reads your SQLAlchemy columns and translates them into Pydantic fields. A primary key becomes excluded from CreateSchema. A server default becomes excluded from write operations. A nullable column becomes an Optional field. You focus on your model. Schemap handles the validation layer.

## Quick Start

Schemap gives you three ways to attach schemas to your models. All three produce identical schemas.

**AutoBase** — inherit from the ready-made declarative base:
```python
from schemap import AutoBase
from sqlalchemy.orm import Mapped, mapped_column

class User(AutoBase):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]
```

**@auto_schema** — decorate any existing model without changing its base class:
```python
from schemap import auto_schema
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

@auto_schema
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]
```

Both approaches give you the same four schemas and conversion methods:

```python
User.Schema         # all columns
User.CreateSchema   # excludes primary keys and server defaults
User.UpdateSchema   # all fields optional for partial updates
User.PublicSchema   # excludes fields starting with __

# Convert between ORM and Pydantic
data = User.CreateSchema(name="Alice", email="alice@example.com")
user = User.from_schema(data)
schema = user.to_schema()
```

The decorator also accepts a config argument:

```python
@auto_schema(config=SchemaConfig(exclude_public=["email"]))
class User(Base):
    ...
```

## SchemaConfig

Customize generated schemas per model using the `__schema_config__` attribute.

```python
from schemap import AutoBase, SchemaConfig
from sqlalchemy.orm import Mapped, mapped_column

class User(AutoBase):
    __tablename__ = "users"
    __schema_config__ = SchemaConfig(
        exclude_public=["email"],
        exclude_create=["internal_id"],
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]
    internal_id: Mapped[int]
```

The SchemaConfig class supports several exclusion options. `exclude_always` removes a field from all schemas. `exclude_create`, `exclude_update`, and `exclude_public` target specific schema variants. `field_overrides` lets you change a field's Python type. `required_always` and `optional_always` override nullability rules.

## Built-in Mixins

Schemap includes two reusable mixins for common model patterns.

**TimestampMixin** adds `created_at` and `updated_at` columns. The timestamps set automatically on insert and update.

**SoftDeleteMixin** adds a `deleted_at` column, a `soft_delete()` method, and an `active()` classmethod filter for excluding deleted records.

```python
from schemap import AutoBase, TimestampMixin, SoftDeleteMixin

class User(AutoBase, TimestampMixin):
    __tablename__ = "users"
    name: Mapped[str]

class Post(AutoBase, SoftDeleteMixin):
    __tablename__ = "posts"
    title: Mapped[str]
```

## Custom Validators

Attach validation functions to any field using `extra_validators` in SchemaConfig. The validator receives the field value and must return it or raise ValueError.

```python
from schemap import AutoBase, SchemaConfig

def validate_positive(value: int) -> int:
    if value <= 0:
        raise ValueError("Value must be positive")
    return value

class Product(AutoBase):
    __tablename__ = "products"
    __schema_config__ = SchemaConfig(extra_validators={"price": validate_positive})
    
    price: Mapped[float]
```

## Standalone Usage

Use `build_schema` directly when you need a schema without modifying the model class.

```python
from schemap import build_schema
from schemap.config import SchemaConfig

UserSchema = build_schema(User, schema_type="create", config=SchemaConfig(exclude_create=["internal_id"]))
```

## Decorator API

Use `@auto_schema` to attach schemas to any SQLAlchemy model without inheritance.

```python
from schemap import auto_schema, SchemaConfig

# Bare decorator — all defaults
@auto_schema
class User(Base):
    __tablename__ = "users"
    ...

# With config
@auto_schema(config=SchemaConfig(exclude_public=["email"]))
class User(Base):
    ...
```

The decorator runs after the class body and attaches `.Schema`, `.CreateSchema`, `.UpdateSchema`, `.PublicSchema`, `.from_schema()`, and `.to_schema()` directly to your class. Your model's inheritance chain stays unchanged.

## Requirements

Python 3.12 or later, SQLAlchemy 2.0.49 or later, Pydantic 2.13.4 or later.

## License

MIT