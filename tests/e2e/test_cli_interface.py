"""E2E tests for CLI interface functionality."""

import subprocess
import sys

import pytest


class TestCLIInterfaceE2E:
    """E2E tests for CLI interface."""

    def test_cli_welcome_message(self) -> None:
        """Test that CLI displays welcome message on startup."""
        # Run the CLI command
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "clean_interfaces.main"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert "Welcome to Clean Interfaces!" in result.stdout
        assert "Type --help for more information" in result.stdout

    def test_cli_help_command(self) -> None:
        """Test that CLI displays help message with --help flag."""
        # Run the CLI command with --help
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "clean_interfaces.main", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "Options" in result.stdout  # Typer uses "Options" without colon
        assert "--help" in result.stdout

    def test_cli_with_interface_type_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that CLI respects INTERFACE_TYPE environment variable."""
        # Set environment variable
        monkeypatch.setenv("INTERFACE_TYPE", "cli")

        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "clean_interfaces.main"],
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0
        assert "Welcome to Clean Interfaces!" in result.stdout
