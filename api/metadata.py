"""
Fetch and persist GitHub metadata.

Currently exposes:
- `get_user_repositories()` — retrieves all repositories accessible to the
  authenticated user, persists a YAML snapshot and a generated Pydantic
  schema, and returns a normalized dict grouped by owner.
"""

import logging
from typing import Any, Dict, List, Mapping, Optional

import requests
from requests import Session
from requests.exceptions import HTTPError, RequestException, Timeout

from config.schemas.generator import dict_to_pydantic_model
from config.settings.generator import dict_to_yaml

logger = logging.getLogger(__name__)

GITHUB_REPOS_URL = "https://api.github.com/user/repos"
REQUEST_TIMEOUT = 30  # seconds
PER_PAGE = 100


def _fetch_all_user_repos(
    session: Optional[Session],
    headers: Mapping[str, str],
) -> List[Dict[str, Any]]:
    """
    Fetch all repositories for the authenticated user with pagination.

    Args:
        session: Optional `requests.Session` to reuse connections.
        headers: HTTP headers including Authorization.

    Returns:
        A list of raw repository dicts returned by the GitHub API.

    Raises:
        HTTPError / RequestException: For network/HTTP errors.
        ValueError: If the response payload is not the expected list.
    """
    sess = session or requests.Session()
    page = 1
    repos: List[Dict[str, Any]] = []

    while True:
        params = {"per_page": PER_PAGE, "page": page, "sort": "full_name", "direction": "asc"}
        try:
            resp = sess.get(
                GITHUB_REPOS_URL,
                headers=headers,
                params=params,
                timeout=REQUEST_TIMEOUT,
            )
            resp.raise_for_status()
        except (Timeout, HTTPError) as exc:
            logger.error("Failed to fetch repositories (page %s): %s", page, exc)
            raise
        except RequestException as exc:
            logger.error("Network error while fetching repositories (page %s): %s", page, exc)
            raise

        batch = resp.json()
        if not batch:
            break

        if not isinstance(batch, list):
            logger.error("Unexpected response format: %r", batch)
            raise ValueError("GitHub API returned an unexpected payload for /user/repos")

        repos.extend(batch)
        page += 1

        # If we received less than PER_PAGE items, assume it's the last page.
        if len(batch) < PER_PAGE:
            break

    return repos


def _normalize_repos(repos: List[Dict[str, Any]]) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    Normalize repositories data into a compact owner->repo mapping.

    Returns:
        Dict[owner][repo_name] -> {"id": int, "permissions": {...}}
    """
    result: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for repo in repos:
        owner = repo.get("owner", {}).get("login")
        name = repo.get("name")
        if not owner or not name:
            logger.debug("Skipping repo with missing owner/name: %r", repo)
            continue

        bucket = result.setdefault(owner, {})
        bucket[name] = {
            "id": repo.get("id"),
            "permissions": repo.get("permissions", {}),
        }
    return result


def get_user_repositories(session: Optional[Session] = None) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """
    List repositories that the authenticated user can access and persist metadata.

    Steps:
    1) Fetch all repositories (handles pagination).
    2) Save YAML snapshot to `config/settings/repositories_meta.yaml`.
    3) Generate Pydantic model file at `config/schemas/repositories_meta.py`.

    Args:
        session: Optional `requests.Session` to reuse connections.

    Returns:
        Normalized mapping grouped by owner (see `_normalize_repos`).

    Raises:
        HTTPError / RequestException: For network/HTTP errors.
        ValueError: For unexpected API payloads.
        Any exception thrown by persistence helpers is propagated.
    """
    # Lazy imports to avoid circular imports on package init.
    from api import get_headers
    from config import ROOT

    headers = get_headers()

    repos = _fetch_all_user_repos(session=session, headers=headers)
    data = _normalize_repos(repos)

    yaml_path = ROOT / "config" / "settings" / "repositories_meta.yaml"
    schema_path = ROOT / "config" / "schemas" / "repositories_meta.py"

    # Persist the YAML snapshot
    dict_to_yaml(data, yaml_path)

    # Persist the Pydantic schema
    dict_to_pydantic_model(
        data=data,
        output_file=schema_path,
        class_name="Model",
    )

    return data


__all__ = ["get_user_repositories"]
