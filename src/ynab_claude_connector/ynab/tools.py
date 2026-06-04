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
    MoneyMovement,
    MoneyMovementGroup,
    Month,
    Payee,
    PayeeLocation,
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


async def get_category(category_id: str, plan_id: str = _DEFAULT_PLAN) -> Category:
    """Return a single category by id (defaults to the last-used plan)."""
    async with client_from_env(_config()) as client:
        return await client.get_category(category_id, plan_id)


async def get_month_category(
    month: str, category_id: str, plan_id: str = _DEFAULT_PLAN
) -> Category:
    """Return a category's values for a month (`current` or an ISO `YYYY-MM-01`)."""
    async with client_from_env(_config()) as client:
        return await client.get_month_category(month, category_id, plan_id)


async def list_payees(plan_id: str = _DEFAULT_PLAN) -> tuple[Payee, ...]:
    """List payees for a plan (defaults to last-used)."""
    async with client_from_env(_config()) as client:
        return await client.list_payees(plan_id)


async def get_payee(payee_id: str, plan_id: str = _DEFAULT_PLAN) -> Payee:
    """Return a single payee by id (defaults to the last-used plan)."""
    async with client_from_env(_config()) as client:
        return await client.get_payee(payee_id, plan_id)


async def list_payee_locations(
    plan_id: str = _DEFAULT_PLAN,
) -> tuple[PayeeLocation, ...]:
    """List all payee locations for a plan (defaults to last-used)."""
    async with client_from_env(_config()) as client:
        return await client.list_payee_locations(plan_id)


async def get_payee_location(
    payee_location_id: str, plan_id: str = _DEFAULT_PLAN
) -> PayeeLocation:
    """Return a single payee location by id (defaults to the last-used plan)."""
    async with client_from_env(_config()) as client:
        return await client.get_payee_location(payee_location_id, plan_id)


async def list_payee_locations_for_payee(
    payee_id: str, plan_id: str = _DEFAULT_PLAN
) -> tuple[PayeeLocation, ...]:
    """List payee locations for a specific payee (defaults to last-used plan)."""
    async with client_from_env(_config()) as client:
        return await client.list_payee_locations_for_payee(payee_id, plan_id)


async def list_months(plan_id: str = _DEFAULT_PLAN) -> tuple[Month, ...]:
    """List the plan's month summaries (defaults to last-used)."""
    async with client_from_env(_config()) as client:
        return await client.list_months(plan_id)


async def get_month(month: str, plan_id: str = _DEFAULT_PLAN) -> Month:
    """Return a single month (`month` accepts `current` or an ISO `YYYY-MM-01`)."""
    async with client_from_env(_config()) as client:
        return await client.get_month(month, plan_id)


async def list_money_movements(
    plan_id: str = _DEFAULT_PLAN,
) -> tuple[MoneyMovement, ...]:
    """List money movements (category budget reallocations) for a plan."""
    async with client_from_env(_config()) as client:
        return await client.list_money_movements(plan_id)


async def list_money_movements_for_month(
    month: str, plan_id: str = _DEFAULT_PLAN
) -> tuple[MoneyMovement, ...]:
    """List money movements for a month (`current` or an ISO `YYYY-MM-01`)."""
    async with client_from_env(_config()) as client:
        return await client.list_money_movements_for_month(month, plan_id)


async def list_money_movement_groups(
    plan_id: str = _DEFAULT_PLAN,
) -> tuple[MoneyMovementGroup, ...]:
    """List money movement groups for a plan (defaults to last-used)."""
    async with client_from_env(_config()) as client:
        return await client.list_money_movement_groups(plan_id)


async def list_money_movement_groups_for_month(
    month: str, plan_id: str = _DEFAULT_PLAN
) -> tuple[MoneyMovementGroup, ...]:
    """List money movement groups for a month (`current` or an ISO `YYYY-MM-01`)."""
    async with client_from_env(_config()) as client:
        return await client.list_money_movement_groups_for_month(month, plan_id)


async def list_transactions(
    plan_id: str = _DEFAULT_PLAN,
) -> tuple[Transaction, ...]:
    """List transactions for a plan (defaults to last-used)."""
    async with client_from_env(_config()) as client:
        return await client.list_transactions(plan_id)


async def get_transaction(
    transaction_id: str, plan_id: str = _DEFAULT_PLAN
) -> Transaction:
    """Return a single transaction by id (defaults to the last-used plan)."""
    async with client_from_env(_config()) as client:
        return await client.get_transaction(transaction_id, plan_id)


async def list_transactions_by_account(
    account_id: str, plan_id: str = _DEFAULT_PLAN
) -> tuple[Transaction, ...]:
    """List a specific account's transactions (defaults to last-used plan)."""
    async with client_from_env(_config()) as client:
        return await client.list_transactions_by_account(account_id, plan_id)


async def list_transactions_by_category(
    category_id: str, plan_id: str = _DEFAULT_PLAN
) -> tuple[Transaction, ...]:
    """List a specific category's transactions (defaults to last-used plan)."""
    async with client_from_env(_config()) as client:
        return await client.list_transactions_by_category(category_id, plan_id)


async def list_transactions_by_payee(
    payee_id: str, plan_id: str = _DEFAULT_PLAN
) -> tuple[Transaction, ...]:
    """List a specific payee's transactions (defaults to last-used plan)."""
    async with client_from_env(_config()) as client:
        return await client.list_transactions_by_payee(payee_id, plan_id)


async def list_transactions_by_month(
    month: str, plan_id: str = _DEFAULT_PLAN
) -> tuple[Transaction, ...]:
    """List a month's transactions (`month` is `current` or an ISO `YYYY-MM-01`)."""
    async with client_from_env(_config()) as client:
        return await client.list_transactions_by_month(month, plan_id)
