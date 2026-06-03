"""Typed YNAB models and pure response parsers.

Each ``parse_*`` function is pure: it maps a YNAB ``{"data": {...}}`` response
envelope to a tuple of frozen dataclasses, reading only known keys and treating
optional fields defensively (missing -> ``None`` / empty). Monetary values are
kept in YNAB **milliunits** (integers) with no lossy currency conversion.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class User:
    id: str


@dataclass(frozen=True, slots=True)
class Plan:
    id: str
    name: str


@dataclass(frozen=True, slots=True)
class CurrencyFormat:
    iso_code: str
    decimal_digits: int
    decimal_separator: str
    symbol_first: bool
    group_separator: str
    currency_symbol: str
    display_symbol: bool
    example_format: str


@dataclass(frozen=True, slots=True)
class DateFormat:
    format: str


@dataclass(frozen=True, slots=True)
class PlanSettings:
    date_format: DateFormat | None
    currency_format: CurrencyFormat | None


@dataclass(frozen=True, slots=True)
class PlanDetailSummary:
    id: str
    name: str
    last_modified_on: str | None
    first_month: str | None
    last_month: str | None
    currency_format: CurrencyFormat | None
    date_format: DateFormat | None
    accounts_count: int
    category_groups_count: int
    categories_count: int
    payees_count: int
    months_count: int
    transactions_count: int
    scheduled_transactions_count: int


@dataclass(frozen=True, slots=True)
class Account:
    id: str
    name: str
    type: str
    on_budget: bool
    closed: bool
    balance: int  # milliunits


@dataclass(frozen=True, slots=True)
class Category:
    id: str
    name: str
    category_group_id: str | None
    budgeted: int  # milliunits
    activity: int  # milliunits
    balance: int  # milliunits


@dataclass(frozen=True, slots=True)
class Transaction:
    id: str
    date: str
    amount: int  # milliunits
    cleared: str
    approved: bool
    account_id: str
    memo: str | None
    payee_name: str | None
    category_id: str | None


def _data(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return the inner ``data`` object from a YNAB response envelope."""
    data = payload.get("data", {})
    return data if isinstance(data, Mapping) else {}


def parse_user(payload: Mapping[str, Any]) -> User:
    # `id` is required: a malformed body should raise, not yield an empty id.
    return User(id=_data(payload)["user"]["id"])


def parse_plans(payload: Mapping[str, Any]) -> tuple[Plan, ...]:
    plans = _data(payload).get("plans", []) or []
    return tuple(Plan(id=item["id"], name=item["name"]) for item in plans)


def _parse_currency_format(value: object) -> CurrencyFormat | None:
    if not isinstance(value, Mapping):
        return None
    return CurrencyFormat(
        iso_code=value["iso_code"],
        decimal_digits=int(value["decimal_digits"]),
        decimal_separator=value["decimal_separator"],
        symbol_first=bool(value["symbol_first"]),
        group_separator=value["group_separator"],
        currency_symbol=value["currency_symbol"],
        display_symbol=bool(value["display_symbol"]),
        example_format=value["example_format"],
    )


def _parse_date_format(value: object) -> DateFormat | None:
    if not isinstance(value, Mapping):
        return None
    return DateFormat(format=value["format"])


def _count(container: Mapping[str, Any], key: str) -> int:
    return len(container.get(key, []) or [])


def parse_plan_detail_summary(payload: Mapping[str, Any]) -> PlanDetailSummary:
    plan = _data(payload)["plan"]
    return PlanDetailSummary(
        id=plan["id"],
        name=plan["name"],
        last_modified_on=plan.get("last_modified_on"),
        first_month=plan.get("first_month"),
        last_month=plan.get("last_month"),
        currency_format=_parse_currency_format(plan.get("currency_format")),
        date_format=_parse_date_format(plan.get("date_format")),
        accounts_count=_count(plan, "accounts"),
        category_groups_count=_count(plan, "category_groups"),
        categories_count=_count(plan, "categories"),
        payees_count=_count(plan, "payees"),
        months_count=_count(plan, "months"),
        transactions_count=_count(plan, "transactions"),
        scheduled_transactions_count=_count(plan, "scheduled_transactions"),
    )


def parse_plan_settings(payload: Mapping[str, Any]) -> PlanSettings:
    settings = _data(payload)["settings"]
    return PlanSettings(
        date_format=_parse_date_format(settings.get("date_format")),
        currency_format=_parse_currency_format(settings.get("currency_format")),
    )


def parse_accounts(payload: Mapping[str, Any]) -> tuple[Account, ...]:
    accounts = _data(payload).get("accounts", []) or []
    return tuple(
        Account(
            id=item["id"],
            name=item["name"],
            type=item["type"],
            on_budget=bool(item.get("on_budget", False)),
            closed=bool(item.get("closed", False)),
            balance=int(item.get("balance", 0)),
        )
        for item in accounts
    )


def _category_from(item: Mapping[str, Any]) -> Category:
    return Category(
        id=item["id"],
        name=item["name"],
        category_group_id=item.get("category_group_id"),
        budgeted=int(item.get("budgeted", 0)),
        activity=int(item.get("activity", 0)),
        balance=int(item.get("balance", 0)),
    )


def parse_categories(payload: Mapping[str, Any]) -> tuple[Category, ...]:
    groups = _data(payload).get("category_groups", []) or []
    return tuple(
        _category_from(category)
        for group in groups
        for category in (group.get("categories", []) or [])
    )


def parse_category(payload: Mapping[str, Any]) -> Category:
    # `category` and its `id` are required: a malformed body raises.
    return _category_from(_data(payload)["category"])


def parse_transactions(payload: Mapping[str, Any]) -> tuple[Transaction, ...]:
    transactions = _data(payload).get("transactions", []) or []
    return tuple(
        Transaction(
            id=item["id"],
            date=item["date"],
            amount=int(item["amount"]),
            cleared=item.get("cleared", ""),
            approved=bool(item.get("approved", False)),
            account_id=item["account_id"],
            memo=item.get("memo"),
            payee_name=item.get("payee_name"),
            category_id=item.get("category_id"),
        )
        for item in transactions
    )
