"""Tests for the YNAB MCP tools (tasks 5.1, 5.3)."""

from __future__ import annotations

import asyncio
from collections.abc import Callable

import httpx
import pytest

from ynab_claude_connector.ynab import tools
from ynab_claude_connector.ynab.client import YnabClient
from ynab_claude_connector.ynab.errors import YnabAuthError

PLANS_PAYLOAD = {"data": {"plans": [{"id": "b1", "name": "B"}]}}
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


def test_list_plans_tool_returns_budgets(monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_client(monkeypatch, lambda r: httpx.Response(200, json=PLANS_PAYLOAD))
    budgets = asyncio.run(tools.list_plans())
    assert [b.id for b in budgets] == ["b1"]


def test_list_accounts_tool_defaults_to_default_alias(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured = _patch_client(
        monkeypatch, lambda r: httpx.Response(200, json=ACCOUNTS_PAYLOAD)
    )
    accounts = asyncio.run(tools.list_accounts())
    assert accounts[0].balance == 500
    assert captured["path"] == "/v1/plans/last-used/accounts"


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
    assert captured["path"] == "/v1/plans/last-used/categories"


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
    assert captured["path"] == "/v1/plans/budget-x/transactions"


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


def test_get_plan_tool_returns_summary(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "data": {
            "plan": {
                "id": "p1",
                "name": "Plan One",
                "accounts": [{"id": "a1"}, {"id": "a2"}],
                "categories": [{"id": "c1"}],
            },
            "server_knowledge": 1,
        }
    }
    captured = _patch_client(monkeypatch, lambda r: httpx.Response(200, json=payload))
    summary = asyncio.run(tools.get_plan())
    assert summary.accounts_count == 2
    assert summary.categories_count == 1
    assert captured["path"] == "/v1/plans/last-used"


def test_get_plan_settings_tool_returns_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        "data": {
            "settings": {
                "date_format": {"format": "MM/DD/YYYY"},
                "currency_format": None,
            }
        }
    }
    captured = _patch_client(monkeypatch, lambda r: httpx.Response(200, json=payload))
    settings = asyncio.run(tools.get_plan_settings("p9"))
    assert settings.date_format is not None
    assert settings.date_format.format == "MM/DD/YYYY"
    assert captured["path"] == "/v1/plans/p9/settings"


def test_get_plan_settings_without_token_raises(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("YNAB_TOKEN", raising=False)
    with pytest.raises(YnabAuthError, match="YNAB_TOKEN"):
        asyncio.run(tools.get_plan_settings())


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


def test_list_payees_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _patch_client(
        monkeypatch,
        lambda r: httpx.Response(
            200, json={"data": {"payees": [{"id": "py1", "name": "Market"}]}}
        ),
    )
    payees = asyncio.run(tools.list_payees())
    assert payees[0].name == "Market"
    assert captured["path"] == "/v1/plans/last-used/payees"


def test_get_payee_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _patch_client(
        monkeypatch,
        lambda r: httpx.Response(
            200, json={"data": {"payee": {"id": "py1", "name": "Market"}}}
        ),
    )
    payee = asyncio.run(tools.get_payee("py1"))
    assert payee.id == "py1"
    assert captured["path"] == "/v1/plans/last-used/payees/py1"


def test_payee_tools_without_token_raise(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("YNAB_TOKEN", raising=False)
    with pytest.raises(YnabAuthError, match="YNAB_TOKEN"):
        asyncio.run(tools.list_payees())
    with pytest.raises(YnabAuthError, match="YNAB_TOKEN"):
        asyncio.run(tools.get_payee("py1"))


def test_get_category_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _patch_client(
        monkeypatch, lambda r: httpx.Response(200, json=_CATEGORY_RESPONSE)
    )
    category = asyncio.run(tools.get_category("c1"))
    assert category.name == "Rent"
    assert captured["path"] == "/v1/plans/last-used/categories/c1"


def test_get_month_category_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = _patch_client(
        monkeypatch, lambda r: httpx.Response(200, json=_CATEGORY_RESPONSE)
    )
    category = asyncio.run(tools.get_month_category("current", "c1"))
    assert category.id == "c1"
    assert captured["path"] == "/v1/plans/last-used/months/current/categories/c1"


def test_category_tools_without_token_raise(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("YNAB_TOKEN", raising=False)
    with pytest.raises(YnabAuthError, match="YNAB_TOKEN"):
        asyncio.run(tools.get_category("c1"))
    with pytest.raises(YnabAuthError, match="YNAB_TOKEN"):
        asyncio.run(tools.get_month_category("current", "c1"))


def test_tools_without_token_raise_auth_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # No monkeypatch of client_from_env: use the real one with no token.
    monkeypatch.delenv("YNAB_TOKEN", raising=False)
    with pytest.raises(YnabAuthError, match="YNAB_TOKEN"):
        asyncio.run(tools.list_plans())
