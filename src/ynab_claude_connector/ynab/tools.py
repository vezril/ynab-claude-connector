"""YNAB MCP tools.

Each tool is a thin async wrapper: read configuration from the environment,
build a client (which fails fast with a clear error if the token is missing),
call the corresponding endpoint, and return typed models. ``client_from_env``
is referenced at module scope so tests can substitute a transport-backed client.
"""

from __future__ import annotations

import os

from ynab_claude_connector.config import ServerConfig, from_env
from ynab_claude_connector.ynab.client import client_from_env
from ynab_claude_connector.ynab.models import (
    Account,
    Budget,
    Category,
    Transaction,
    User,
)

_DEFAULT_BUDGET = "default"


def _config() -> ServerConfig:
    return from_env(dict(os.environ))


async def get_user() -> User:
    """Return the authenticated YNAB user's id (GET /user)."""
    async with client_from_env(_config()) as client:
        return await client.get_user()


async def list_budgets() -> tuple[Budget, ...]:
    """List the user's YNAB budgets (ids and names)."""
    async with client_from_env(_config()) as client:
        return await client.list_budgets()


async def list_accounts(budget_id: str = _DEFAULT_BUDGET) -> tuple[Account, ...]:
    """List accounts (with milliunit balances) for a budget (defaults to last-used)."""
    async with client_from_env(_config()) as client:
        return await client.list_accounts(budget_id)


async def list_categories(budget_id: str = _DEFAULT_BUDGET) -> tuple[Category, ...]:
    """List budget categories for a budget (defaults to last-used)."""
    async with client_from_env(_config()) as client:
        return await client.list_categories(budget_id)


async def list_transactions(
    budget_id: str = _DEFAULT_BUDGET,
) -> tuple[Transaction, ...]:
    """List transactions for a budget (defaults to last-used)."""
    async with client_from_env(_config()) as client:
        return await client.list_transactions(budget_id)
