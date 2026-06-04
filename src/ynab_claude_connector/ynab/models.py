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
class Payee:
    id: str
    name: str
    transfer_account_id: str | None
    deleted: bool


@dataclass(frozen=True, slots=True)
class PayeeLocation:
    id: str
    payee_id: str
    latitude: str | None
    longitude: str | None
    deleted: bool


@dataclass(frozen=True, slots=True)
class Month:
    month: str  # ISO date identifying the month, e.g. "2026-06-01"
    note: str | None
    income: int  # milliunits
    budgeted: int  # milliunits
    activity: int  # milliunits
    to_be_budgeted: int  # milliunits
    age_of_money: int | None
    deleted: bool


@dataclass(frozen=True, slots=True)
class MoneyMovement:
    id: str
    month: str | None
    moved_at: str | None
    note: str | None
    money_movement_group_id: str | None
    performed_by_user_id: str | None
    from_category_id: str | None
    to_category_id: str | None
    amount: int  # milliunits


@dataclass(frozen=True, slots=True)
class MoneyMovementGroup:
    id: str
    group_created_at: str | None
    month: str | None
    note: str | None
    performed_by_user_id: str | None


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


def _payee_from(item: Mapping[str, Any]) -> Payee:
    return Payee(
        id=item["id"],
        name=item["name"],
        transfer_account_id=item.get("transfer_account_id"),
        deleted=bool(item.get("deleted", False)),
    )


def parse_payees(payload: Mapping[str, Any]) -> tuple[Payee, ...]:
    payees = _data(payload).get("payees", []) or []
    return tuple(_payee_from(item) for item in payees)


def parse_payee(payload: Mapping[str, Any]) -> Payee:
    # `payee` and its `id` are required: a malformed body raises.
    return _payee_from(_data(payload)["payee"])


def _payee_location_from(item: Mapping[str, Any]) -> PayeeLocation:
    return PayeeLocation(
        id=item["id"],
        payee_id=item["payee_id"],
        latitude=item.get("latitude"),
        longitude=item.get("longitude"),
        deleted=bool(item.get("deleted", False)),
    )


def parse_payee_locations(payload: Mapping[str, Any]) -> tuple[PayeeLocation, ...]:
    locations = _data(payload).get("payee_locations", []) or []
    return tuple(_payee_location_from(item) for item in locations)


def parse_payee_location(payload: Mapping[str, Any]) -> PayeeLocation:
    # `payee_location` and its `id` are required: a malformed body raises.
    return _payee_location_from(_data(payload)["payee_location"])


def _month_from(item: Mapping[str, Any]) -> Month:
    return Month(
        month=item["month"],
        note=item.get("note"),
        income=int(item.get("income", 0)),
        budgeted=int(item.get("budgeted", 0)),
        activity=int(item.get("activity", 0)),
        to_be_budgeted=int(item.get("to_be_budgeted", 0)),
        age_of_money=item.get("age_of_money"),
        deleted=bool(item.get("deleted", False)),
    )


def parse_months(payload: Mapping[str, Any]) -> tuple[Month, ...]:
    months = _data(payload).get("months", []) or []
    return tuple(_month_from(item) for item in months)


def parse_month(payload: Mapping[str, Any]) -> Month:
    # `month` object (and its `month` id) is required: a malformed body raises.
    return _month_from(_data(payload)["month"])


def _money_movement_from(item: Mapping[str, Any]) -> MoneyMovement:
    return MoneyMovement(
        id=item["id"],
        month=item.get("month"),
        moved_at=item.get("moved_at"),
        note=item.get("note"),
        money_movement_group_id=item.get("money_movement_group_id"),
        performed_by_user_id=item.get("performed_by_user_id"),
        from_category_id=item.get("from_category_id"),
        to_category_id=item.get("to_category_id"),
        amount=int(item["amount"]),
    )


def _money_movement_group_from(item: Mapping[str, Any]) -> MoneyMovementGroup:
    return MoneyMovementGroup(
        id=item["id"],
        group_created_at=item.get("group_created_at"),
        month=item.get("month"),
        note=item.get("note"),
        performed_by_user_id=item.get("performed_by_user_id"),
    )


def parse_money_movements(payload: Mapping[str, Any]) -> tuple[MoneyMovement, ...]:
    movements = _data(payload).get("money_movements", []) or []
    return tuple(_money_movement_from(item) for item in movements)


def parse_money_movement_groups(
    payload: Mapping[str, Any],
) -> tuple[MoneyMovementGroup, ...]:
    groups = _data(payload).get("money_movement_groups", []) or []
    return tuple(_money_movement_group_from(item) for item in groups)


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
