"""MCP server factory.

All usage of the MCP SDK is confined to this module (and ``__main__``), so a
future SDK API change touches one place. ``build_server`` is a stateless
factory: each call returns a fresh, fully-configured :class:`FastMCP` instance
with the connector's tools registered.
"""

from __future__ import annotations

from typing import Final

from mcp.server.fastmcp import FastMCP

from ynab_claude_connector.config import ServerConfig
from ynab_claude_connector.tools import ping
from ynab_claude_connector.ynab.tools import (
    get_category,
    get_month,
    get_month_category,
    get_payee,
    get_payee_location,
    get_plan,
    get_plan_settings,
    get_user,
    list_accounts,
    list_categories,
    list_money_movement_groups,
    list_money_movement_groups_for_month,
    list_money_movements,
    list_money_movements_for_month,
    list_months,
    list_payee_locations,
    list_payee_locations_for_payee,
    list_payees,
    list_plans,
    list_transactions,
)

_SERVER_NAME: Final = "ynab-claude-connector"

# Tools exposed by the connector: the health probe plus the YNAB read tools.
_TOOLS: Final = (
    ping,
    get_user,
    list_plans,
    get_plan,
    get_plan_settings,
    list_accounts,
    list_categories,
    get_category,
    get_month_category,
    list_payees,
    get_payee,
    list_payee_locations,
    get_payee_location,
    list_payee_locations_for_payee,
    list_months,
    get_month,
    list_money_movements,
    list_money_movements_for_month,
    list_money_movement_groups,
    list_money_movement_groups_for_month,
    list_transactions,
)


def build_server(config: ServerConfig) -> FastMCP:
    """Build a configured MCP server with all connector tools registered."""
    server: FastMCP = FastMCP(
        _SERVER_NAME,
        host=config.host,
        port=config.port,
        log_level=config.log_level,
    )
    for tool in _TOOLS:
        server.add_tool(tool)
    return server
