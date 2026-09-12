"""Tests for AutoBase and SchemaMixin."""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, DeclarativeBase

from schemap.base import AutoBase, SchemaMixin
from sqlalchemy.orm import Mapped, mapped_column


class User(AutoBase):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)


# --- SchemaMixin standalone (not via AutoBase) ---

class CustomBase(SchemaMixin, DeclarativeBase):
    pass


class Product(CustomBase):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    price: Mapped[float]


def test_auto_schemas_exist():
    """Test that schemas are auto-generated as class attributes."""
    assert hasattr(User, "Schema")
    assert hasattr(User, "CreateSchema")
    assert hasattr(User, "UpdateSchema")
    assert hasattr(User, "PublicSchema")


def test_from_schema_creates_instance():
    """Test creating ORM instance from Pydantic schema."""
    data = User.CreateSchema(username="alice", email="alice@example.com")
    user = User.from_schema(data)

    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.id is None  # Not set because excluded from CreateSchema


def test_to_schema_converts_instance():
    """Test converting ORM instance to Pydantic schema."""
    user = User(id=1, username="bob", email="bob@example.com")
    schema = user.to_schema()

    assert schema.username == "bob"
    assert schema.email == "bob@example.com"
    assert schema.id == 1


def test_round_trip():
    """Test ORM -> Schema -> ORM round trip."""
    original = User(id=5, username="charlie", email="charlie@example.com")
    schema = original.to_schema()
    rehydrated = User.from_schema(schema)

    assert rehydrated.username == original.username
    assert rehydrated.email == original.email
    assert rehydrated.id == original.id


# --- SchemaMixin standalone tests ---

def test_schema_mixin_has_all_schemas():
    """Test that SchemaMixin on a custom base generates all four schemas."""
    assert hasattr(Product, "Schema")
    assert hasattr(Product, "CreateSchema")
    assert hasattr(Product, "UpdateSchema")
    assert hasattr(Product, "PublicSchema")


def test_schema_mixin_fields():
    """Test that SchemaMixin-generated schemas have correct fields."""
    assert "id" in Product.Schema.model_fields
    assert "name" in Product.Schema.model_fields
    assert "price" in Product.Schema.model_fields


def test_schema_mixin_create_excludes_pk():
    """Test that CreateSchema from SchemaMixin excludes PKs."""
    assert "id" not in Product.CreateSchema.model_fields
    assert "name" in Product.CreateSchema.model_fields
    assert "price" in Product.CreateSchema.model_fields


def test_schema_mixin_to_schema():
    """Test to_schema works with SchemaMixin standalone."""
    product = Product(id=1, name="widget", price=9.99)
    schema = product.to_schema()
    assert schema.name == "widget"
    assert schema.price == 9.99


def test_schema_mixin_from_schema():
    """Test from_schema works with SchemaMixin standalone."""
    data = Product.CreateSchema(name="gadget", price=19.99)
    product = Product.from_schema(data)
    assert product.name == "gadget"
    assert product.price == 19.99
    assert product.id is None