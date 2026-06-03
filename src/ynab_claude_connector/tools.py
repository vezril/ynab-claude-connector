"""Connector tools.

Tools are plain, pure, type-hinted functions. FastMCP derives each tool's
input schema from the function signature, so type hints are the contract.
This module holds only the trivial health tool for now; YNAB tools land in a
later feature.
"""

from __future__ import annotations


def ping() -> str:
    """Return a constant health response, proving the tool request path works."""
    return "pong"
