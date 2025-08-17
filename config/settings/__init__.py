"""
Settings utilities package.

This package exposes helpers to:
- Save dictionaries to YAML files.
- Read YAML configuration.
- Persist a GitHub token into `general.ini`.
- (Re-export) Schema generation helpers for convenience.

Public API:
    dict_to_yaml, load_yaml, write_token,
    dict_to_pydantic_model, load_schema
"""

from .generator import dict_to_yaml, load_yaml, write_token  # local exports
from config.schemas.generator import (  # convenient re-exports
    dict_to_pydantic_model,
    load_schema,
)

__all__ = [
    "dict_to_yaml",
    "load_yaml",
    "write_token",
    "dict_to_pydantic_model",
    "load_schema",
]
