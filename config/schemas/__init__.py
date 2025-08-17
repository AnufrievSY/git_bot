"""
Schema utilities package.

This package contains tools for:
- Generating Pydantic models dynamically from dictionaries.
- Dynamically importing generated schema classes.
"""

from .generator import dict_to_pydantic_model, load_schema

__all__ = ["dict_to_pydantic_model", "load_schema"]
