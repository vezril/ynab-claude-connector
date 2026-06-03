"""Tests for the async YNAB client via httpx MockTransport (tasks 4.1, 4.3, 4.5)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import httpx
import pytest

from ynab_claude_connector.config import from_env
from ynab_claude_connector.ynab.client import YnabClient, client_from_env
from ynab_claude_connector.ynab.errors import (
    YnabApiError,
    YnabAuthError,
    YnabRateLimitError,
)

BUDGETS_PAYLOAD = {
    "data": {"budgets": [{"id": "b1", "name": "B"}, {"id": "b2", "name": "C"}]}
}
ACCOUNTS_PAYLOAD = {
    "data": {
        "accounts": [
            {
                "id": "a1",
                "name": "Checking",
                "type": "checking",
                "on_budget": True,
                "closed": False,
                "balance": 100,
            }
        ]
    }
}


def _client(handler: Callable[[httpx.Request], httpx.Response]) -> YnabClient:
    http = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        base_url="https://api.ynab.com/v1/",
        headers={"Authorization": "Bearer test-token"},
    )
    return YnabClient(http)


def test_list_budgets_sends_bearer_and_parses() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["auth"] = request.headers.get("authorization", "")
        return httpx.Response(200, json=BUDGETS_PAYLOAD)

    async def run() -> tuple[str, ...]:
        async with _client(handler) as client:
            return tuple(b.id for b in await client.list_budgets())

    assert asyncio.run(run()) == ("b1", "b2")
    assert captured["auth"] == "Bearer test-token"
    assert captured["path"] == "/v1/budgets"


def test_get_user_sends_bearer_and_parses() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["auth"] = request.headers.get("authorization", "")
        return httpx.Response(200, json={"data": {"user": {"id": "u-123"}}})

    async def run() -> str:
        async with _client(handler) as client:
            return (await client.get_user()).id

    assert asyncio.run(run()) == "u-123"
    assert captured["auth"] == "Bearer test-token"
    assert captured["path"] == "/v1/user"


def test_budget_scoped_defaults_to_default_alias() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        return httpx.Response(200, json=ACCOUNTS_PAYLOAD)

    async def run() -> int:
        async with _client(handler) as client:
            accounts = await client.list_accounts()
            return accounts[0].balance

    assert asyncio.run(run()) == 100
    assert captured["path"] == "/v1/budgets/default/accounts"


def test_explicit_budget_id_is_used() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        return httpx.Response(200, json={"data": {"transactions": []}})

    async def run() -> None:
        async with _client(handler) as client:
            await client.list_transactions("my-budget")

    asyncio.run(run())
    assert captured["path"] == "/v1/budgets/my-budget/transactions"


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, YnabAuthError),
        (429, YnabRateLimitError),
        (500, YnabApiError),
    ],
)
def test_error_statuses_map_to_typed_errors(
    status: int, expected: type[Exception]
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json={"error": {"detail": "nope"}})

    async def run() -> None:
        async with _client(handler) as client:
            await client.list_budgets()

    with pytest.raises(expected):
        asyncio.run(run())


def test_error_with_non_json_body_maps_to_api_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="<html>down</html>")

    async def run() -> None:
        async with _client(handler) as client:
            await client.list_categories()

    with pytest.raises(YnabApiError):
        asyncio.run(run())


def test_client_from_env_requires_token() -> None:
    with pytest.raises(YnabAuthError, match="YNAB_TOKEN"):
        client_from_env(from_env({}))


def test_client_from_env_sets_auth_header_and_base_url() -> None:
    config = from_env(
        {"YNAB_TOKEN": "abc123", "YNAB_API_BASE_URL": "https://example.test/v1"}
    )
    client = client_from_env(config)
    try:
        assert client.http.headers["authorization"] == "Bearer abc123"
        assert str(client.http.base_url).rstrip("/") == "https://example.test/v1"
    finally:
        asyncio.run(client.aclose())
