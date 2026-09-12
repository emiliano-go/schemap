"""Tests for SchemaConfig."""

import pytest
import pydantic
from typing import Optional
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


# ===================================================================
# Extra validators: edge cases
# ===================================================================

def test_validator_skips_none_on_optional_field():
    """Validator should not be called when value is None for optional fields."""
    call_count = 0

    def track_calls(v):
        nonlocal call_count
        call_count += 1
        if v <= 0:
            raise ValueError("Must be positive")
        return v

    class Item(AutoBase):
        __tablename__ = "test_validator_none"
        __schema_config__ = SchemaConfig(
            extra_validators={"price": track_calls}
        )
        id: Mapped[int] = mapped_column(primary_key=True)
        price: Mapped[Optional[float]] = mapped_column(nullable=True)

    # None should skip the validator entirely
    s = Item.UpdateSchema(price=None)
    assert s.price is None
    assert call_count == 0

    # Non-None should call the validator
    s = Item.UpdateSchema(price=10.0)
    assert s.price == 10.0
    assert call_count == 1


def test_validator_on_update_schema_all_optional():
    """Validator should run on non-None values in UpdateSchema."""
    def must_be_positive(v):
        if v <= 0:
            raise ValueError("Must be positive")
        return v

    class Item(AutoBase):
        __tablename__ = "test_validator_update"
        __schema_config__ = SchemaConfig(
            extra_validators={"price": must_be_positive}
        )
        id: Mapped[int] = mapped_column(primary_key=True)
        price: Mapped[float]

    # Valid value
    s = Item.UpdateSchema(price=10.0)
    assert s.price == 10.0

    # None passes through (optional)
    s = Item.UpdateSchema(price=None)
    assert s.price is None

    # Invalid value raises
    with pytest.raises(pydantic.ValidationError):
        Item.UpdateSchema(price=-5.0)


def test_validators_on_multiple_fields():
    """Multiple validators on different fields should all work."""
    def validate_price(v):
        if v <= 0:
            raise ValueError("Price must be positive")
        return v

    def validate_name(v):
        if len(v) < 3:
            raise ValueError("Name too short")
        return v

    class Item(AutoBase):
        __tablename__ = "test_multi_validators"
        __schema_config__ = SchemaConfig(
            extra_validators={
                "price": validate_price,
                "name": validate_name,
            }
        )
        id: Mapped[int] = mapped_column(primary_key=True)
        price: Mapped[float]
        name: Mapped[str]

    # Both valid
    s = Item.CreateSchema(price=10.0, name="hello")
    assert s.price == 10.0
    assert s.name == "hello"

    # Both invalid
    with pytest.raises(pydantic.ValidationError) as exc_info:
        Item.CreateSchema(price=-1.0, name="ab")
    assert exc_info.value.error_count() == 2

    # Only price invalid
    with pytest.raises(pydantic.ValidationError) as exc_info:
        Item.CreateSchema(price=-1.0, name="hello")
    assert exc_info.value.error_count() == 1

    # Only name invalid
    with pytest.raises(pydantic.ValidationError) as exc_info:
        Item.CreateSchema(price=10.0, name="ab")
    assert exc_info.value.error_count() == 1


def test_validator_on_public_schema():
    """Validator should also run on PublicSchema."""
    def must_be_positive(v):
        if v <= 0:
            raise ValueError("Must be positive")
        return v

    class Item(AutoBase):
        __tablename__ = "test_validator_public"
        __schema_config__ = SchemaConfig(
            extra_validators={"price": must_be_positive}
        )
        id: Mapped[int] = mapped_column(primary_key=True)
        price: Mapped[float]

    # Valid
    s = Item.PublicSchema(id=1, price=10.0)
    assert s.price == 10.0

    # Invalid
    with pytest.raises(pydantic.ValidationError):
        Item.PublicSchema(id=1, price=-5.0)


def test_validator_returning_wrong_type():
    """Validator returning wrong type should not crash (Pydantic accepts it)."""
    def bad_return(v):
        return "not a float"

    class Item(AutoBase):
        __tablename__ = "test_bad_return"
        __schema_config__ = SchemaConfig(
            extra_validators={"price": bad_return}
        )
        id: Mapped[int] = mapped_column(primary_key=True)
        price: Mapped[float]

    # Pydantic doesn't re-validate after field_validator in 'after' mode
    s = Item.CreateSchema(price=10.0)
    assert s.price == "not a float"


def test_validator_on_field_with_default():
    """Validator on a field excluded from CreateSchema should not crash."""
    def must_be_positive(v):
        if v <= 0:
            raise ValueError("Must be positive")
        return v

    class Item(AutoBase):
        __tablename__ = "test_validator_default"
        __schema_config__ = SchemaConfig(
            extra_validators={"price": must_be_positive}
        )
        id: Mapped[int] = mapped_column(primary_key=True)
        price: Mapped[float] = mapped_column(default=10.0)

    # price has a default, so it's excluded from CreateSchema
    # validator for price should be skipped (field not in schema)
    s = Item.CreateSchema()
    assert "price" not in Item.CreateSchema.model_fields

    # price IS in UpdateSchema, validator should work there
    s = Item.UpdateSchema(price=20.0)
    assert s.price == 20.0

    with pytest.raises(pydantic.ValidationError):
        Item.UpdateSchema(price=-5.0)


def test_config_unknown_field_raises():
    """Config referencing unknown column should raise ValueError on schema access."""
    from schemap.builder import build_schema
    from sqlalchemy.orm import DeclarativeBase

    class Base(DeclarativeBase):
        pass

    class BadModel(Base):
        __tablename__ = "test_bad_config"
        id: Mapped[int] = mapped_column(primary_key=True)

    with pytest.raises(ValueError, match="unknown columns"):
        build_schema(
            BadModel,
            "full",
            SchemaConfig(extra_validators={"nonexistent_field": lambda v: v}),
        )


def test_required_and_optional_conflict():
    """Config with field in both required_always and optional_always should raise."""
    with pytest.raises(ValueError, match="both required_always and optional_always"):
        SchemaConfig(
            required_always=["email"],
            optional_always=["email"],
        )