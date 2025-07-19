#!/usr/bin/env python3
"""Main entry point for TestProject."""

import sys
from typing import NoReturn

from test_project.utils.logger import get_logger, setup_application_logging


def main() -> NoReturn:
    """Execute the main function."""
    # Set up application logging
    setup_application_logging("TestProject", "development")
    logger = get_logger(__name__)

    logger.info("Hello from TestProject!")
    sys.exit(0)


if __name__ == "__main__":
    main()
