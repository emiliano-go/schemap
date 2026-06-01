# schemap

Automatic Pydantic v2 schemas from SQLAlchemy 2.0 ORM models. Define your model once. Four schemas come for free.

## Install

```bash
pip install schemap
```

## Quick start

```python
from schemap import AutoBase
from sqlalchemy.orm import Mapped, mapped_column

class User(AutoBase):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]

User.Schema         # Full schema, all columns
User.CreateSchema   # Excludes PKs, defaults (for inserts)
User.UpdateSchema   # All fields optional (for partial updates)
User.PublicSchema   # Excludes sensitive fields
```

## What you get

- One model definition, four schemas generated automatically.
- SchemaConfig for field exclusion, type overrides, and custom validators.
- Timestamp, soft delete, audit, and versioning mixins included.
