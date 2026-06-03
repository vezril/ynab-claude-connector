"""Logging setup for the connector.

Named ``logging_config`` (not ``logging``) to avoid shadowing the standard
library module. ``configure_logging`` is the one thin side-effecting function
in the otherwise-pure core.
"""

from __future__ import annotations

import logging

_LOG_FORMAT: str = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def configure_logging(level: str) -> None:
    """Configure root logging at the given (already-validated) level name."""
    logging.basicConfig(
        level=getattr(logging, level),
        format=_LOG_FORMAT,
        force=True,
    )
