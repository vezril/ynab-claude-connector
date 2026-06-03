"""ynab-claude-connector: a Claude connector for YNAB budget insights.

This module exposes the package version (derived from the Git tag at build
time by ``hatch-vcs`` and read back via :mod:`importlib.metadata`) and a small
set of pure, type-hinted helpers. The functional style established here —
no mutable module state, pure functions — is the pattern later features build on.
"""

from __future__ import annotations

import re
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _distribution_version
from typing import Final

__all__ = ["__version__", "is_semver", "package_name"]

_DISTRIBUTION_NAME: Final = "ynab-claude-connector"

# Strict Semantic Versioning 2.0.0 grammar (https://semver.org).
_SEMVER_PATTERN: Final = re.compile(
    r"^(?P<major>0|[1-9]\d*)"
    r"\.(?P<minor>0|[1-9]\d*)"
    r"\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<prerelease>"
    r"(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*"
    r"))?"
    r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$"
)


def package_name() -> str:
    """Return the distribution name (the single source of truth for metadata)."""
    return _DISTRIBUTION_NAME


def is_semver(value: str) -> bool:
    """Return ``True`` if ``value`` is a valid Semantic Versioning 2.0.0 string."""
    return _SEMVER_PATTERN.match(value) is not None


def _resolve_version() -> str:
    """Read the installed distribution version (tag-derived via hatch-vcs)."""
    try:
        return _distribution_version(_DISTRIBUTION_NAME)
    except PackageNotFoundError:  # pragma: no cover - only when not installed
        return "0.0.0+unknown"


__version__: Final[str] = _resolve_version()
