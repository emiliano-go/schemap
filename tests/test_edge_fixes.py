"""Tests for edge-case fixes #5, #10, #11, #12."""

from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from schemap import auto_schema
from schemap.builder import build_schema
from schemap.utils.schema import from_schema


class Base(DeclarativeBase):
    pass


# ===================================================================
# #5: __qualname__ with <locals> in schema names
# ===================================================================

def _make_model():
    """Create a model inside a function to trigger <locals> in __qualname__."""

    @auto_schema
    class LocalModel(Base):
        __tablename__ = "test_locals"
        id: Mapped[int] = mapped_column(primary_key=True)
        name: Mapped[str]

    return LocalModel


def test_qualname_locals_stripped_from_schema_name():
    """Schema names should not contain <locals> segments."""
    Model = _make_model()
    assert "<locals>" not in Model.Schema.__name__
    assert Model.Schema.__name__ == "LocalModelFullSchema"
    assert Model.CreateSchema.__name__ == "LocalModelCreateSchema"
    assert Model.UpdateSchema.__name__ == "LocalModelUpdateSchema"
    assert Model.PublicSchema.__name__ == "LocalModelPublicSchema"


# ===================================================================
# #10: from_schema drops Ellipsis values silently
# ===================================================================

@auto_schema
class WithOptional(Base):
    __tablename__ = "test_ellipsis"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str]
    bio: Mapped[Optional[str]] = mapped_column(nullable=True)


def test_from_schema_dict_drops_ellipsis():
    """Ellipsis values in dicts should be treated as 'unset' and dropped."""
    obj = from_schema(WithOptional, {"name": "alice", "bio": ...})
    assert obj.name == "alice"
    assert obj.bio is None


def test_from_schema_dict_keeps_none():
    """None should be preserved (distinct from Ellipsis)."""
    obj = from_schema(WithOptional, {"name": "bob", "bio": None})
    assert obj.name == "bob"
    assert obj.bio is None


# ===================================================================
# #11: Callable default wrapper — no-arg callable
# ===================================================================

def _no_arg_default():
    """Default that takes no arguments (not even context)."""
    return 99


@auto_schema
class WithNoArgDefault(Base):
    __tablename__ = "test_no_arg_default"
    id: Mapped[int] = mapped_column(primary_key=True)
    seq: Mapped[int] = mapped_column(default=_no_arg_default)


def test_no_arg_callable_default_works():
    """Callable that takes no args should work as a default."""
    field = WithNoArgDefault.Schema.model_fields["seq"]
    assert field.default_factory is not None
    assert field.default_factory() == 99


def test_no_arg_callable_default_excluded_from_create():
    """Callable default column should be excluded from CreateSchema."""
    assert "seq" not in WithNoArgDefault.CreateSchema.model_fields


# ===================================================================
# #12: CreatedByMixin with actual relationship
# ===================================================================

from schemap.mixins import CreatedByMixin, UpdatedByMixin


class ArticleWithCreatedBy(Base, CreatedByMixin):
    __tablename__ = "test_mixin_articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]


class ArticleWithUpdatedBy(Base, UpdatedByMixin):
    __tablename__ = "test_mixin_updated"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]


def test_createdby_mixin_no_forward_ref_error():
    """CreatedByMixin should not raise errors at class definition time."""
    fields = build_schema(ArticleWithCreatedBy, "full").model_fields
    assert "created_by_id" in fields
    assert "title" in fields


def test_updatedby_mixin_no_forward_ref_error():
    """UpdatedByMixin should not raise errors at class definition time."""
    fields = build_schema(ArticleWithUpdatedBy, "full").model_fields
    assert "updated_by_id" in fields
    assert "title" in fields


def test_createdby_mixin_fk_is_optional():
    """created_by_id FK should be optional (nullable)."""
    field = build_schema(ArticleWithCreatedBy, "full").model_fields["created_by_id"]
    assert field.is_required() is False
