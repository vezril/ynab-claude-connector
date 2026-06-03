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
class Budget:
    id: str
    name: str


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


def parse_budgets(payload: Mapping[str, Any]) -> tuple[Budget, ...]:
    budgets = _data(payload).get("budgets", []) or []
    return tuple(Budget(id=item["id"], name=item["name"]) for item in budgets)


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


def parse_categories(payload: Mapping[str, Any]) -> tuple[Category, ...]:
    groups = _data(payload).get("category_groups", []) or []
    return tuple(
        Category(
            id=category["id"],
            name=category["name"],
            category_group_id=category.get("category_group_id"),
            budgeted=int(category.get("budgeted", 0)),
            activity=int(category.get("activity", 0)),
            balance=int(category.get("balance", 0)),
        )
        for group in groups
        for category in (group.get("categories", []) or [])
    )


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
