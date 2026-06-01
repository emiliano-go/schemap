# Mixins

Schemap ships with nine reusable mixins for common patterns.

## TimestampMixin

Adds `created_at` and `updated_at` with auto-populating defaults.

```python
from schemap import TimestampMixin, AutoBase

class Post(AutoBase, TimestampMixin):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
```

Both columns use `default=lambda: datetime.now(timezone.utc)`. `updated_at` also uses `onupdate` to refresh on every write. Both are excluded from `CreateSchema` (they have client defaults).

## SoftDeleteMixin

Adds `deleted_at` timestamp, `soft_delete()`, and `active()` filter.

```python
from schemap import SoftDeleteMixin, AutoBase

class Article(AutoBase, SoftDeleteMixin):
    __tablename__ = "articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]

article.soft_delete()
# article.deleted_at is now set

# Query for undeleted records
from sqlalchemy import select
results = session.execute(
    select(Article).where(Article.active())
).scalars().all()
```

## CreatedByMixin and UpdatedByMixin

Audit trail mixins with foreign keys and relationships to `users`.

```python
from schemap import CreatedByMixin, UpdatedByMixin, AutoBase

class Document(AutoBase, CreatedByMixin, UpdatedByMixin):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str]
```

`CreatedByMixin` adds `created_by_id` (FK) and `created_by` (relationship). `UpdatedByMixin` adds `updated_by_id` and `updated_by`. Use separately or together.

## StatusMixin

Adds `status` column with `activate()` and `deactivate()` methods.

```python
from schemap import StatusMixin, AutoBase

class Subscription(AutoBase, StatusMixin):
    __tablename__ = "subscriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    plan: Mapped[str]

sub.activate()   # status = "active"
sub.deactivate() # status = "inactive"
```

Default status is `"active"`.

## ArchivableMixin

Adds `archived_at` timestamp with `archive()` and `restore()` methods.

```python
from schemap import ArchivableMixin, AutoBase

class Order(AutoBase, ArchivableMixin):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    total: Mapped[float]

order.archive()   # archived_at is set
order.restore()   # archived_at is None
```

## VersionMixin

Adds `version: int` column for optimistic locking.

```python
from schemap import VersionMixin, AutoBase

class Product(AutoBase, VersionMixin):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    price: Mapped[float]

product.increment_version()
```

## UUIDPrimaryKeyMixin and IntPrimaryKeyMixin

Standard primary key columns.

```python
from schemap import UUIDPrimaryKeyMixin, IntPrimaryKeyMixin, AutoBase

class Tenant(AutoBase, UUIDPrimaryKeyMixin):
    __tablename__ = "tenants"
    name: Mapped[str]

class Tag(AutoBase, IntPrimaryKeyMixin):
    __tablename__ = "tags"
    name: Mapped[str]
```

`UUIDPrimaryKeyMixin` uses `default=uuid4`. `IntPrimaryKeyMixin` provides a bare `int` PK.

## Writing your own mixin

A mixin is a plain class with `Mapped` columns. No base class needed.

```python
from sqlalchemy.orm import Mapped, mapped_column

class AuditMixin:
    created_by: Mapped[str] = mapped_column(nullable=False)
    updated_by: Mapped[str] = mapped_column(nullable=True)

class Document(AutoBase, AuditMixin):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(primary_key=True)
    content: Mapped[str]
```

Guidelines:
- Column names must not collide between mixins or with the model.
- Do not define `__tablename__` in a mixin.
- Use `Optional` or `| None` for nullable columns.
- Add methods for domain logic (activate, archive, soft_delete, etc.).
