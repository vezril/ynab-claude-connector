"""Tests for the trivial health tool (task 3.1)."""

from __future__ import annotations

from ynab_claude_connector.tools import ping


def test_ping_returns_pong() -> None:
    assert ping() == "pong"


def test_ping_is_pure() -> None:
    # Repeated calls return the same value with no side effects.
    assert ping() == ping() == "pong"
