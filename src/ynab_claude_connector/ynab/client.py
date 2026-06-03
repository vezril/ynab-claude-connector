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
    Category,
    Payee,
    Plan,
    PlanDetailSummary,
    PlanSettings,
    Transaction,
    User,
    parse_accounts,
    parse_categories,
    parse_category,
    parse_payee,
    parse_payees,
    parse_plan_detail_summary,
    parse_plan_settings,
    parse_plans,
    parse_transactions,
    parse_user,
)

_DEFAULT_PLAN: str = "last-used"


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

    async def get_user(self) -> User:
        return parse_user(await self._get("user"))

    async def list_plans(self) -> tuple[Plan, ...]:
        return parse_plans(await self._get("plans"))

    async def get_plan(self, plan_id: str = _DEFAULT_PLAN) -> PlanDetailSummary:
        return parse_plan_detail_summary(await self._get(f"plans/{plan_id}"))

    async def get_plan_settings(self, plan_id: str = _DEFAULT_PLAN) -> PlanSettings:
        return parse_plan_settings(await self._get(f"plans/{plan_id}/settings"))

    async def list_accounts(self, plan_id: str = _DEFAULT_PLAN) -> tuple[Account, ...]:
        return parse_accounts(await self._get(f"plans/{plan_id}/accounts"))

    async def list_categories(
        self, plan_id: str = _DEFAULT_PLAN
    ) -> tuple[Category, ...]:
        return parse_categories(await self._get(f"plans/{plan_id}/categories"))

    async def get_category(
        self, category_id: str, plan_id: str = _DEFAULT_PLAN
    ) -> Category:
        return parse_category(
            await self._get(f"plans/{plan_id}/categories/{category_id}")
        )

    async def get_month_category(
        self, month: str, category_id: str, plan_id: str = _DEFAULT_PLAN
    ) -> Category:
        return parse_category(
            await self._get(f"plans/{plan_id}/months/{month}/categories/{category_id}")
        )

    async def list_payees(self, plan_id: str = _DEFAULT_PLAN) -> tuple[Payee, ...]:
        return parse_payees(await self._get(f"plans/{plan_id}/payees"))

    async def get_payee(self, payee_id: str, plan_id: str = _DEFAULT_PLAN) -> Payee:
        return parse_payee(await self._get(f"plans/{plan_id}/payees/{payee_id}"))

    async def list_transactions(
        self, plan_id: str = _DEFAULT_PLAN
    ) -> tuple[Transaction, ...]:
        return parse_transactions(await self._get(f"plans/{plan_id}/transactions"))


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
