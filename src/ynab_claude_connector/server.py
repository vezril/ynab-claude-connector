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

_SERVER_NAME: Final = "ynab-claude-connector"

# Tools exposed by the connector. Add YNAB tools here in a later feature.
_TOOLS: Final = (ping,)


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
