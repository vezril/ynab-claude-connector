"""Tests for YNAB typed models and pure parsers (tasks 2.1, 2.3)."""

from __future__ import annotations

import pytest

from ynab_claude_connector.ynab.models import (
    parse_accounts,
    parse_categories,
    parse_category,
    parse_money_movement_groups,
    parse_money_movements,
    parse_month,
    parse_months,
    parse_payee,
    parse_payee_location,
    parse_payee_locations,
    parse_payees,
    parse_plan_detail_summary,
    parse_plan_settings,
    parse_plans,
    parse_scheduled_transaction,
    parse_scheduled_transactions,
    parse_transaction,
    parse_transactions,
    parse_user,
)

PLANS_PAYLOAD = {
    "data": {
        "plans": [
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


def test_parse_plans() -> None:
    budgets = parse_plans(PLANS_PAYLOAD)
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


def test_parse_payees() -> None:
    payees = parse_payees(
        {
            "data": {
                "payees": [
                    {
                        "id": "py1",
                        "name": "Market",
                        "transfer_account_id": None,
                        "deleted": False,
                    },
                    {
                        "id": "py2",
                        "name": "Transfer",
                        "transfer_account_id": "a9",
                        "deleted": False,
                    },
                ]
            }
        }
    )
    assert [(p.id, p.name, p.transfer_account_id) for p in payees] == [
        ("py1", "Market", None),
        ("py2", "Transfer", "a9"),
    ]


def test_parse_money_movements() -> None:
    movements = parse_money_movements(
        {
            "data": {
                "money_movements": [
                    {
                        "id": "mm1",
                        "month": "2026-06-01",
                        "moved_at": "2026-06-02T10:00:00Z",
                        "note": "reallocate",
                        "money_movement_group_id": "mmg1",
                        "performed_by_user_id": "u1",
                        "from_category_id": "c1",
                        "to_category_id": "c2",
                        "amount": -25000,
                    }
                ]
            }
        }
    )
    assert len(movements) == 1
    mv = movements[0]
    assert mv.id == "mm1"
    assert mv.month == "2026-06-01"
    assert mv.from_category_id == "c1"
    assert mv.to_category_id == "c2"
    assert mv.money_movement_group_id == "mmg1"
    assert mv.amount == -25000


def test_parse_money_movement_minimal() -> None:
    mv = parse_money_movements(
        {"data": {"money_movements": [{"id": "mm2", "amount": 100}]}}
    )[0]
    assert mv.id == "mm2"
    assert mv.amount == 100
    assert mv.month is None
    assert mv.note is None
    assert mv.from_category_id is None


def test_parse_money_movement_groups() -> None:
    groups = parse_money_movement_groups(
        {
            "data": {
                "money_movement_groups": [
                    {
                        "id": "mmg1",
                        "group_created_at": "2026-06-02T10:00:00Z",
                        "month": "2026-06-01",
                        "note": "june moves",
                        "performed_by_user_id": "u1",
                    }
                ]
            }
        }
    )
    assert len(groups) == 1
    g = groups[0]
    assert g.id == "mmg1"
    assert g.month == "2026-06-01"
    assert g.note == "june moves"
    assert g.performed_by_user_id == "u1"


def test_parse_money_movements_empty() -> None:
    assert parse_money_movements({"data": {"money_movements": []}}) == ()
    assert parse_money_movement_groups({"data": {"money_movement_groups": []}}) == ()


def test_parse_months() -> None:
    months = parse_months(
        {
            "data": {
                "months": [
                    {
                        "month": "2026-06-01",
                        "note": "June",
                        "income": 5000000,
                        "budgeted": 4000000,
                        "activity": -3500000,
                        "to_be_budgeted": 1000000,
                        "age_of_money": 30,
                        "deleted": False,
                    }
                ]
            }
        }
    )
    assert len(months) == 1
    m = months[0]
    assert m.month == "2026-06-01"
    assert m.note == "June"
    assert m.income == 5000000
    assert m.budgeted == 4000000
    assert m.activity == -3500000
    assert m.to_be_budgeted == 1000000
    assert m.age_of_money == 30
    assert m.deleted is False


def test_parse_month_single() -> None:
    m = parse_month(
        {
            "data": {
                "month": {
                    "month": "2026-06-01",
                    "income": 0,
                    "budgeted": 0,
                    "activity": 0,
                    "to_be_budgeted": 0,
                    "deleted": False,
                }
            }
        }
    )
    assert m.month == "2026-06-01"
    assert m.note is None
    assert m.age_of_money is None


def test_parse_months_empty() -> None:
    assert parse_months({"data": {"months": []}}) == ()


def test_parse_month_missing_raises() -> None:
    with pytest.raises((KeyError, TypeError)):
        parse_month({"data": {}})
    with pytest.raises((KeyError, TypeError)):
        parse_month({"data": {"month": {}}})


def test_parse_payee_locations() -> None:
    locations = parse_payee_locations(
        {
            "data": {
                "payee_locations": [
                    {
                        "id": "pl1",
                        "payee_id": "py1",
                        "latitude": "40.7128",
                        "longitude": "-74.0060",
                        "deleted": False,
                    }
                ]
            }
        }
    )
    assert len(locations) == 1
    loc = locations[0]
    assert loc.id == "pl1"
    assert loc.payee_id == "py1"
    assert loc.latitude == "40.7128"
    assert loc.longitude == "-74.0060"
    assert loc.deleted is False


def test_parse_payee_location_single() -> None:
    loc = parse_payee_location(
        {"data": {"payee_location": {"id": "pl1", "payee_id": "py1"}}}
    )
    assert loc.id == "pl1"
    assert loc.payee_id == "py1"
    assert loc.latitude is None
    assert loc.longitude is None
    assert loc.deleted is False


def test_parse_payee_locations_empty() -> None:
    assert parse_payee_locations({"data": {"payee_locations": []}}) == ()


def test_parse_payee_location_missing_fields_raises() -> None:
    with pytest.raises((KeyError, TypeError)):
        parse_payee_location({"data": {}})
    with pytest.raises((KeyError, TypeError)):
        parse_payee_location({"data": {"payee_location": {}}})


def test_parse_payee_single() -> None:
    payee = parse_payee(
        {"data": {"payee": {"id": "py1", "name": "Market", "deleted": True}}}
    )
    assert payee.id == "py1"
    assert payee.name == "Market"
    assert payee.transfer_account_id is None
    assert payee.deleted is True


def test_parse_payees_empty_and_partial() -> None:
    assert parse_payees({"data": {"payees": []}}) == ()
    payee = parse_payees({"data": {"payees": [{"id": "p", "name": "n"}]}})[0]
    assert payee.transfer_account_id is None
    assert payee.deleted is False


def test_parse_payee_missing_fields_raises() -> None:
    with pytest.raises((KeyError, TypeError)):
        parse_payee({"data": {}})
    with pytest.raises((KeyError, TypeError)):
        parse_payee({"data": {"payee": {}}})


def test_parse_category_single() -> None:
    category = parse_category(
        {
            "data": {
                "category": {
                    "id": "c1",
                    "name": "Rent",
                    "category_group_id": "g1",
                    "budgeted": 1000000,
                    "activity": -250000,
                    "balance": 750000,
                }
            }
        }
    )
    assert category.id == "c1"
    assert category.name == "Rent"
    assert category.category_group_id == "g1"
    assert category.budgeted == 1000000
    assert category.activity == -250000
    assert category.balance == 750000


def test_parse_category_missing_fields_raises() -> None:
    with pytest.raises((KeyError, TypeError)):
        parse_category({"data": {}})
    with pytest.raises((KeyError, TypeError)):
        parse_category({"data": {"category": {}}})


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


def test_parse_scheduled_transactions() -> None:
    sched = parse_scheduled_transactions(
        {
            "data": {
                "scheduled_transactions": [
                    {
                        "id": "st1",
                        "date_first": "2026-01-01",
                        "date_next": "2026-07-01",
                        "frequency": "monthly",
                        "amount": -120000,
                        "account_id": "a1",
                        "payee_id": "py1",
                        "category_id": "c1",
                        "memo": "Rent",
                        "deleted": False,
                    }
                ]
            }
        }
    )
    assert len(sched) == 1
    s = sched[0]
    assert s.id == "st1"
    assert s.date_first == "2026-01-01"
    assert s.date_next == "2026-07-01"
    assert s.frequency == "monthly"
    assert s.amount == -120000
    assert s.account_id == "a1"
    assert s.payee_id == "py1"
    assert s.category_id == "c1"
    assert s.memo == "Rent"
    assert s.deleted is False


def test_parse_scheduled_transaction_minimal() -> None:
    s = parse_scheduled_transaction(
        {
            "data": {
                "scheduled_transaction": {
                    "id": "st2",
                    "date_first": "2026-01-01",
                    "date_next": "2026-07-01",
                    "frequency": "never",
                    "amount": 0,
                    "account_id": "a1",
                    "deleted": False,
                }
            }
        }
    )
    assert s.id == "st2"
    assert s.payee_id is None
    assert s.category_id is None
    assert s.memo is None


def test_parse_scheduled_transactions_empty() -> None:
    assert parse_scheduled_transactions({"data": {"scheduled_transactions": []}}) == ()


def test_parse_scheduled_transaction_missing_raises() -> None:
    with pytest.raises((KeyError, TypeError)):
        parse_scheduled_transaction({"data": {}})
    with pytest.raises((KeyError, TypeError)):
        parse_scheduled_transaction({"data": {"scheduled_transaction": {}}})


def test_parse_transaction_single() -> None:
    txn = parse_transaction(
        {
            "data": {
                "transaction": {
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
            }
        }
    )
    assert txn.id == "t1"
    assert txn.amount == -54320
    assert txn.payee_name == "Market"
    assert txn.account_id == "a1"


def test_parse_transaction_missing_raises() -> None:
    with pytest.raises((KeyError, TypeError)):
        parse_transaction({"data": {}})
    with pytest.raises((KeyError, TypeError)):
        parse_transaction({"data": {"transaction": {}}})


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


PLAN_DETAIL_PAYLOAD = {
    "data": {
        "plan": {
            "id": "p1",
            "name": "My Plan",
            "last_modified_on": "2026-06-01T00:00:00Z",
            "first_month": "2025-01-01",
            "last_month": "2026-06-01",
            "currency_format": {
                "iso_code": "USD",
                "decimal_digits": 2,
                "decimal_separator": ".",
                "symbol_first": True,
                "group_separator": ",",
                "currency_symbol": "$",
                "display_symbol": True,
                "example_format": "123,456.78",
            },
            "date_format": {"format": "MM/DD/YYYY"},
            "accounts": [{"id": "a1"}, {"id": "a2"}],
            "category_groups": [{"id": "g1"}],
            "categories": [{"id": "c1"}, {"id": "c2"}, {"id": "c3"}],
            "payees": [{"id": "py1"}],
            "months": [{"month": "2026-06-01"}],
            "transactions": [{"id": "t1"}, {"id": "t2"}],
            "scheduled_transactions": [{"id": "st1"}],
        },
        "server_knowledge": 99,
    }
}


def test_parse_plan_detail_summary_metadata_and_formats() -> None:
    summary = parse_plan_detail_summary(PLAN_DETAIL_PAYLOAD)
    assert summary.id == "p1"
    assert summary.name == "My Plan"
    assert summary.first_month == "2025-01-01"
    assert summary.last_month == "2026-06-01"
    assert summary.last_modified_on == "2026-06-01T00:00:00Z"
    assert summary.currency_format is not None
    assert summary.currency_format.iso_code == "USD"
    assert summary.currency_format.currency_symbol == "$"
    assert summary.date_format is not None
    assert summary.date_format.format == "MM/DD/YYYY"


def test_parse_plan_detail_summary_counts() -> None:
    summary = parse_plan_detail_summary(PLAN_DETAIL_PAYLOAD)
    assert summary.accounts_count == 2
    assert summary.category_groups_count == 1
    assert summary.categories_count == 3
    assert summary.payees_count == 1
    assert summary.months_count == 1
    assert summary.transactions_count == 2
    assert summary.scheduled_transactions_count == 1


def test_parse_plan_detail_summary_missing_arrays_count_zero() -> None:
    summary = parse_plan_detail_summary(
        {"data": {"plan": {"id": "p2", "name": "Bare"}}}
    )
    assert summary.accounts_count == 0
    assert summary.transactions_count == 0
    assert summary.currency_format is None
    assert summary.date_format is None


def test_parse_plan_settings() -> None:
    settings = parse_plan_settings(
        {
            "data": {
                "settings": {
                    "date_format": {"format": "YYYY-MM-DD"},
                    "currency_format": {
                        "iso_code": "EUR",
                        "decimal_digits": 2,
                        "decimal_separator": ",",
                        "symbol_first": False,
                        "group_separator": ".",
                        "currency_symbol": "€",
                        "display_symbol": True,
                        "example_format": "123.456,78",
                    },
                }
            }
        }
    )
    assert settings.date_format is not None
    assert settings.date_format.format == "YYYY-MM-DD"
    assert settings.currency_format is not None
    assert settings.currency_format.iso_code == "EUR"


def test_parse_plan_settings_nullable_formats() -> None:
    settings = parse_plan_settings(
        {"data": {"settings": {"date_format": None, "currency_format": None}}}
    )
    assert settings.date_format is None
    assert settings.currency_format is None


def test_parse_user_returns_user_id() -> None:
    user = parse_user({"data": {"user": {"id": "u1"}}})
    assert user.id == "u1"


def test_parse_user_missing_fields_raises() -> None:
    with pytest.raises((KeyError, TypeError)):
        parse_user({"data": {}})
    with pytest.raises((KeyError, TypeError)):
        parse_user({"data": {"user": {}}})


def test_parse_empty_lists_yield_empty_tuples() -> None:
    assert parse_plans({"data": {"plans": []}}) == ()
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
