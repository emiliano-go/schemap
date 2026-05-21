from typing import Any, Optional
from pydantic import Field

def should_include(schema_type : str, metadata : dict[str, Any]):
    """Determine if a column should be included in the schema."""
    
    if schema_type == "default":
        return True
    
    elif schema_type == "create":
        # Exclude primary keys and server_default fields
        if metadata["primary_key"]:
            return False
        if metadata.get("server_default") is not None:
            return False
        return True
    
    elif schema_type == "update":
        # Exclude primary keys only
        if metadata["primary_key"]:
            return False
        return True
    
    elif schema_type == "public":
        # Exclude fields starting with __ (private)
        if metadata["name"].startswith("__"):
            return False
        return True
    
    else:
        raise ValueError(f"Unknown schema_type: {schema_type}")
    
def transform_for_schema(metadata: dict, schema_type: str) -> tuple[type, Any]:
    """Transform column metadata into (field_type, Field(...)) for create_model."""
    
    python_type = metadata["python_type"]
    
    # Build Field kwargs from constraints
    field_kwargs = {}
    
    # String length constraint
    if metadata.get("max_length") is not None:
        field_kwargs["max_length"] = metadata["max_length"]
    
    if schema_type == "update":
        field_kwargs["default"] = None
        return (Optional[python_type], Field(**field_kwargs))
    
    elif schema_type == "create":
        if metadata.get("default") is not None:
            field_kwargs["default"] = metadata["default"]
            return (python_type, Field(**field_kwargs))
        elif metadata["is_optional"]:
            field_kwargs["default"] = None
            return (Optional[python_type], Field(**field_kwargs))
        else:
            return (python_type, Field(**field_kwargs) if field_kwargs else ...)
    
    else:  # default or public
        if metadata.get("default") is not None:
            field_kwargs["default"] = metadata["default"]
            return (python_type, Field(**field_kwargs))
        elif metadata["is_optional"]:
            from typing import Optional
            field_kwargs["default"] = None
            return (Optional[python_type], Field(**field_kwargs))
        else:
            return (python_type, Field(**field_kwargs) if field_kwargs else ...)