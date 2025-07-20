#!/usr/bin/env python3
"""Main entry point for clean_interfaces."""

import sys
from typing import NoReturn

from clean_interfaces.app import run_app


def main() -> NoReturn:
    """Execute the main function."""
    run_app()
    sys.exit(0)


if __name__ == "__main__":
    main()
