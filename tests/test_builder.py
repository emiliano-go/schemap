"""Tests for dynamic schema builder."""

import pytest
from datetime import datetime, timezone
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Optional, Union
from schemap.builder import build_schema


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(nullable=False, unique=True)
    email: Mapped[str] = mapped_column(nullable=False)
    age: Mapped[int] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.now(timezone.utc))


def test_build_full_schema():
    """Test building complete schema with all fields."""
    UserSchema = build_schema(User, "full")
    
    # Check schema has all expected fields
    assert "id" in UserSchema.model_fields
    assert "username" in UserSchema.model_fields
    assert "email" in UserSchema.model_fields
    assert "age" in UserSchema.model_fields
    assert "created_at" in UserSchema.model_fields
    
    # Check types
    assert UserSchema.model_fields["username"].annotation == str
    assert UserSchema.model_fields["age"].annotation == Optional[int]
    
    # Check from_attributes is enabled
    assert UserSchema.model_config["from_attributes"] is True


def test_build_create_schema():
    """Test create schema excludes auto-generated fields."""
    UserCreateSchema = build_schema(User, "create")
    
    # id and created_at should be excluded (primary key and server_default)
    assert "id" not in UserCreateSchema.model_fields
    assert "created_at" not in UserCreateSchema.model_fields
    
    # Required fields should be required
    assert UserCreateSchema.model_fields["username"].is_required() is True
    assert UserCreateSchema.model_fields["email"].is_required() is True


def test_build_update_schema():
    """Test update schema makes all fields optional."""
    UserUpdateSchema = build_schema(User, "update")
    
    # All fields should be Optional with default None
    for field_name, field in UserUpdateSchema.model_fields.items():
        # Check type is Optional (handles both Optional[X] and X | None)
        is_optional = getattr(field.annotation, "__origin__", None) is Union and type(None) in getattr(field.annotation, "__args__", [])
        assert is_optional or field.is_required() is False


def test_can_create_instance():
    """Test the generated schema can actually create instances."""
    UserSchema = build_schema(User, "full")
    
    user = UserSchema(
        id=1,
        username="testuser",
        email="test@example.com",
        age=30,
        created_at=datetime.now(timezone.utc)
    )
    
    assert user.username == "testuser"
    assert user.model_dump()["username"] == "testuser"


def test_non_mapped_class_raises_type_error():
    """Test that build_schema with a non-mapped class raises TypeError."""
    with pytest.raises(TypeError, match="SQLAlchemy mapped class"):
        build_schema(str, "full")

    with pytest.raises(TypeError, match="SQLAlchemy mapped class"):
        build_schema(int, "create")