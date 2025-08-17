"""
Configuration bootstrap module.

Responsibilities:
- Resolve project paths and read the GitHub token from `config/settings/general.ini`.
- Provide a helper to load typed configs using a YAML payload and a generated Pydantic schema.
- Expose `repositories_meta` loaded (or generated on demand) via `api.metadata.get_user_repositories`.

Notes:
- Business logic is preserved: on ImportError/FileNotFoundError the executor is called,
  and the load is retried once more (total attempts = 2). If both attempts fail, `None` is returned.
"""

import configparser
import logging
from pathlib import Path
from typing import Any, Callable, Optional

from config.schemas.generator import load_schema
from config.settings.generator import load_yaml, write_token

# Project root (two levels up from this file: <project>/config/__init__.py -> <project>)
PROJECT_ROOT: Path = Path(__file__).parent.parent

# Paths to settings and schemas
SETTINGS_DIR: Path = PROJECT_ROOT / "config" / "settings"
SCHEMAS_DIR: Path = PROJECT_ROOT / "config" / "schemas"
GENERAL_INI: Path = SETTINGS_DIR / "general.ini"

logger = logging.getLogger(__name__)

# Read token eagerly so `config.token` is available to other modules.
_config = configparser.ConfigParser()
_config.read(GENERAL_INI, encoding="utf-8")
try:
    token: str = _config["DEFAULT"]["token"]
except KeyError as exc:
    token_input = input("GitHub token: ")
    token: str = token_input.replace("GitHub token: ", "").strip()
    write_token(token=token)


def _load_common_config(
    yaml_path: str | Path,
    schema_path: str | Path,
    executor: Callable[[], Any],
) -> Optional[Any]:
    """
    Load a config object by:
      1) reading YAML data,
      2) importing a generated Pydantic schema class named "Model",
      3) instantiating and returning the class with the YAML payload.

    If the schema or YAML is missing (ImportError/FileNotFoundError), run `executor()`
    to (re)generate the artifacts and retry once more. Any other exception is propagated.

    Args:
        yaml_path: Path to a YAML file with data.
        schema_path: Path to a Python module file that defines class "Model".
        executor: A callable used to (re)generate schema/data when missing.

    Returns:
        An instance of the loaded schema class, or None if both attempts fail.
    """
    MAX_ATTEMPTS = 2
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            data = load_yaml(file_path=yaml_path)
            schema_cls = load_schema(module_path=schema_path, class_name="Model")
            return schema_cls(**data)
        except (ImportError, FileNotFoundError) as err:
            logger.info(
                "Schema or YAML not found (attempt %d/%d). Executing recovery: %s",
                attempt,
                MAX_ATTEMPTS,
                getattr(executor, "__name__", str(executor)),
            )
            executor()
        except Exception:
            # Preserve original behavior: propagate any non-recoverable error.
            raise
    return None


# Lazily import to avoid cycles during module import.
from api import metadata  # noqa: E402
repositories_meta  = _load_common_config(
    yaml_path=SETTINGS_DIR / "repositories_meta.yaml",
    schema_path=SCHEMAS_DIR / "repositories_meta.py",
    executor=metadata.get_user_repositories,
)
from config.schemas.repositories_meta import Model
repositories_meta: Model

__all__ = [
    "PROJECT_ROOT",
    "SETTINGS_DIR",
    "SCHEMAS_DIR",
    "GENERAL_INI",
    "token",
    "repositories_meta",
]
