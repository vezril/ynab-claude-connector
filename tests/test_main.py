"""Tests for logging setup and the runnable entry point (tasks 5.1, 5.3)."""

from __future__ import annotations

import logging

import pytest

from ynab_claude_connector import __main__
from ynab_claude_connector.config import ConfigError
from ynab_claude_connector.logging_config import configure_logging


def test_configure_logging_accepts_valid_level() -> None:
    configure_logging("DEBUG")
    assert logging.getLogger().level == logging.DEBUG
    # Reset to a sane default so the level does not leak into other tests.
    configure_logging("WARNING")


def test_main_runs_server_with_configured_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    recorded: dict[str, str] = {}

    def fake_run(self: object, transport: str = "stdio") -> None:
        recorded["transport"] = transport

    monkeypatch.setattr("mcp.server.fastmcp.FastMCP.run", fake_run)
    monkeypatch.setenv("YNAB_CONNECTOR_TRANSPORT", "streamable-http")
    monkeypatch.setenv("YNAB_CONNECTOR_LOG_LEVEL", "WARNING")

    __main__.main()

    assert recorded["transport"] == "streamable-http"


def test_main_fails_fast_on_invalid_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False

    def fake_run(self: object, transport: str = "stdio") -> None:
        nonlocal called
        called = True

    monkeypatch.setattr("mcp.server.fastmcp.FastMCP.run", fake_run)
    monkeypatch.setenv("YNAB_CONNECTOR_TRANSPORT", "carrier-pigeon")

    with pytest.raises(ConfigError, match="transport"):
        __main__.main()
    assert called is False  # server never started
