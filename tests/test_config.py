"""Tests for SchemaConfig."""

import pytest
import pydantic
from schemap.base import AutoBase
from schemap.config import SchemaConfig
from sqlalchemy.orm import Mapped, mapped_column

class User(AutoBase):
    __tablename__ = "config_users"
    __schema_config__ = SchemaConfig(
        exclude_public=["email"],
        exclude_create=["internal_id"],
    )
    
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column()
    email: Mapped[str] = mapped_column()
    internal_id: Mapped[int] = mapped_column()

def test_exclude_from_public():
    """Test that email is excluded from PublicSchema."""
    assert "email" not in User.PublicSchema.model_fields
    assert "name" in User.PublicSchema.model_fields

def test_exclude_from_create():
    """Test that internal_id is excluded from CreateSchema."""
    assert "internal_id" not in User.CreateSchema.model_fields
    assert "name" in User.CreateSchema.model_fields

def test_default_schema_untouched():
    """Test that default Schema still has all fields."""
    assert "email" in User.Schema.model_fields
    assert "internal_id" in User.Schema.model_fields

def test_extra_validators():
    """Test that custom validators are applied."""
    def must_be_positive(v: float) -> float:
        if v <= 0:
            raise ValueError("Must be positive")
        return v
    
    class Product(AutoBase):
        __tablename__ = "config_products"
        __schema_config__ = SchemaConfig(
            extra_validators={"price": must_be_positive}
        )
        id: Mapped[int] = mapped_column(primary_key=True)
        price: Mapped[float]
    
    # Valid price should work
    p = Product.CreateSchema(price=10.5)
    assert p.price == 10.5
    
    # Invalid price should raise Pydantic ValidationError
    with pytest.raises(pydantic.ValidationError) as exc_info:
        Product.CreateSchema(price=-5.0)
    
    # Verify the error message contains our custom message
    assert "Must be positive" in str(exc_info.value)


def test_public_exclude_prefix():
    """Test that public_exclude_prefix controls which fields are excluded."""

    class TaggedUser(AutoBase):
        __tablename__ = "tagged_users"
        __schema_config__ = SchemaConfig(
            public_exclude_prefix=("_secret",),
        )
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]
        _secret_token: Mapped[str] = mapped_column()
        visible_field: Mapped[str] = mapped_column()

    # _secret_token excluded because it starts with "_secret"
    assert "_secret_token" not in TaggedUser.PublicSchema.model_fields
    # visible_field NOT excluded (doesn't match any prefix)
    assert "visible_field" in TaggedUser.PublicSchema.model_fields
    assert "name" in TaggedUser.PublicSchema.model_fields