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

PLANS_PAYLOAD = {
    "data": {"plans": [{"id": "b1", "name": "B"}, {"id": "b2", "name": "C"}]}
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


def test_list_plans_sends_bearer_and_parses() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["auth"] = request.headers.get("authorization", "")
        return httpx.Response(200, json=PLANS_PAYLOAD)

    async def run() -> tuple[str, ...]:
        async with _client(handler) as client:
            return tuple(b.id for b in await client.list_plans())

    assert asyncio.run(run()) == ("b1", "b2")
    assert captured["auth"] == "Bearer test-token"
    assert captured["path"] == "/v1/plans"


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
    assert captured["path"] == "/v1/plans/last-used/accounts"


def test_get_plan_returns_summary_default_alias() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["auth"] = request.headers.get("authorization", "")
        return httpx.Response(
            200,
            json={
                "data": {
                    "plan": {
                        "id": "p1",
                        "name": "Plan One",
                        "accounts": [{"id": "a1"}],
                        "transactions": [{"id": "t1"}, {"id": "t2"}],
                    },
                    "server_knowledge": 1,
                }
            },
        )

    async def run() -> tuple[int, int]:
        async with _client(handler) as client:
            summary = await client.get_plan()
            return summary.accounts_count, summary.transactions_count

    assert asyncio.run(run()) == (1, 2)
    assert captured["auth"] == "Bearer test-token"
    assert captured["path"] == "/v1/plans/last-used"


def test_get_plan_settings_returns_settings_default_alias() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        return httpx.Response(
            200,
            json={
                "data": {
                    "settings": {
                        "date_format": {"format": "YYYY-MM-DD"},
                        "currency_format": None,
                    }
                }
            },
        )

    async def run() -> str | None:
        async with _client(handler) as client:
            settings = await client.get_plan_settings()
            return settings.date_format.format if settings.date_format else None

    assert asyncio.run(run()) == "YYYY-MM-DD"
    assert captured["path"] == "/v1/plans/last-used/settings"


_CATEGORY_RESPONSE = {
    "data": {
        "category": {
            "id": "c1",
            "name": "Rent",
            "category_group_id": "g1",
            "budgeted": 100,
            "activity": -50,
            "balance": 50,
        }
    }
}


def test_payee_location_paths() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["auth"] = request.headers.get("authorization", "")
        if request.url.path.endswith("/payee_locations/pl1"):
            return httpx.Response(
                200,
                json={"data": {"payee_location": {"id": "pl1", "payee_id": "py1"}}},
            )
        return httpx.Response(
            200,
            json={"data": {"payee_locations": [{"id": "pl1", "payee_id": "py1"}]}},
        )

    async def run_list() -> int:
        async with _client(handler) as client:
            return len(await client.list_payee_locations())

    assert asyncio.run(run_list()) == 1
    assert captured["auth"] == "Bearer test-token"
    assert captured["path"] == "/v1/plans/last-used/payee_locations"

    async def run_get() -> str:
        async with _client(handler) as client:
            return (await client.get_payee_location("pl1")).payee_id

    assert asyncio.run(run_get()) == "py1"
    assert captured["path"] == "/v1/plans/last-used/payee_locations/pl1"

    async def run_for_payee() -> int:
        async with _client(handler) as client:
            return len(await client.list_payee_locations_for_payee("py1"))

    assert asyncio.run(run_for_payee()) == 1
    assert captured["path"] == "/v1/plans/last-used/payees/py1/payee_locations"


def test_get_payee_location_404() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": {"detail": "nope"}})

    async def run() -> None:
        async with _client(handler) as client:
            await client.get_payee_location("missing")

    with pytest.raises(YnabApiError):
        asyncio.run(run())


def test_list_payees_path_and_parse() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["auth"] = request.headers.get("authorization", "")
        return httpx.Response(
            200,
            json={"data": {"payees": [{"id": "py1", "name": "Market"}]}},
        )

    async def run() -> str:
        async with _client(handler) as client:
            return (await client.list_payees())[0].name

    assert asyncio.run(run()) == "Market"
    assert captured["auth"] == "Bearer test-token"
    assert captured["path"] == "/v1/plans/last-used/payees"


def test_get_payee_path_and_404() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        return httpx.Response(200, json={"data": {"payee": {"id": "py1", "name": "M"}}})

    async def run() -> str:
        async with _client(handler) as client:
            return (await client.get_payee("py1")).id

    assert asyncio.run(run()) == "py1"
    assert captured["path"] == "/v1/plans/last-used/payees/py1"

    def handler_404(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": {"detail": "nope"}})

    async def run_404() -> None:
        async with _client(handler_404) as client:
            await client.get_payee("missing")

    with pytest.raises(YnabApiError):
        asyncio.run(run_404())


def test_get_category_path_and_parse() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["auth"] = request.headers.get("authorization", "")
        return httpx.Response(200, json=_CATEGORY_RESPONSE)

    async def run() -> str:
        async with _client(handler) as client:
            return (await client.get_category("c1")).name

    assert asyncio.run(run()) == "Rent"
    assert captured["auth"] == "Bearer test-token"
    assert captured["path"] == "/v1/plans/last-used/categories/c1"


def test_get_month_category_path() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        return httpx.Response(200, json=_CATEGORY_RESPONSE)

    async def run_iso() -> None:
        async with _client(handler) as client:
            await client.get_month_category("2026-06-01", "c1")

    asyncio.run(run_iso())
    assert captured["path"] == "/v1/plans/last-used/months/2026-06-01/categories/c1"

    async def run_current() -> None:
        async with _client(handler) as client:
            await client.get_month_category("current", "c1")

    asyncio.run(run_current())
    assert captured["path"] == "/v1/plans/last-used/months/current/categories/c1"


def test_get_category_404_maps_to_api_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"error": {"detail": "not found"}})

    async def run() -> None:
        async with _client(handler) as client:
            await client.get_category("missing")

    with pytest.raises(YnabApiError):
        asyncio.run(run())


def test_explicit_plan_id_is_used() -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        return httpx.Response(200, json={"data": {"transactions": []}})

    async def run() -> None:
        async with _client(handler) as client:
            await client.list_transactions("my-budget")

    asyncio.run(run())
    assert captured["path"] == "/v1/plans/my-budget/transactions"


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
            await client.list_plans()

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
