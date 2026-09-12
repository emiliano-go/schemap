"""Tests for type resolution."""

import enum
import pytest
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import Integer, String, Boolean, DateTime, Date, Float, Text, JSON, Enum as SAEnum, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Column

from schemap.types import extract_python_type, extract_column_metadata


def test_simple_type_mapping():
    """Test that basic SQLAlchemy types map to correct Python types."""
    assert extract_python_type(Integer()) == (int, False)
    assert extract_python_type(String()) == (str, False)
    assert extract_python_type(Boolean()) == (bool, False)
    assert extract_python_type(Float()) == (float, False)
    assert extract_python_type(DateTime()) == (datetime, False)
    assert extract_python_type(Date()) == (date, False)
    assert extract_python_type(Text()) == (str, False)


class Color(enum.Enum):
    RED = "red"
    GREEN = "green"
    BLUE = "blue"


def test_enum_type_mapping():
    """Test that SQLAlchemy Enum maps to the concrete Python enum class."""
    col = Column("color", SAEnum(Color), nullable=False)
    py_type, is_optional = extract_python_type(col)
    assert py_type is Color
    assert is_optional is False


def test_column_metadata_basics():
    """Test extraction of column properties."""
    col = Column("id", Integer, primary_key=True, nullable=False)
    metadata = extract_column_metadata(col)

    assert metadata["python_type"] == int
    assert metadata["is_optional"] is False
    assert metadata["primary_key"] is True


def test_string_length():
    """Test that String(100) captures max_length."""
    col = Column("name", String(100), nullable=False)
    metadata = extract_column_metadata(col)

    assert metadata["max_length"] == 100


def test_nullable_column():
    """Test that nullable=True sets is_optional=True."""
    col = Column("bio", Text, nullable=True)
    metadata = extract_column_metadata(col)

    assert metadata["is_optional"] is True


def test_callable_default_extracted():
    """Test that callable defaults are stored as default_factory, not default."""
    col = Column("seq", Integer, default=lambda ctx: 42)
    metadata = extract_column_metadata(col)

    assert metadata["default"] is None
    assert metadata["default_factory"] is not None
    assert callable(metadata["default_factory"])


def test_non_callable_default_extracted():
    """Test that non-callable defaults are stored as default."""
    col = Column("score", Float, default=0.0)
    metadata = extract_column_metadata(col)

    assert metadata["default"] == 0.0
    assert metadata["default_factory"] is None


def test_numeric_precision():
    """Test that Numeric precision and scale are extracted."""
    col = Column("price", Numeric(10, 2), nullable=False)
    metadata = extract_column_metadata(col)

    assert metadata["precision"] == 10
    assert metadata["scale"] == 2


def test_json_maps_to_any():
    """Test that JSON columns map to Any (not dict)."""
    from typing import Any as TypingAny
    col = Column("data", JSON, nullable=False)
    py_type, _ = extract_python_type(col)
    assert py_type is TypingAny
