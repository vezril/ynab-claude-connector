"""Environment-based connector configuration.

Configuration is parsed from a plain string mapping (typically ``os.environ``)
into an immutable :class:`ServerConfig`. ``from_env`` is a pure function: it
takes the environment as an argument and either returns a validated config or
raises :class:`ConfigError`. No global state, no side effects.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, Literal, get_args

Transport = Literal["stdio", "streamable-http"]
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

_VALID_TRANSPORTS: Final[tuple[Transport, ...]] = get_args(Transport)
_VALID_LOG_LEVELS: Final[tuple[LogLevel, ...]] = get_args(LogLevel)

_MIN_PORT: Final = 1
_MAX_PORT: Final = 65535

# Environment variable names.
_ENV_TRANSPORT: Final = "YNAB_CONNECTOR_TRANSPORT"
_ENV_HOST: Final = "YNAB_CONNECTOR_HOST"
_ENV_PORT: Final = "YNAB_CONNECTOR_PORT"
_ENV_LOG_LEVEL: Final = "YNAB_CONNECTOR_LOG_LEVEL"

# Defaults.
_DEFAULT_TRANSPORT: Final[Transport] = "stdio"
_DEFAULT_HOST: Final = "127.0.0.1"
_DEFAULT_PORT: Final = 8000
_DEFAULT_LOG_LEVEL: Final[LogLevel] = "INFO"


class ConfigError(ValueError):
    """Raised when the environment holds an invalid configuration value."""


@dataclass(frozen=True, slots=True)
class ServerConfig:
    """Immutable connector configuration."""

    transport: Transport
    host: str
    port: int
    log_level: LogLevel


def _parse_transport(value: str) -> Transport:
    for valid in _VALID_TRANSPORTS:
        if value == valid:
            return valid
    raise ConfigError(
        f"Invalid transport {value!r}; expected one of {list(_VALID_TRANSPORTS)}."
    )


def _parse_port(value: str) -> int:
    try:
        port = int(value)
    except ValueError as exc:
        raise ConfigError(f"Invalid port {value!r}; expected an integer.") from exc
    if not _MIN_PORT <= port <= _MAX_PORT:
        raise ConfigError(f"Invalid port {port}; expected {_MIN_PORT}-{_MAX_PORT}.")
    return port


def _parse_log_level(value: str) -> LogLevel:
    upper = value.upper()
    for valid in _VALID_LOG_LEVELS:
        if upper == valid:
            return valid
    raise ConfigError(
        f"Invalid log level {value!r}; expected one of {list(_VALID_LOG_LEVELS)}."
    )


def from_env(env: Mapping[str, str]) -> ServerConfig:
    """Build a validated :class:`ServerConfig` from an environment mapping."""
    return ServerConfig(
        transport=_parse_transport(env.get(_ENV_TRANSPORT, _DEFAULT_TRANSPORT)),
        host=env.get(_ENV_HOST, _DEFAULT_HOST),
        port=_parse_port(env.get(_ENV_PORT, str(_DEFAULT_PORT))),
        log_level=_parse_log_level(env.get(_ENV_LOG_LEVEL, _DEFAULT_LOG_LEVEL)),
    )
