"""Tests for type resolution."""

import enum
import uuid
import pytest
from datetime import datetime, date, time
from decimal import Decimal
from typing import Any
from sqlalchemy import (
    Integer, String, Boolean, DateTime, Date, Float, Text, JSON,
    Enum as SAEnum, Numeric, SmallInteger, BigInteger, DECIMAL, REAL,
    Time, TIMESTAMP, Unicode, UnicodeText, CHAR, VARCHAR, NCHAR, NVARCHAR, CLOB,
    LargeBinary, BLOB, BINARY, VARBINARY, ARRAY, TypeDecorator,
)
from sqlalchemy.sql.sqltypes import NullType
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
    col = Column("data", JSON, nullable=False)
    py_type, _ = extract_python_type(col)
    assert py_type is Any


# ===================================================================
# TYPE_MAP completeness — all entries resolve correctly
# ===================================================================

@pytest.mark.parametrize("sa_type,expected", [
    (SmallInteger(), int),
    (BigInteger(), int),
    (DECIMAL(), Decimal),
    (REAL(), float),
    (Time(), time),
    (TIMESTAMP(), datetime),
    (Unicode(), str),
    (UnicodeText(), str),
    (CHAR(), str),
    (VARCHAR(), str),
    (NCHAR(), str),
    (NVARCHAR(), str),
    (CLOB(), str),
    (LargeBinary(), bytes),
    (BLOB(), bytes),
    (BINARY(), bytes),
    (VARBINARY(), bytes),
    (NullType(), object),
])
def test_type_map_completeness(sa_type, expected):
    """Every TYPE_MAP entry resolves to the expected Python type."""
    result, is_optional = extract_python_type(sa_type)
    assert result is expected
    assert is_optional is False


# ===================================================================
# ARRAY inner type preservation
# ===================================================================

def test_array_integer():
    """ARRAY(Integer) should resolve to list[int]."""
    col = Column("tags", ARRAY(Integer))
    py_type, _ = extract_python_type(col)
    assert py_type == list[int]


def test_array_string():
    """ARRAY(String) should resolve to list[str]."""
    col = Column("names", ARRAY(String(50)))
    py_type, _ = extract_python_type(col)
    assert py_type == list[str]


# ===================================================================
# TypeDecorator support
# ===================================================================

class EncryptedString(TypeDecorator):
    """Custom TypeDecorator wrapping String."""
    impl = String
    cache_ok = True


class GUID(TypeDecorator):
    """Custom TypeDecorator wrapping LargeBinary for UUID storage."""
    impl = BLOB
    cache_ok = True


def test_typedef_decorator_string():
    """TypeDecorator wrapping String should resolve to str."""
    col = Column("secret", EncryptedString(256))
    py_type, _ = extract_python_type(col)
    assert py_type is str


def test_typedef_decorator_blob():
    """TypeDecorator wrapping LargeBinary should resolve to bytes."""
    col = Column("guid", GUID())
    py_type, _ = extract_python_type(col)
    assert py_type is bytes


def test_typedef_decorator_in_metadata():
    """TypeDecorator column metadata should have correct python_type."""
    col = Column("secret", EncryptedString(100))
    meta = extract_column_metadata(col)
    assert meta["python_type"] is str
    assert meta["max_length"] == 100


# ===================================================================
# String-based Enum (without Python class)
# ===================================================================

def test_string_enum_falls_back_to_str():
    """Enum('A','B') without Python class should resolve to str."""
    col = Column("status", SAEnum("active", "inactive"))
    py_type, _ = extract_python_type(col)
    assert py_type is str


# ===================================================================
# Composition: TypeDecorator + ARRAY + Enum
# ===================================================================

class DoubleEncrypted(TypeDecorator):
    """Nested TypeDecorator: wraps another TypeDecorator."""
    impl = EncryptedString
    cache_ok = True


def test_nested_typedef():
    """Nested TypeDecorator should resolve to the innermost impl type."""
    col = Column("deep", DoubleEncrypted(128))
    py_type, _ = extract_python_type(col)
    assert py_type is str


def test_array_of_typedef():
    """ARRAY(TypeDecorator(String)) should resolve to list[str]."""
    col = Column("secrets", ARRAY(EncryptedString(256)))
    py_type, _ = extract_python_type(col)
    assert py_type == list[str]


def test_array_of_enum():
    """ARRAY(Enum(Color)) should resolve to list[Color]."""
    col = Column("colors", ARRAY(SAEnum(Color)))
    py_type, _ = extract_python_type(col)
    assert py_type == list[Color]


def test_typedef_wrapping_array():
    """TypeDecorator(ARRAY(String)) should resolve to list[str]."""

    class ArrayString(TypeDecorator):
        impl = ARRAY(String(100))
        cache_ok = True

    col = Column("tags", ArrayString())
    py_type, _ = extract_python_type(col)
    assert py_type == list[str]


def test_typedef_wrapping_array_of_typedef():
    """TypeDecorator(ARRAY(TypeDecorator(String))) should resolve to list[str]."""

    class DeepArray(TypeDecorator):
        impl = ARRAY(EncryptedString(256))
        cache_ok = True

    col = Column("deep_tags", DeepArray())
    py_type, _ = extract_python_type(col)
    assert py_type == list[str]
