"""
Settings helpers: YAML I/O and token persistence.

This module provides small, production-ready utilities:
- `dict_to_yaml`: persist a Python dictionary to a YAML file.
- `load_yaml`: read a YAML file into a dictionary.
- `write_token`: store a token in `general.ini` using configparser.

All functions use pathlib, include basic validation, and raise clear errors
on invalid inputs or I/O failures.
"""

import configparser
from pathlib import Path
from typing import Any, Dict, Mapping, Union

import yaml

# Base directory for settings files (same folder as this module).
ROOT: Path = Path(__file__).parent


def dict_to_yaml(
    data: Mapping[str, Any],
    output_file: Union[str, Path] = ROOT / "settings.yaml",
) -> None:
    """
    Persist a mapping to a YAML file.

    Args:
        data: Input mapping to serialize.
        output_file: Destination path (e.g., "settings.yaml").

    Raises:
        TypeError: If `data` is not a mapping.
        OSError: If the file cannot be written.
        yaml.YAMLError: If serialization fails.
    """
    if not isinstance(data, Mapping):
        raise TypeError("`data` must be a mapping (e.g., dict).")

    yaml_path = Path(output_file)
    yaml_path.parent.mkdir(parents=True, exist_ok=True)

    with yaml_path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(
            data,
            fh,
            allow_unicode=True,
            sort_keys=False,
            indent=2,
        )


def write_token(token: str) -> None:
    """
    Write a token to `general.ini` under the `DEFAULT` section.

    Args:
        token: Token value to store.

    Raises:
        ValueError: If `token` is empty or whitespace.
        OSError: If the file cannot be written.
    """
    if not isinstance(token, str) or not token.strip():
        raise ValueError("`token` must be a non-empty string.")

    file_path = ROOT / "general.ini"
    config = configparser.ConfigParser()
    # Ensure DEFAULT section exists
    if "DEFAULT" not in config:
        config["DEFAULT"] = {}
    config["DEFAULT"]["token"] = token

    with file_path.open("w", encoding="utf-8") as fp:
        config.write(fp)


def load_yaml(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a YAML file and return its contents as a dictionary.

    Args:
        file_path: Path to the YAML file.

    Returns:
        A dictionary with the parsed YAML contents. Empty file yields {}.

    Raises:
        FileNotFoundError: If the file does not exist.
        OSError: If the file cannot be read.
        yaml.YAMLError: If parsing fails.
        TypeError: If the result is not a mapping.
    """
    path = Path(file_path)

    with path.open(encoding="utf-8") as fh:
        loaded = yaml.safe_load(fh)  # may return None for empty YAML

    if loaded is None:
        return {}

    if not isinstance(loaded, dict):
        raise TypeError(f"YAML content must be a mapping, got: {type(loaded).__name__}")

    return loaded
