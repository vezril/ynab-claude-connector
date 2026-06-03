"""Tests for the MCP server factory (tasks 4.1, 4.2, 4.4)."""

from __future__ import annotations

import asyncio
from typing import Any, cast

from mcp.server.fastmcp import FastMCP

from ynab_claude_connector.config import ServerConfig
from ynab_claude_connector.server import build_server

_CONFIG = ServerConfig(transport="stdio", host="127.0.0.1", port=8000, log_level="INFO")


def _tool_names(server: FastMCP) -> list[str]:
    tools = asyncio.run(server.list_tools())
    return [tool.name for tool in tools]


def test_build_server_returns_fastmcp_with_ping_registered() -> None:
    server = build_server(_CONFIG)
    assert isinstance(server, FastMCP)
    assert "ping" in _tool_names(server)


def test_ping_tool_has_input_schema_from_type_hints() -> None:
    server = build_server(_CONFIG)
    tools = asyncio.run(server.list_tools())
    ping_tool = next(tool for tool in tools if tool.name == "ping")
    assert ping_tool.inputSchema is not None


def test_build_server_applies_host_and_port_from_config() -> None:
    server = build_server(
        ServerConfig(
            transport="streamable-http",
            host="0.0.0.0",
            port=9100,
            log_level="WARNING",
        )
    )
    assert server.settings.host == "0.0.0.0"
    assert server.settings.port == 9100


def test_build_server_returns_independent_instances() -> None:
    first = build_server(_CONFIG)
    second = build_server(_CONFIG)
    assert first is not second


def test_ping_tool_invoked_through_server_returns_pong() -> None:
    server = build_server(_CONFIG)
    # FastMCP.call_tool returns (content_blocks, structured_result) at runtime,
    # but is annotated loosely as a union; cast to the real shape.
    _content, structured = cast(
        tuple[list[Any], dict[str, Any]],
        asyncio.run(server.call_tool("ping", {})),
    )
    assert structured == {"result": "pong"}
