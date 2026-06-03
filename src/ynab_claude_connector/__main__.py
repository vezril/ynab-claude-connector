"""Runnable entry point for the connector.

``main`` is the thin imperative shell: read the environment, configure logging,
build the server, and start it on the configured transport. Configuration is
parsed first, so an invalid environment fails fast before the server serves.
"""

from __future__ import annotations

import os

from ynab_claude_connector.config import from_env
from ynab_claude_connector.logging_config import configure_logging
from ynab_claude_connector.server import build_server


def main() -> None:
    """Load config from the environment, build the server, and run it."""
    config = from_env(dict(os.environ))
    configure_logging(config.log_level)
    server = build_server(config)
    server.run(transport=config.transport)


if __name__ == "__main__":  # pragma: no cover
    main()
