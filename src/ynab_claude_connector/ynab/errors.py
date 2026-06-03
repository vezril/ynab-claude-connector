"""YNAB error taxonomy and a pure status-to-error mapper.

Exceptions never carry the access token. ``error_from_response`` is pure: given
an HTTP status and the parsed JSON body, it returns the appropriate typed
exception (without raising), so every branch is unit-testable.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class YnabError(Exception):
    """Base class for all YNAB integration errors."""


class YnabAuthError(YnabError):
    """Authentication/authorization failure (missing token, 401, or 403)."""


class YnabRateLimitError(YnabError):
    """The YNAB request rate limit (200/hour per token) was exceeded (429)."""


class YnabApiError(YnabError):
    """Any other non-success YNAB API response."""

    def __init__(self, status: int, detail: str) -> None:
        self.status = status
        self.detail = detail
        super().__init__(f"YNAB API error (HTTP {status}): {detail}")


def _detail(body: Mapping[str, Any]) -> str:
    error = body.get("error")
    if isinstance(error, Mapping):
        return str(error.get("detail") or error.get("name") or "unknown error")
    return "unknown error"


def error_from_response(status: int, body: Mapping[str, Any]) -> YnabError:
    """Map an HTTP status + parsed body to a typed YNAB error (does not raise)."""
    if status in (401, 403):
        return YnabAuthError(
            f"YNAB authentication failed (HTTP {status}): {_detail(body)}"
        )
    if status == 429:
        return YnabRateLimitError(
            "YNAB rate limit exceeded (HTTP 429): "
            "up to 200 requests/hour per token are allowed."
        )
    return YnabApiError(status, _detail(body))
