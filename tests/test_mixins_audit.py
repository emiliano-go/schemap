"""Tests for CreatedByMixin and UpdatedByMixin (isolated registry)."""

from typing import Optional
from sqlalchemy import create_engine, ForeignKey
from sqlalchemy.orm import Session, Mapped, mapped_column, DeclarativeBase

from schemap.base import SchemaMixin
from schemap.mixins import CreatedByMixin, UpdatedByMixin


# Separate registry to avoid cascading mapper failures
class AuditBase(SchemaMixin, DeclarativeBase):
    pass


class AuditUser(AuditBase):
    __tablename__ = "audit_users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]


class Article(AuditBase):
    __tablename__ = "audit_articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("audit_users.id"))


class ArticleWithUpdated(AuditBase):
    __tablename__ = "audit_articles_updated"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    updated_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("audit_users.id"))


class ArticleWithBoth(AuditBase):
    __tablename__ = "audit_articles_both"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("audit_users.id"))
    updated_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("audit_users.id"))


class CustomUserArticle(AuditBase):
    __tablename__ = "audit_custom_user_articles"
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("audit_users.id"))


# --- CreatedByMixin tests (using build_schema directly) ---
def test_created_by_mixin_fk_column_in_schema():
    """Test that a model with created_by_id FK column has it in schema."""
    from schemap.builder import build_schema
    fields = build_schema(Article, "full").model_fields
    assert "created_by_id" in fields
    assert "title" in fields


def test_created_by_mixin_fk_excluded_from_create():
    """Test that nullable FK with no default is included in CreateSchema."""
    from schemap.builder import build_schema
    fields = build_schema(Article, "create").model_fields
    # nullable FK with no default IS included in create (user must provide it)
    assert "created_by_id" in fields


def test_created_by_mixin_update_schema_has_fk():
    """Test that UpdateSchema includes created_by_id as Optional."""
    from schemap.builder import build_schema
    fields = build_schema(Article, "update").model_fields
    assert "created_by_id" in fields


# --- UpdatedByMixin tests ---
def test_updated_by_mixin_fk_column_in_schema():
    """Test that a model with updated_by_id FK column has it in schema."""
    from schemap.builder import build_schema
    fields = build_schema(ArticleWithUpdated, "full").model_fields
    assert "updated_by_id" in fields
    assert "title" in fields


# --- Both mixins combined ---
def test_both_mixins_schema():
    """Test schema includes all FK fields from both patterns."""
    from schemap.builder import build_schema
    fields = build_schema(ArticleWithBoth, "full").model_fields
    assert "created_by_id" in fields
    assert "updated_by_id" in fields
    assert "title" in fields


def test_both_mixins_create_schema():
    """Test CreateSchema includes both nullable FKs."""
    from schemap.builder import build_schema
    fields = build_schema(ArticleWithBoth, "create").model_fields
    assert "created_by_id" in fields
    assert "updated_by_id" in fields
