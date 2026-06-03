"""Tests for version exposure and SemVer validation (tasks 3.1, 3.4)."""

from __future__ import annotations

import importlib.metadata

from ynab_claude_connector import __version__, is_semver, package_name


def _is_release_version(value: str) -> bool:
    """A final release has no PEP 440 dev/local segment."""
    return "dev" not in value and "+" not in value


def test_version_is_exposed_and_nonempty() -> None:
    assert isinstance(__version__, str)
    assert __version__ != ""


def test_version_matches_installed_metadata() -> None:
    # Single source of truth: the value comes from package metadata
    # (derived from the Git tag by hatch-vcs).
    assert __version__ == importlib.metadata.version(package_name())


def test_version_starts_with_semver_core() -> None:
    # Even dev builds (e.g. "0.1.dev1+g<sha>") start with MAJOR.MINOR.
    head = __version__.split("dev")[0].split("+")[0].rstrip(".")
    assert head.split(".")[0].isdigit()


def test_release_version_is_strict_semver() -> None:
    # When this is a tagged release (no dev/local part) it must be SemVer.
    if _is_release_version(__version__):
        assert is_semver(__version__)


def test_is_semver_accepts_basic_release() -> None:
    assert is_semver("0.1.0")
    assert is_semver("1.2.3")
    assert is_semver("10.20.30")


def test_is_semver_accepts_prerelease() -> None:
    # Edge case: experimental/pre-release identifiers are valid SemVer.
    assert is_semver("0.2.0-rc.1")
    assert is_semver("1.0.0-alpha")
    assert is_semver("1.0.0-0.3.7")
    assert is_semver("1.0.0-x.7.z.92")


def test_is_semver_accepts_build_metadata() -> None:
    assert is_semver("1.0.0+build.1")
    assert is_semver("1.0.0-beta+exp.sha.5114f85")


def test_is_semver_rejects_invalid_strings() -> None:
    # Edge cases: malformed versions must be rejected.
    assert not is_semver("")  # empty
    assert not is_semver("1.2")  # missing patch
    assert not is_semver("1.2.3.4")  # too many segments
    assert not is_semver("v1.2.3")  # leading "v" is a tag prefix, not SemVer
    assert not is_semver("01.2.3")  # leading zero
    assert not is_semver("1.2.3-")  # empty prerelease
    assert not is_semver("a.b.c")  # non-numeric core
