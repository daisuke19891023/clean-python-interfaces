#!/usr/bin/env python3
"""Main entry point for clean_interfaces."""

import sys
from typing import NoReturn


def main() -> NoReturn:
    """Execute the main function."""
    import logging

    logger = logging.getLogger(__name__)
    logger.info("Hello from clean_interfaces!")
    sys.exit(0)


if __name__ == "__main__":
    main()
