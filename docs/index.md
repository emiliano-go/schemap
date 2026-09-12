# schemap

Automatic Pydantic v2 schemas from SQLAlchemy 2.0 ORM models. Define your model once. Four schemas come for free.

## Install

```bash
pip install schemap
```

## Quick start

Schemap gives you three approaches (`AutoBase`, `SchemaMixin`, or `@auto_schema`). They all produce identical schemas.

**AutoBase**: inherit from the ready-made base:

```python
from schemap import AutoBase
from sqlalchemy.orm import Mapped, mapped_column

class User(AutoBase):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]
```

**@auto_schema**: decorate any existing model:

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

Both give you the same four schemas:

```python
User.Schema         # Full schema, all columns
User.CreateSchema   # Excludes PKs, defaults (for inserts)
User.UpdateSchema   # All fields optional (for partial updates)
User.PublicSchema   # Excludes sensitive fields
```

## What you get

- One model definition, four schemas generated automatically.
- Three approaches: `AutoBase`, `SchemaMixin`, or `@auto_schema` decorator.
- `SchemaConfig` for field exclusion, type overrides, and custom validators.
- `SchemaType` enum for type-safe schema variant selection.
- `Status` enum for status fields with `StatusMixin`.
- Timestamp, soft delete, audit, status, archivable, and versioning mixins included.
- PEP 561 `py.typed` marker for full IDE and type checker support.
