"""Tests for mixins."""

import uuid
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, select, String
from sqlalchemy.orm import Session, Mapped, mapped_column

from schemap.base import AutoBase
from schemap.mixins import (
    TimestampMixin,
    SoftDeleteMixin,
    VersionMixin,
    Status,
    StatusMixin,
    ArchivableMixin,
    UUIDPrimaryKeyMixin,
    IntPrimaryKeyMixin,
)


# --- Test models ---
class User(AutoBase, TimestampMixin):
    __tablename__ = "mixin_users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


class Post(AutoBase, SoftDeleteMixin):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()


class Product(AutoBase, VersionMixin):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


class Subscription(AutoBase, StatusMixin):
    __tablename__ = "subscriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    plan: Mapped[str]


class Order(AutoBase, ArchivableMixin):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    total: Mapped[float]


class Tenant(AutoBase, UUIDPrimaryKeyMixin):
    __tablename__ = "tenants"
    name: Mapped[str]


class Tag(AutoBase, IntPrimaryKeyMixin):
    __tablename__ = "tags"
    name: Mapped[str]


# --- Fixtures ---
@pytest.fixture
def session():
    """Provide a SQLite in-memory database session."""
    engine = create_engine("sqlite:///:memory:")
    AutoBase.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


# --- TimestampMixin tests ---
def test_timestamp_mixin_has_fields():
    """Test that TimestampMixin adds expected columns."""
    assert hasattr(User, "created_at")
    assert hasattr(User, "updated_at")


def test_timestamp_mixin_defaults(session):
    """Test that timestamps are auto-populated on flush."""
    user = User(name="test")
    assert user.created_at is None  # Not set until flush
    assert user.updated_at is None

    session.add(user)
    session.flush()  # Triggers default evaluation

    assert user.created_at is not None
    assert user.updated_at is not None
    assert isinstance(user.created_at, datetime)
    assert isinstance(user.updated_at, datetime)


def test_timestamp_mixin_updates(session):
    """Test that updated_at changes when the row is updated."""
    user = User(name="original")
    session.add(user)
    session.flush()
    original_updated = user.updated_at

    # Update the user
    user.name = "changed"
    session.flush()
    new_updated = user.updated_at

    assert new_updated is not None
    # Some DBs have millisecond precision; allow small difference
    assert new_updated > original_updated


# --- SoftDeleteMixin tests ---
def test_soft_delete_mixin_has_fields():
    """Test that SoftDeleteMixin adds deleted_at."""
    assert hasattr(Post, "deleted_at")


def test_soft_delete_method(session):
    """Test soft_delete() sets deleted_at."""
    post = Post(title="test")
    session.add(post)
    session.flush()

    assert post.deleted_at is None

    post.soft_delete()
    assert post.deleted_at is not None
    assert isinstance(post.deleted_at, datetime)


def test_soft_delete_active_filter(session):
    """Test that active() filter excludes soft-deleted rows."""
    post1 = Post(title="active")
    post2 = Post(title="deleted")
    session.add_all([post1, post2])
    session.flush()

    post2.soft_delete()
    session.flush()

    # Query using active filter
    active_posts = session.execute(select(Post).where(Post.active())).scalars().all()
    active_titles = [p.title for p in active_posts]

    assert "active" in active_titles
    assert "deleted" not in active_titles


# --- VersionMixin tests ---
def test_version_mixin_has_field():
    """Test that VersionMixin adds version column."""
    assert hasattr(Product, "version")


def test_version_mixin_default(session):
    """Test that version defaults to 1."""
    product = Product(name="widget")
    session.add(product)
    session.flush()
    assert product.version == 1


def test_version_mixin_increment(session):
    """Test that increment_version bumps the version."""
    product = Product(name="widget")
    session.add(product)
    session.flush()

    product.increment_version()
    session.flush()
    assert product.version == 2

    product.increment_version()
    session.flush()
    assert product.version == 3


# --- StatusMixin tests ---
def test_status_mixin_has_field():
    """Test that StatusMixin adds status column."""
    assert hasattr(Subscription, "status")


def test_status_mixin_default(session):
    """Test that status defaults to active."""
    sub = Subscription(plan="pro")
    session.add(sub)
    session.flush()
    assert sub.status == Status.ACTIVE


def test_status_mixin_activate_deactivate(session):
    """Test activate() and deactivate() toggle status."""
    sub = Subscription(plan="pro")
    session.add(sub)
    session.flush()

    sub.deactivate()
    session.flush()
    assert sub.status == Status.INACTIVE

    sub.activate()
    session.flush()
    assert sub.status == Status.ACTIVE


# --- ArchivableMixin tests ---
def test_archivable_mixin_has_field():
    """Test that ArchivableMixin adds archived_at column."""
    assert hasattr(Order, "archived_at")


def test_archivable_mixin_archive_restore(session):
    """Test archive() and restore() toggle archived_at."""
    order = Order(total=99.99)
    session.add(order)
    session.flush()

    assert order.archived_at is None

    order.archive()
    session.flush()
    assert order.archived_at is not None
    assert isinstance(order.archived_at, datetime)

    order.restore()
    session.flush()
    assert order.archived_at is None


# --- UUIDPrimaryKeyMixin tests ---
def test_uuid_pk_mixin_has_field():
    """Test that UUIDPrimaryKeyMixin adds id column."""
    assert hasattr(Tenant, "id")


def test_uuid_pk_mixin_generates_uuid(session):
    """Test that UUID PK is auto-generated."""
    tenant = Tenant(name="acme")
    session.add(tenant)
    session.flush()
    assert isinstance(tenant.id, uuid.UUID)


# --- IntPrimaryKeyMixin tests ---
def test_int_pk_mixin_has_field():
    """Test that IntPrimaryKeyMixin adds id column."""
    assert hasattr(Tag, "id")


def test_int_pk_mixin_is_int(session):
    """Test that int PK works as expected."""
    tag = Tag(name="python")
    session.add(tag)
    session.flush()
    assert isinstance(tag.id, int)
    assert tag.id >= 1