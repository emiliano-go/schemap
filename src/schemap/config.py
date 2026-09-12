from dataclasses import dataclass, field
from typing import Any
from collections.abc import Callable


@dataclass
class SchemaConfig:
    """Configuration for auto-generated Pydantic schemas.

    Customize which fields appear in each schema variant, override field
    types, and attach custom validators.

    Example::

        from schemap import SchemaConfig

        config = SchemaConfig(
            exclude_always=["internal_id"],
            exclude_public=["email", "password_hash"],
            field_overrides={"score": Decimal},
            required_always=["nickname"],
            optional_always=["bio"],
        )

        class MyModel(AutoBase):
            __schema_config__ = config
            ...

    Raises:
        ValueError: If a field appears in both ``required_always`` and
            ``optional_always``.
    """

    # Fields to exclude from specific schemas
    exclude_always: list[str] = field(default_factory=list)
    """Fields excluded from *all* schema variants.

    Example::

        SchemaConfig(exclude_always=["internal_id", "password_hash"])
    """

    exclude_create: list[str] = field(default_factory=list)
    """Fields excluded from ``CreateSchema`` only.

    Example::

        SchemaConfig(exclude_create=["notes"])
    """

    exclude_update: list[str] = field(default_factory=list)
    """Fields excluded from ``UpdateSchema`` only.

    Example::

        SchemaConfig(exclude_update=["created_at"])
    """

    exclude_public: list[str] = field(default_factory=list)
    """Fields excluded from ``PublicSchema`` only.

    Example::

        SchemaConfig(exclude_public=["email", "ssn"])
    """

    # Override field types or add validation
    field_overrides: dict[str, Any] = field(default_factory=dict)
    """Override the Python type used for specific fields.

    Keys are column names, values are Python types (including
    ``Optional[X]``, ``Union`` types, ``Decimal``, etc.).

    Example::

        SchemaConfig(field_overrides={
            "score": Decimal,
            "tags": list[str],
            "metadata": Optional[dict],
        })
    """

    # Force required/optional
    required_always: list[str] = field(default_factory=list)
    """Force fields to be required in all schema variants.

    Overrides the default nullable-based inference.

    Example::

        SchemaConfig(required_always=["email"])
    """

    optional_always: list[str] = field(default_factory=list)
    """Force fields to be optional in all schema variants.

    Overrides the default nullable-based inference.

    Example::

        SchemaConfig(optional_always=["bio", "nickname"])
    """

    # Custom validators to attach
    extra_validators: dict[str, Callable] = field(default_factory=dict)
    """Attach custom Pydantic validators to specific fields.

    Keys are field names, values are validator functions.

    Example::

        def must_be_positive(v: float) -> float:
            if v <= 0:
                raise ValueError("Must be positive")
            return v

        SchemaConfig(extra_validators={"price": must_be_positive})
    """

    # Prefixes to exclude from public schema (default: double-underscore)
    public_exclude_prefix: tuple[str, ...] = ("__",)
    """Column name prefixes excluded from ``PublicSchema``.

    Defaults to ``("__",)`` which hides SQLAlchemy internal columns.
    Set to ``()`` to disable prefix-based exclusion.

    Example::

        SchemaConfig(public_exclude_prefix=("_secret", "__"))
    """

    def __post_init__(self) -> None:
        conflict = set(self.required_always) & set(self.optional_always)
        if conflict:
            raise ValueError(
                f"Fields in both required_always and optional_always: {conflict}"
            )
