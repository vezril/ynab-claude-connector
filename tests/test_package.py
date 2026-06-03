"""Tests for the placeholder pure functions (task 3.2)."""

from __future__ import annotations

from ynab_claude_connector import package_name


def test_package_name_returns_distribution_name() -> None:
    assert package_name() == "ynab-claude-connector"


def test_package_name_is_pure() -> None:
    # Calling twice yields the same value with no side effects.
    assert package_name() == package_name()
