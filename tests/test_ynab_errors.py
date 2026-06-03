"""Tests for the YNAB error taxonomy and mapper (task 3.1)."""

from __future__ import annotations

from ynab_claude_connector.ynab.errors import (
    YnabApiError,
    YnabAuthError,
    YnabError,
    YnabRateLimitError,
    error_from_response,
)

UNAUTHORIZED = {"error": {"id": "401", "name": "unauthorized", "detail": "bad token"}}
RATE_LIMITED = {"error": {"id": "429", "name": "too_many_requests", "detail": "slow"}}
SERVER_ERROR = {
    "error": {"id": "500", "name": "internal_server_error", "detail": "boom"}
}


def test_401_maps_to_auth_error() -> None:
    err = error_from_response(401, UNAUTHORIZED)
    assert isinstance(err, YnabAuthError)
    assert isinstance(err, YnabError)


def test_403_maps_to_auth_error() -> None:
    assert isinstance(error_from_response(403, UNAUTHORIZED), YnabAuthError)


def test_429_maps_to_rate_limit_error() -> None:
    err = error_from_response(429, RATE_LIMITED)
    assert isinstance(err, YnabRateLimitError)
    assert "limit" in str(err).lower()


def test_other_status_maps_to_api_error_with_status_and_detail() -> None:
    err = error_from_response(500, SERVER_ERROR)
    assert isinstance(err, YnabApiError)
    assert err.status == 500
    assert "boom" in str(err)


def test_api_error_without_error_body_is_safe() -> None:
    err = error_from_response(503, {})
    assert isinstance(err, YnabApiError)
    assert err.status == 503
