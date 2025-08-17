"""
GitHub API package utilities.

This module provides:
- `get_headers()` — a safe builder for GitHub REST API headers.
- `HEADERS` — a ready-to-use headers mapping (raises if token is missing).
- Re-export of `.metadata` for convenience.

It expects a `config.token` to hold a GitHub personal access token.
"""

from __future__ import annotations

import logging
from typing import Dict, Mapping, Optional

import config  # expects `token` attribute

# GitHub REST API version pin for consistent behavior across requests.
API_VERSION: str = "2022-11-28"
_ACCEPT_HEADER: str = "application/vnd.github+json"


def get_headers(token: Optional[str] = None) -> Dict[str, str]:
    """
    Build HTTP headers for GitHub REST API calls.

    Args:
        token: Personal access token. If None, falls back to `config.token`.

    Returns:
        A dictionary of HTTP headers suitable for GitHub requests.

    Raises:
        RuntimeError: If a token is missing or empty.
    """
    tok = token if token is not None else getattr(config, "token", None)
    if not isinstance(tok, str) or not tok.strip():
        raise RuntimeError(
            "GitHub token is not configured. Provide `config.token` or pass `token` to get_headers()."
        )

    return {
        "Accept": _ACCEPT_HEADER,
        "Authorization": f"Bearer {tok}",
        "X-GitHub-Api-Version": API_VERSION,
    }


# Backward-compatible constant. Will fail fast with a clear error if no token is configured.
HEADERS: Mapping[str, str] = get_headers()

# Re-export the submodule for convenience imports like: `from api import metadata`
from . import metadata as metadata  # noqa: E402

__all__ = ["API_VERSION", "get_headers", "HEADERS", "metadata"]
