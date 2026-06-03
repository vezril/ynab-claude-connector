"""Async YNAB API client.

All ``httpx`` usage is confined to this module. The client wraps an injected
``httpx.AsyncClient`` (so tests can supply a ``MockTransport``); pure parsing
and error mapping live in :mod:`models` and :mod:`errors`. Each request GETs a
relative path, raises a typed error on non-2xx, and otherwise parses the body.
"""

from __future__ import annotations

from types import TracebackType
from typing import Self

import httpx

from ynab_claude_connector.config import ServerConfig
from ynab_claude_connector.ynab.errors import YnabAuthError, error_from_response
from ynab_claude_connector.ynab.models import (
    Account,
    Budget,
    Category,
    Transaction,
    parse_accounts,
    parse_budgets,
    parse_categories,
    parse_transactions,
)

_DEFAULT_BUDGET: str = "default"


class YnabClient:
    """Async client over the YNAB API, wrapping an ``httpx.AsyncClient``."""

    def __init__(self, http: httpx.AsyncClient) -> None:
        self.http = http

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self.http.aclose()

    async def _get(self, path: str) -> dict[str, object]:
        response = await self.http.get(path)
        if response.status_code >= 400:
            body = _safe_json(response)
            raise error_from_response(response.status_code, body)
        return _safe_json(response)

    async def list_budgets(self) -> tuple[Budget, ...]:
        return parse_budgets(await self._get("budgets"))

    async def list_accounts(
        self, budget_id: str = _DEFAULT_BUDGET
    ) -> tuple[Account, ...]:
        return parse_accounts(await self._get(f"budgets/{budget_id}/accounts"))

    async def list_categories(
        self, budget_id: str = _DEFAULT_BUDGET
    ) -> tuple[Category, ...]:
        return parse_categories(await self._get(f"budgets/{budget_id}/categories"))

    async def list_transactions(
        self, budget_id: str = _DEFAULT_BUDGET
    ) -> tuple[Transaction, ...]:
        return parse_transactions(await self._get(f"budgets/{budget_id}/transactions"))


def _safe_json(response: httpx.Response) -> dict[str, object]:
    try:
        body = response.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


def build_async_http_client(config: ServerConfig) -> httpx.AsyncClient:
    """Build an ``httpx.AsyncClient`` with the YNAB base URL and bearer auth."""
    if not config.ynab_token:
        raise YnabAuthError(
            "No YNAB token configured. Set the YNAB_TOKEN environment variable "
            "to a YNAB Personal Access Token."
        )
    base_url = config.ynab_api_base_url.rstrip("/") + "/"
    return httpx.AsyncClient(
        base_url=base_url,
        headers={"Authorization": f"Bearer {config.ynab_token}"},
        timeout=httpx.Timeout(30.0),
    )


def client_from_env(config: ServerConfig) -> YnabClient:
    """Build a :class:`YnabClient` from configuration (requires a token)."""
    return YnabClient(build_async_http_client(config))
