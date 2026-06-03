"""Tests for environment-based connector configuration (tasks 2.1, 2.2, 2.4)."""

from __future__ import annotations

import pytest

from ynab_claude_connector.config import ConfigError, ServerConfig, from_env


def test_defaults_apply_for_empty_environment() -> None:
    config = from_env({})
    assert config == ServerConfig(
        transport="stdio",
        host="127.0.0.1",
        port=8000,
        log_level="INFO",
    )


def test_environment_overrides_are_applied() -> None:
    config = from_env(
        {
            "YNAB_CONNECTOR_TRANSPORT": "streamable-http",
            "YNAB_CONNECTOR_HOST": "0.0.0.0",
            "YNAB_CONNECTOR_PORT": "9001",
            "YNAB_CONNECTOR_LOG_LEVEL": "DEBUG",
        }
    )
    assert config.transport == "streamable-http"
    assert config.host == "0.0.0.0"
    assert config.port == 9001
    assert isinstance(config.port, int)
    assert config.log_level == "DEBUG"


def test_config_is_immutable() -> None:
    config = from_env({})
    with pytest.raises(AttributeError):
        config.port = 1234  # type: ignore[misc]


def test_invalid_transport_is_rejected() -> None:
    with pytest.raises(ConfigError, match="transport"):
        from_env({"YNAB_CONNECTOR_TRANSPORT": "carrier-pigeon"})


def test_non_integer_port_is_rejected() -> None:
    with pytest.raises(ConfigError, match="port"):
        from_env({"YNAB_CONNECTOR_PORT": "abc"})


def test_out_of_range_port_is_rejected() -> None:
    with pytest.raises(ConfigError, match="port"):
        from_env({"YNAB_CONNECTOR_PORT": "70000"})


def test_invalid_log_level_is_rejected() -> None:
    with pytest.raises(ConfigError, match="log level"):
        from_env({"YNAB_CONNECTOR_LOG_LEVEL": "VERBOSE"})
