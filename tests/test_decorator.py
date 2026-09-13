"""Tests for @auto_schema decorator — all edge cases."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional, Any

import pytest
from pydantic import ValidationError
from sqlalchemy import String, Text, JSON, Float, DateTime, Date, Boolean, Numeric, UUID as SA_UUID, Enum as SAEnum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from schemap import auto_schema, SchemaConfig
from schemap.base import AutoBase


# ---------------------------------------------------------------------------
# Shared base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ===================================================================
# 1. BASIC FUNCTIONALITY (regression — original tests preserved)
# ===================================================================

@auto_schema
class User(Base):
    __tablename__ = "decorator_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(nullable=False)


def test_schemas_exist():
    assert hasattr(User, "Schema")
    assert hasattr(User, "CreateSchema")
    assert hasattr(User, "UpdateSchema")
    assert hasattr(User, "PublicSchema")


def test_from_schema_creates_instance():
    data = User.CreateSchema(username="alice", email="alice@example.com")
    user = User.from_schema(data)
    assert user.username == "alice"
    assert user.email == "alice@example.com"
    assert user.id is None


def test_to_schema_converts_instance():
    user = User(id=1, username="bob", email="bob@example.com")
    schema = user.to_schema()
    assert schema.username == "bob"
    assert schema.email == "bob@example.com"
    assert schema.id == 1


def test_round_trip():
    original = User(id=5, username="charlie", email="charlie@example.com")
    schema = original.to_schema()
    rehydrated = User.from_schema(schema)
    assert rehydrated.username == original.username
    assert rehydrated.email == original.email
    assert rehydrated.id == original.id


# ===================================================================
# 2. DECORATOR WITH CONFIG
# ===================================================================

@auto_schema(config=SchemaConfig(exclude_public=["email"]))
class UserWithConfig(Base):
    __tablename__ = "decorator_config_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str]


def test_config_excludes_from_public():
    assert "email" not in UserWithConfig.PublicSchema.model_fields
    assert "name" in UserWithConfig.PublicSchema.model_fields


def test_config_default_schema_untouched():
    assert "email" in UserWithConfig.Schema.model_fields
    assert "name" in UserWithConfig.Schema.model_fields


def test_to_schema_with_explicit_class():
    user = UserWithConfig(id=1, name="alice", email="alice@example.com")
    schema = user.to_schema(UserWithConfig.PublicSchema)
    assert schema.name == "alice"
    assert not hasattr(schema, "email")


# ===================================================================
# 3. BARE DECORATOR (no parens)
# ===================================================================

@auto_schema
class MinimalUser(Base):
    __tablename__ = "decorator_minimal"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


def test_bare_decorator_works():
    assert hasattr(MinimalUser, "Schema")
    assert hasattr(MinimalUser, "CreateSchema")
    assert hasattr(MinimalUser, "UpdateSchema")
    assert hasattr(MinimalUser, "PublicSchema")
    assert hasattr(MinimalUser, "from_schema")
    assert hasattr(MinimalUser, "to_schema")


def test_create_schema_excludes_pk():
    assert "id" not in MinimalUser.CreateSchema.model_fields
    assert "name" in MinimalUser.CreateSchema.model_fields


def test_update_schema_all_optional():
    for field_name, field in MinimalUser.UpdateSchema.model_fields.items():
        assert field.default is None


# ===================================================================
# 4. EDGE CASE: ALL COLUMN TYPES
# ===================================================================

@auto_schema
class AllTypes(Base):
    __tablename__ = "decorator_all_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    str_col: Mapped[str]
    int_col: Mapped[int]
    float_col: Mapped[float]
    bool_col: Mapped[bool]
    decimal_col: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    date_col: Mapped[date]
    datetime_col: Mapped[datetime]
    text_col: Mapped[str] = mapped_column(Text)
    json_col: Mapped[dict] = mapped_column(JSON)
    uuid_col: Mapped[uuid.UUID] = mapped_column(SA_UUID)
    name_50: Mapped[str] = mapped_column(String(50))


def test_all_types_have_correct_annotations():
    fields = AllTypes.Schema.model_fields

    assert fields["str_col"].annotation is str
    assert fields["int_col"].annotation is int
    assert fields["float_col"].annotation is float
    assert fields["bool_col"].annotation is bool
    assert fields["decimal_col"].annotation is Decimal
    assert fields["date_col"].annotation is date
    assert fields["datetime_col"].annotation is datetime
    assert fields["text_col"].annotation is str
    assert fields["json_col"].annotation is Any
    assert fields["uuid_col"].annotation is uuid.UUID
    assert fields["name_50"].annotation is str


def test_all_types_max_length():
    from annotated_types import MaxLen
    field = AllTypes.Schema.model_fields["name_50"]
    assert any(isinstance(m, MaxLen) and m.max_length == 50 for m in field.metadata)


# ===================================================================
# 5. EDGE CASE: NULLABLE vs NON-NULLABLE COLUMNS
# ===================================================================

@auto_schema
class NullableDemo(Base):
    __tablename__ = "decorator_nullable"

    id: Mapped[int] = mapped_column(primary_key=True)
    required_field: Mapped[str] = mapped_column(nullable=False)
    optional_field: Mapped[Optional[str]] = mapped_column(nullable=True)


def test_required_field_is_required():
    field = NullableDemo.Schema.model_fields["required_field"]
    assert field.is_required()


def test_optional_field_is_optional():
    field = NullableDemo.Schema.model_fields["optional_field"]
    assert not field.is_required()


def test_optional_field_allows_none():
    schema = NullableDemo.Schema(id=1, required_field="hello", optional_field=None)
    assert schema.optional_field is None


# ===================================================================
# 6. EDGE CASE: COLUMNS WITH DEFAULTS
# ===================================================================

@auto_schema
class WithDefaults(Base):
    __tablename__ = "decorator_with_defaults"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    score: Mapped[float] = mapped_column(default=0.0)
    active: Mapped[bool] = mapped_column(default=True)


def test_defaults_carried_into_schema():
    field = WithDefaults.Schema.model_fields["score"]
    assert field.default == 0.0

    field = WithDefaults.Schema.model_fields["active"]
    assert field.default is True


def test_create_schema_excludes_columns_with_defaults():
    assert "score" not in WithDefaults.CreateSchema.model_fields
    assert "active" not in WithDefaults.CreateSchema.model_fields
    assert "name" in WithDefaults.CreateSchema.model_fields


# ===================================================================
# 7. EDGE CASE: SERVER_DEFAULT COLUMNS
# ===================================================================

from sqlalchemy import func as sa_func

@auto_schema
class WithServerDefault(Base):
    __tablename__ = "decorator_server_default"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=sa_func.now())


def test_server_default_excluded_from_create():
    assert "created_at" not in WithServerDefault.CreateSchema.model_fields


def test_server_default_included_in_full():
    assert "created_at" in WithServerDefault.Schema.model_fields


# ===================================================================
# 8. EDGE CASE: PUBLIC SCHEMA — PRIVATE FIELDS
# ===================================================================

@auto_schema
class WithPrivateFields(Base):
    __tablename__ = "decorator_private"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    secret: Mapped[str]


def test_public_schema_includes_regular_fields():
    assert "name" in WithPrivateFields.PublicSchema.model_fields
    assert "secret" in WithPrivateFields.PublicSchema.model_fields
    assert "id" in WithPrivateFields.PublicSchema.model_fields


def test_public_schema_full_schema_match():
    assert set(WithPrivateFields.Schema.model_fields) == set(WithPrivateFields.PublicSchema.model_fields)


# ===================================================================
# 9. EDGE CASE: SchemaConfig — full config matrix
# ===================================================================

@auto_schema(config=SchemaConfig(
    exclude_always=["internal_id"],
    exclude_create=["notes"],
    exclude_update=["immutable_field"],
    exclude_public=["email"],
    field_overrides={"score": Decimal},
    required_always=["nickname"],
    optional_always=["email"],
))
class FullConfigModel(Base):
    __tablename__ = "decorator_full_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    email: Mapped[str] = mapped_column(nullable=False)
    nickname: Mapped[Optional[str]] = mapped_column(nullable=True)
    score: Mapped[float]
    internal_id: Mapped[int]
    notes: Mapped[Optional[str]] = mapped_column(nullable=True)
    immutable_field: Mapped[str]


def test_exclude_always():
    assert "internal_id" not in FullConfigModel.Schema.model_fields
    assert "internal_id" not in FullConfigModel.CreateSchema.model_fields
    assert "internal_id" not in FullConfigModel.PublicSchema.model_fields


def test_exclude_create():
    assert "notes" not in FullConfigModel.CreateSchema.model_fields
    assert "notes" in FullConfigModel.Schema.model_fields


def test_exclude_update():
    assert "immutable_field" not in FullConfigModel.UpdateSchema.model_fields
    assert "immutable_field" in FullConfigModel.Schema.model_fields


def test_exclude_public():
    assert "email" not in FullConfigModel.PublicSchema.model_fields
    assert "email" in FullConfigModel.Schema.model_fields


def test_field_override():
    field = FullConfigModel.Schema.model_fields["score"]
    assert field.annotation is Decimal


def test_required_always():
    field = FullConfigModel.Schema.model_fields["nickname"]
    assert field.is_required()


def test_optional_always():
    field = FullConfigModel.Schema.model_fields["email"]
    assert not field.is_required()


# ===================================================================
# 10. EDGE CASE: MIXIN + DECORATOR (regression)
# ===================================================================

from schemap.mixins import TimestampMixin

@auto_schema
class DecoratedWithMixin(Base, TimestampMixin):
    __tablename__ = "decorator_mixin"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]


def test_decorator_with_mixin_has_all_schemas():
    assert hasattr(DecoratedWithMixin, "Schema")
    assert hasattr(DecoratedWithMixin, "CreateSchema")
    assert hasattr(DecoratedWithMixin, "UpdateSchema")
    assert hasattr(DecoratedWithMixin, "PublicSchema")


def test_decorator_with_mixin_fields():
    assert "title" in DecoratedWithMixin.Schema.model_fields
    assert "created_at" in DecoratedWithMixin.Schema.model_fields
    assert "updated_at" in DecoratedWithMixin.Schema.model_fields


# ===================================================================
# 11. EDGE CASE: SCHEMA INDEPENDENCE — no cross-contamination
# ===================================================================

@auto_schema
class ModelA(Base):
    __tablename__ = "decorator_a"

    id: Mapped[int] = mapped_column(primary_key=True)
    a_only: Mapped[str]


@auto_schema
class ModelB(Base):
    __tablename__ = "decorator_b"

    id: Mapped[int] = mapped_column(primary_key=True)
    b_only: Mapped[str]


def test_schemas_are_independent():
    assert "a_only" in ModelA.Schema.model_fields
    assert "a_only" not in ModelB.Schema.model_fields
    assert "b_only" in ModelB.Schema.model_fields
    assert "b_only" not in ModelA.Schema.model_fields


def test_schema_names_are_distinct():
    assert ModelA.Schema.__name__ == "ModelAFullSchema"
    assert ModelB.Schema.__name__ == "ModelBFullSchema"


# ===================================================================
# 12. EDGE CASE: AutoBase (original) still works
# ===================================================================

class AutoBaseUser(AutoBase):
    __tablename__ = "decorator_autobase"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


def test_autobase_still_works():
    assert hasattr(AutoBaseUser, "Schema")
    assert hasattr(AutoBaseUser, "CreateSchema")
    assert hasattr(AutoBaseUser, "UpdateSchema")
    assert hasattr(AutoBaseUser, "PublicSchema")

    user = AutoBaseUser(id=1, name="hello")
    schema = user.to_schema()
    assert schema.name == "hello"

    rehydrated = AutoBaseUser.from_schema(schema)
    assert rehydrated.name == "hello"


# ===================================================================
# 13. EDGE CASE: PK-only model
# ===================================================================

@auto_schema
class PkOnly(Base):
    __tablename__ = "decorator_pk_only"

    id: Mapped[int] = mapped_column(primary_key=True)


def test_pk_only_schema():
    assert "id" in PkOnly.Schema.model_fields
    assert "id" in PkOnly.PublicSchema.model_fields


def test_pk_only_create_has_no_fields():
    assert len(PkOnly.CreateSchema.model_fields) == 0


def test_pk_only_update_has_no_fields():
    assert len(PkOnly.UpdateSchema.model_fields) == 0


# ===================================================================
# 14. EDGE CASE: to_schema with UpdateSchema (all-optional)
# ===================================================================

@auto_schema
class ForUpdate(Base):
    __tablename__ = "decorator_for_update"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    age: Mapped[int]


def test_to_schema_with_update():
    user = ForUpdate(id=10, name="dave", age=30)
    schema = user.to_schema(ForUpdate.UpdateSchema)
    assert schema.name == "dave"
    assert schema.age == 30
    assert not hasattr(schema, "id")


# ===================================================================
# 15. EDGE CASE: ValidationError on bad data
# ===================================================================

@auto_schema
class StrictModel(Base):
    __tablename__ = "decorator_strict"

    id: Mapped[int] = mapped_column(primary_key=True)
    age: Mapped[int]


def test_validation_error_on_wrong_type():
    with pytest.raises(ValidationError):
        StrictModel.Schema(id=1, age="not_a_number")


# ===================================================================
# 16. BUGFIX: from_schema preserves explicit None values
# ===================================================================

@auto_schema
class NonePreserve(Base):
    __tablename__ = "decorator_none_preserve"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    bio: Mapped[Optional[str]] = mapped_column(nullable=True)


def test_from_schema_preserves_explicit_none():
    """from_schema should not drop fields set to None."""
    data = NonePreserve.CreateSchema(name="alice", bio=None)
    user = NonePreserve.from_schema(data)
    assert user.name == "alice"
    assert user.bio is None


def test_from_schema_drops_unset_fields():
    """from_schema should drop fields not provided in the schema."""
    data = NonePreserve.CreateSchema(name="bob")
    user = NonePreserve.from_schema(data)
    assert user.name == "bob"
    assert user.bio is None


# ===================================================================
# 17. EDGE CASE: Empty create/update schemas (PK-only model)
# ===================================================================

@auto_schema
class EdgePkOnly(Base):
    __tablename__ = "decorator_edge_pk_only"

    id: Mapped[int] = mapped_column(primary_key=True)


def test_pk_only_create_is_empty():
    """CreateSchema for PK-only model should have zero fields."""
    assert len(EdgePkOnly.CreateSchema.model_fields) == 0


def test_pk_only_update_is_empty():
    """UpdateSchema for PK-only model should have zero fields."""
    assert len(EdgePkOnly.UpdateSchema.model_fields) == 0


def test_pk_only_full_has_pk():
    """Full schema should still have the PK."""
    assert "id" in EdgePkOnly.Schema.model_fields


# ===================================================================
# 18. EDGE CASE: from_schema with UpdateSchema (no PK)
# ===================================================================

@auto_schema
class ForFromUpdate(Base):
    __tablename__ = "decorator_from_update"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    age: Mapped[int]


def test_from_schema_with_update_schema():
    """from_schema with UpdateSchema should work (PK absent, ORM gets None)."""
    data = ForFromUpdate.UpdateSchema(name="dave", age=30)
    obj = ForFromUpdate.from_schema(data)
    assert obj.name == "dave"
    assert obj.age == 30
    assert obj.id is None


# ===================================================================
# 19. EDGE CASE: should_include with unknown schema_type
# ===================================================================

def test_unknown_schema_type_raises():
    """build_schema with unknown schema_type should raise ValueError."""
    from schemap.builder import build_schema
    with pytest.raises(ValueError, match="Unknown schema_type"):
        build_schema(ForFromUpdate, "bogus")


# ===================================================================
# 20. EDGE CASE: SchemaConfig with no config (standalone build_schema)
# ===================================================================

def test_build_schema_no_config():
    """build_schema without config should work with all schema types."""
    from schemap.builder import build_schema

    s = build_schema(ForFromUpdate, "full")
    assert "name" in s.model_fields

    s = build_schema(ForFromUpdate, "create")
    assert "id" not in s.model_fields

    s = build_schema(ForFromUpdate, "update")
    for f in s.model_fields.values():
        assert f.default is None

    s = build_schema(ForFromUpdate, "public")
    assert "name" in s.model_fields


# ===================================================================
# 21. HARDENING: Callable defaults use default_factory
# ===================================================================

@auto_schema
class WithCallableDefault(Base):
    __tablename__ = "decorator_callable_default"

    id: Mapped[int] = mapped_column(primary_key=True)
    seq_num: Mapped[int] = mapped_column(default=lambda: 42)


def test_callable_default_not_stored_as_function():
    """Callable default should be invoked, not stored as a function object."""
    field = WithCallableDefault.Schema.model_fields["seq_num"]
    # Pydantic stores callable defaults in default_factory, not default
    assert field.default_factory is not None
    assert field.default_factory() == 42


def test_callable_default_excluded_from_create():
    """Columns with callable defaults should be excluded from CreateSchema."""
    assert "seq_num" not in WithCallableDefault.CreateSchema.model_fields


def test_callable_default_in_full_schema():
    """Columns with callable defaults should be included in full Schema."""
    assert "seq_num" in WithCallableDefault.Schema.model_fields


# ===================================================================
# 22. HARDENING: JSON columns accept any type
# ===================================================================

@auto_schema
class WithJson(Base):
    __tablename__ = "decorator_json"

    id: Mapped[int] = mapped_column(primary_key=True)
    data: Mapped[dict] = mapped_column(JSON)


def test_json_field_allows_lists():
    """JSON field should accept lists, not just dicts."""
    from typing import Any
    field = WithJson.Schema.model_fields["data"]
    # Should be typed as Any, not dict
    assert field.annotation is Any


# ===================================================================
# 23. HARDENING: from_schema accepts dicts
# ===================================================================

def test_from_schema_accepts_dict():
    """from_schema should accept a plain dict."""
    user = ForFromUpdate.from_schema({"name": "eve", "age": 25})
    assert user.name == "eve"
    assert user.age == 25


def test_from_schema_dict_drops_unset():
    """from_schema with dict should drop fields not in the dict."""
    user = ForFromUpdate.from_schema({"name": "frank"})
    assert user.name == "frank"
    assert user.id is None
    assert user.age is None


# ===================================================================
# 24. HARDENING: Enum columns work end-to-end
# ===================================================================

import enum

class Mood(enum.Enum):
    HAPPY = "happy"
    SAD = "sad"


@auto_schema
class WithEnum(Base):
    __tablename__ = "decorator_enum"

    id: Mapped[int] = mapped_column(primary_key=True)
    mood: Mapped[Mood] = mapped_column(SAEnum(Mood))


def test_enum_field_uses_concrete_class():
    """Enum field should be typed as the concrete enum, not abstract enum.Enum."""
    field = WithEnum.Schema.model_fields["mood"]
    assert field.annotation is Mood


def test_enum_field_validates():
    """Enum field should validate enum members."""
    schema = WithEnum.Schema(id=1, mood=Mood.HAPPY)
    assert schema.mood is Mood.HAPPY

    with pytest.raises(ValidationError):
        WithEnum.Schema(id=1, mood="invalid")


# ===================================================================
# 25. GAP: from_schema dict ignores unknown keys
# ===================================================================

def test_from_schema_dict_ignores_unknown_keys():
    """from_schema with dict should silently ignore keys not in the model."""
    user = ForFromUpdate.from_schema({"name": "x", "unknown_key": 123, "another": True})
    assert user.name == "x"
    assert not hasattr(user, "unknown_key")
    assert not hasattr(user, "another")


# ===================================================================
# 26. GAP: Composite primary key
# ===================================================================

from sqlalchemy import ForeignKey as SA_FK

@auto_schema
class CompositePK(Base):
    __tablename__ = "decorator_composite_pk"

    tenant_id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(primary_key=True)
    value: Mapped[str]


def test_composite_pk_full_schema_has_both():
    """Full schema should include both PK columns."""
    fields = CompositePK.Schema.model_fields
    assert "tenant_id" in fields
    assert "item_id" in fields
    assert "value" in fields


def test_composite_pk_create_excludes_both():
    """CreateSchema should exclude both PK columns."""
    fields = CompositePK.CreateSchema.model_fields
    assert "tenant_id" not in fields
    assert "item_id" not in fields
    assert "value" in fields


def test_composite_pk_update_excludes_both():
    """UpdateSchema should exclude both PK columns."""
    fields = CompositePK.UpdateSchema.model_fields
    assert "tenant_id" not in fields
    assert "item_id" not in fields
    assert "value" in fields


def test_composite_pk_round_trip():
    """Round-trip with composite PK should preserve both keys."""
    obj = CompositePK(tenant_id=1, item_id=42, value="hello")
    schema = obj.to_schema()
    rehydrated = CompositePK.from_schema(schema)
    assert rehydrated.tenant_id == 1
    assert rehydrated.item_id == 42
    assert rehydrated.value == "hello"


# ===================================================================
# 27. GAP: Mixin fields with __schema_config__
# ===================================================================

@auto_schema(config=SchemaConfig(exclude_create=["created_at"]))
class WithMixinAndConfig(Base, TimestampMixin):
    __tablename__ = "decorator_mixin_config"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]


def test_mixin_field_excluded_by_config():
    """Config should be able to exclude mixin-provided fields."""
    assert "created_at" not in WithMixinAndConfig.CreateSchema.model_fields
    assert "created_at" in WithMixinAndConfig.Schema.model_fields


# ===================================================================
# 28. GAP: Required + override on same field
# ===================================================================

@auto_schema(config=SchemaConfig(
    required_always=["email"],
    field_overrides={"email": str},
))
class RequiredWithOverride(Base):
    __tablename__ = "decorator_required_override"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str]


def test_required_with_override():
    """required_always + field_overrides on same field should work."""
    field = RequiredWithOverride.Schema.model_fields["email"]
    assert field.is_required()
    assert field.annotation is str


# ===================================================================
# 29. GAP: VersionMixin excluded from CreateSchema
# ===================================================================

from schemap.mixins import VersionMixin

@auto_schema
class VersionedModel(Base, VersionMixin):
    __tablename__ = "decorator_versioned"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]


def test_version_excluded_from_create():
    """VersionMixin.version (default=1) should be excluded from CreateSchema."""
    assert "version" not in VersionedModel.CreateSchema.model_fields


def test_version_in_full_schema():
    """VersionMixin.version should be in full Schema."""
    assert "version" in VersionedModel.Schema.model_fields


def test_version_default_in_schema():
    """VersionMixin.version should have default=1 in full Schema."""
    field = VersionedModel.Schema.model_fields["version"]
    assert field.default == 1
