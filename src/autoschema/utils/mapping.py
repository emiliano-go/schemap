from sqlalchemy import types as sa_types
from datetime import date, time, datetime
from decimal import Decimal
import uuid

TYPE_MAP = {
    # --- Strings ---
    sa_types.String: str,
    sa_types.Text: str,
    sa_types.Unicode: str,
    sa_types.UnicodeText: str,
    sa_types.CHAR: str,
    sa_types.VARCHAR: str,
    sa_types.NCHAR: str,
    sa_types.NVARCHAR: str,
    sa_types.CLOB: str,

    # --- Integers ---
    sa_types.Integer: int,
    sa_types.SmallInteger: int,
    sa_types.BigInteger: int,

    # --- Numeric ---
    sa_types.Numeric: Decimal,
    sa_types.DECIMAL: Decimal,

    # --- Floating point ---
    sa_types.Float: float,
    sa_types.REAL: float,

    # --- Boolean ---
    sa_types.Boolean: bool,

    # --- Date / Time ---
    sa_types.Date: date,
    sa_types.Time: time,
    sa_types.DateTime: datetime,
    sa_types.TIMESTAMP: datetime,

    # --- Binary ---
    sa_types.LargeBinary: bytes,
    sa_types.BLOB: bytes,
    sa_types.BINARY: bytes,
    sa_types.VARBINARY: bytes,

    # --- JSON ---
    sa_types.JSON: dict,

    # --- UUID ---
    sa_types.UUID: uuid.UUID,

    # --- Arrays ---
    sa_types.ARRAY: list,

    # --- Generic fallback ---
    sa_types.NullType: object,
}
