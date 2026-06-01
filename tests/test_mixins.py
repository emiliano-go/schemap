"""Tests for mixins."""

import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, Mapped, mapped_column

from schemap.base import AutoBase
from schemap.mixins import TimestampMixin, SoftDeleteMixin


# --- Test models ---
class User(AutoBase, TimestampMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()


class Post(AutoBase, SoftDeleteMixin):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column()


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