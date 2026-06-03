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
    Category,
    Plan,
    PlanDetailSummary,
    PlanSettings,
    Transaction,
    User,
)

_DEFAULT_PLAN = "last-used"


def _config() -> ServerConfig:
    return from_env(dict(os.environ))


async def get_user() -> User:
    """Return the authenticated YNAB user's id (GET /user)."""
    async with client_from_env(_config()) as client:
        return await client.get_user()


async def list_plans() -> tuple[Plan, ...]:
    """List the user's YNAB plans (ids and names)."""
    async with client_from_env(_config()) as client:
        return await client.list_plans()


async def get_plan(plan_id: str = _DEFAULT_PLAN) -> PlanDetailSummary:
    """Return a curated summary of a plan: metadata, formats, and entity counts."""
    async with client_from_env(_config()) as client:
        return await client.get_plan(plan_id)


async def get_plan_settings(plan_id: str = _DEFAULT_PLAN) -> PlanSettings:
    """Return a plan's date and currency format (defaults to last-used)."""
    async with client_from_env(_config()) as client:
        return await client.get_plan_settings(plan_id)


async def list_accounts(plan_id: str = _DEFAULT_PLAN) -> tuple[Account, ...]:
    """List accounts (with milliunit balances) for a plan (defaults to last-used)."""
    async with client_from_env(_config()) as client:
        return await client.list_accounts(plan_id)


async def list_categories(plan_id: str = _DEFAULT_PLAN) -> tuple[Category, ...]:
    """List plan categories for a plan (defaults to last-used)."""
    async with client_from_env(_config()) as client:
        return await client.list_categories(plan_id)


async def list_transactions(
    plan_id: str = _DEFAULT_PLAN,
) -> tuple[Transaction, ...]:
    """List transactions for a plan (defaults to last-used)."""
    async with client_from_env(_config()) as client:
        return await client.list_transactions(plan_id)
