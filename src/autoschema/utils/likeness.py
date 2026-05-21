from typing import Protocol, Optional, Set, Any
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.sql.schema import (
    ColumnDefault,
    DefaultClause,
    Identity,
    Computed,
    ForeignKey,
    Constraint,
    DialectKWArgs,
)


class ColumnLike(Protocol):
    """Protocol for objects that behave like SQLAlchemy Column."""

    # --- Identity ---
    name: str
    key: str

    # --- Type ---
    type: TypeEngine[Any]

    # --- Nullability / defaults ---
    nullable: bool
    default: Optional[ColumnDefault]
    server_default: Optional[DefaultClause]
    autoincrement: Any  # SQLAlchemy uses bool | Literal["auto"] | etc

    # --- Constraints / keys ---
    primary_key: bool
    unique: Optional[bool]
    index: Optional[bool]
    foreign_keys: Set[ForeignKey]
    constraints: Set[Constraint]

    # --- Generated / identity ---
    identity: Optional[Identity]
    computed: Optional[Computed]

    # --- Docs / comments ---
    comment: Optional[str]
    doc: Optional[str]

    # --- Misc ---
    quote: Optional[bool]
    system: bool
    info: dict[str, Any]
    dialect_options: DialectKWArgs