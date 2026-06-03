"""Tests for YNAB typed models and pure parsers (tasks 2.1, 2.3)."""

from __future__ import annotations

from ynab_claude_connector.ynab.models import (
    parse_accounts,
    parse_budgets,
    parse_categories,
    parse_transactions,
)

BUDGETS_PAYLOAD = {
    "data": {
        "budgets": [
            {"id": "b1", "name": "My Budget"},
            {"id": "b2", "name": "Side Budget"},
        ]
    }
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
                "balance": 123450,
            }
        ],
        "server_knowledge": 42,
    }
}

CATEGORIES_PAYLOAD = {
    "data": {
        "category_groups": [
            {
                "id": "g1",
                "name": "Monthly Bills",
                "categories": [
                    {
                        "id": "c1",
                        "name": "Rent",
                        "category_group_id": "g1",
                        "budgeted": 1000000,
                        "activity": -1000000,
                        "balance": 0,
                    }
                ],
            }
        ]
    }
}

TRANSACTIONS_PAYLOAD = {
    "data": {
        "transactions": [
            {
                "id": "t1",
                "date": "2026-06-01",
                "amount": -54320,
                "memo": "Groceries",
                "cleared": "cleared",
                "approved": True,
                "payee_name": "Market",
                "category_id": "c1",
                "account_id": "a1",
            }
        ]
    }
}


def test_parse_budgets() -> None:
    budgets = parse_budgets(BUDGETS_PAYLOAD)
    assert [(b.id, b.name) for b in budgets] == [
        ("b1", "My Budget"),
        ("b2", "Side Budget"),
    ]


def test_parse_accounts_keeps_milliunits() -> None:
    accounts = parse_accounts(ACCOUNTS_PAYLOAD)
    assert len(accounts) == 1
    account = accounts[0]
    assert account.id == "a1"
    assert account.name == "Checking"
    assert account.type == "checking"
    assert account.on_budget is True
    assert account.closed is False
    assert account.balance == 123450  # milliunits, unchanged


def test_parse_categories_flattens_groups() -> None:
    categories = parse_categories(CATEGORIES_PAYLOAD)
    assert len(categories) == 1
    category = categories[0]
    assert category.id == "c1"
    assert category.name == "Rent"
    assert category.category_group_id == "g1"
    assert category.budgeted == 1000000
    assert category.activity == -1000000
    assert category.balance == 0


def test_parse_transactions() -> None:
    transactions = parse_transactions(TRANSACTIONS_PAYLOAD)
    assert len(transactions) == 1
    txn = transactions[0]
    assert txn.id == "t1"
    assert txn.date == "2026-06-01"
    assert txn.amount == -54320
    assert txn.memo == "Groceries"
    assert txn.payee_name == "Market"
    assert txn.category_id == "c1"
    assert txn.account_id == "a1"


def test_parse_empty_lists_yield_empty_tuples() -> None:
    assert parse_budgets({"data": {"budgets": []}}) == ()
    assert parse_accounts({"data": {"accounts": []}}) == ()
    assert parse_categories({"data": {"category_groups": []}}) == ()
    assert parse_transactions({"data": {"transactions": []}}) == ()


def test_parse_missing_optional_fields_is_safe() -> None:
    # Transaction with optional payee/memo/category absent.
    payload = {
        "data": {
            "transactions": [
                {
                    "id": "t9",
                    "date": "2026-06-02",
                    "amount": 1000,
                    "cleared": "uncleared",
                    "approved": False,
                    "account_id": "a1",
                }
            ]
        }
    }
    txn = parse_transactions(payload)[0]
    assert txn.memo is None
    assert txn.payee_name is None
    assert txn.category_id is None
