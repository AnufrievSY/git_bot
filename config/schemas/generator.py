"""
Schema generator utilities.

This module provides:
- `dict_to_pydantic_model`: Generates a Pydantic model file from a Python dictionary
  using `datamodel-code-generator`.
- `load_schema`: Dynamically loads a generated Pydantic class from a given file path.

These tools are helpful for projects that need to persist schemas derived from runtime
data structures and reload them later.
"""

import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Type

from datamodel_code_generator import generate, InputFileType, PythonVersion

# Root directory of this module
ROOT = Path(__file__).parent


def dict_to_pydantic_model(
    data: Dict[str, Any],
    output_file: Path | str = ROOT / "models.py",
    class_name: str = "Config",
) -> None:
    """
    Generate a Pydantic model schema from the provided dictionary, save it as a Python file,
    and remove the temporary JSON file used for generation.

    Args:
        data: Dictionary describing the structure to infer the Pydantic model from.
        output_file: Destination file path for the generated model (e.g., "models.py").
        class_name: Name of the generated root class.

    Raises:
        OSError: If writing or deleting temporary files fails.
        Exception: If datamodel-code-generator fails internally.
    """
    tmp_path: Path

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        json.dump(data, tmp, ensure_ascii=False, indent=2)
        tmp_path = Path(tmp.name)

    try:
        generate(
            input_=tmp_path,
            input_file_type=InputFileType.Json,
            output=Path(output_file),
            target_python_version=PythonVersion.PY_312,
            use_default_kwarg=True,
            class_name=class_name,
        )
    finally:
        tmp_path.unlink(missing_ok=True)


def load_schema(module_path: Path | str, class_name: str) -> Type[Any]:
    """
    Dynamically import and return a class from a given Python module file.

    Args:
        module_path: Path to the Python module file (.py).
        class_name: Name of the class to be imported.

    Returns:
        The imported class object.

    Raises:
        ImportError: If the module cannot be loaded or the class is not found.
    """
    module_path = Path(module_path).resolve()
    module_name = module_path.stem

    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Failed to load module from path: {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)

    try:
        return getattr(module, class_name)
    except AttributeError as exc:
        raise ImportError(
            f"Class '{class_name}' not found in module {module_path}"
        ) from exc
