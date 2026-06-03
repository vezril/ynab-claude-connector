"""Tests for the YNAB MCP tools (tasks 5.1, 5.3)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import httpx
import pytest

from ynab_claude_connector.ynab import tools
from ynab_claude_connector.ynab.client import YnabClient
from ynab_claude_connector.ynab.errors import YnabAuthError

BUDGETS_PAYLOAD = {"data": {"budgets": [{"id": "b1", "name": "B"}]}}
ACCOUNTS_PAYLOAD = {
    "data": {
        "accounts": [
            {
                "id": "a1",
                "name": "Checking",
                "type": "checking",
                "on_budget": True,
                "closed": False,
                "balance": 500,
            }
        ]
    }
}


def _patch_client(
    monkeypatch: pytest.MonkeyPatch,
    handler: Callable[[httpx.Request], httpx.Response],
) -> dict[str, str]:
    captured: dict[str, str] = {}

    def recording_handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        return handler(request)

    def fake_client_from_env(config: object) -> YnabClient:
        http = httpx.AsyncClient(
            transport=httpx.MockTransport(recording_handler),
            base_url="https://api.ynab.com/v1/",
            headers={"Authorization": "Bearer test-token"},
        )
        return YnabClient(http)

    monkeypatch.setattr(tools, "client_from_env", fake_client_from_env)
    return captured


def test_list_budgets_tool_returns_budgets(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_client(monkeypatch, lambda r: httpx.Response(200, json=BUDGETS_PAYLOAD))
    budgets = asyncio.run(tools.list_budgets())
    assert [b.id for b in budgets] == ["b1"]


def test_list_accounts_tool_defaults_to_default_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _patch_client(
        monkeypatch, lambda r: httpx.Response(200, json=ACCOUNTS_PAYLOAD)
    )
    accounts = asyncio.run(tools.list_accounts())
    assert accounts[0].balance == 500
    assert captured["path"] == "/v1/budgets/default/accounts"


def test_list_categories_tool_defaults_to_default_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "data": {
            "category_groups": [
                {
                    "id": "g1",
                    "name": "Bills",
                    "categories": [
                        {
                            "id": "c1",
                            "name": "Rent",
                            "category_group_id": "g1",
                            "budgeted": 1,
                            "activity": 0,
                            "balance": 1,
                        }
                    ],
                }
            ]
        }
    }
    captured = _patch_client(monkeypatch, lambda r: httpx.Response(200, json=payload))
    categories = asyncio.run(tools.list_categories())
    assert categories[0].name == "Rent"
    assert captured["path"] == "/v1/budgets/default/categories"


def test_list_transactions_tool_uses_explicit_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "data": {
            "transactions": [
                {
                    "id": "t1",
                    "date": "2026-06-01",
                    "amount": -100,
                    "cleared": "cleared",
                    "approved": True,
                    "account_id": "a1",
                }
            ]
        }
    }
    captured = _patch_client(monkeypatch, lambda r: httpx.Response(200, json=payload))
    transactions = asyncio.run(tools.list_transactions("budget-x"))
    assert transactions[0].id == "t1"
    assert captured["path"] == "/v1/budgets/budget-x/transactions"


def test_get_user_tool_returns_user_id(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _patch_client(
        monkeypatch,
        lambda r: httpx.Response(200, json={"data": {"user": {"id": "u-9"}}}),
    )
    user = asyncio.run(tools.get_user())
    assert user.id == "u-9"
    assert captured["path"] == "/v1/user"


def test_get_user_without_token_raises_auth_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("YNAB_TOKEN", raising=False)
    with pytest.raises(YnabAuthError, match="YNAB_TOKEN"):
        asyncio.run(tools.get_user())


def test_tools_without_token_raise_auth_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # No monkeypatch of client_from_env: use the real one with no token.
    monkeypatch.delenv("YNAB_TOKEN", raising=False)
    with pytest.raises(YnabAuthError, match="YNAB_TOKEN"):
        asyncio.run(tools.list_budgets())
