from typing import Type, Any, Optional
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import inspect
from pydantic import create_model, ConfigDict, Field

from .types import extract_column_metadata
from .utils.schema import should_include, transform_for_schema


def build_schema(
    model: Type[DeclarativeBase],
    schema_type: str = "default",  # "default", "create", "update", "public"
    config: Optional[Any] = None,  # SchemaConfig
) -> Any:
    """
    Build a Pydantic schema class for a SQLAlchemy model.
    
    Args:
        model: The SQLAlchemy model class (e.g., User)
        schema_type: Which schema variant to build
        config: Optional SchemaConfig for customization
        
    Returns:
        A Pydantic model class
    """
    
    inspector = inspect(model)

    columns_meta = []

    for col in inspector.columns:
        meta = extract_column_metadata(col)
        if should_include(schema_type, meta):
            columns_meta.append(meta)

    fields = {}
    
    for col_meta in columns_meta:
        field_type, field_kwargs = transform_for_schema(col_meta, schema_type)
        fields[col_meta["name"]] = (field_type, field_kwargs)

    schema_name = f"{model.__name__}{schema_type.capitalize()}Schema"

    return create_model(schema_name, __config__=ConfigDict(from_attributes=True, **fields))