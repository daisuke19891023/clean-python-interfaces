"""Main entry point for clean_interfaces."""

import sys
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from clean_interfaces.app import run_app


def main(
    dotenv: Annotated[
        Path | None,
        typer.Option(
            "--dotenv",
            "-e",
            help="Path to .env file to load environment variables from",
            exists=True,
            file_okay=True,
            dir_okay=False,
            readable=True,
        ),
    ] = None,
) -> NoReturn:
    """Execute the main function with optional dotenv file."""
    # Clear sys.argv to prevent CLI interface from processing our arguments
    original_argv = sys.argv
    sys.argv = [sys.argv[0]]  # Keep only the script name

    try:
        run_app(dotenv_path=dotenv)
    finally:
        sys.argv = original_argv

    sys.exit(0)


if __name__ == "__main__":
    typer.run(main)
