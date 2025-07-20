"""Simple CLI E2E tests using subprocess for initial verification."""

import os
import subprocess
import sys
from pathlib import Path

from clean_interfaces.models.io import WelcomeMessage


class TestCLISimple:
    """Simple E2E tests for the CLI interface using subprocess."""

    @property
    def env(self) -> dict[str, str]:
        """Get environment variables for tests."""
        return {
            **os.environ,  # Include current environment
            "LOG_LEVEL": "ERROR",  # Suppress logs
            "PYTHONPATH": str(
                Path(__file__).parent / ".." / ".." / ".." / ".." / "src",
            ),
        }

    def test_cli_shows_welcome_without_args(self) -> None:
        """Test that CLI shows welcome message when run without arguments."""
        # Run the CLI without arguments
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "clean_interfaces.main"],
            capture_output=True,
            text=True,
            env=self.env,
            check=False,
        )

        # Check exit code
        assert result.returncode == 0

        # Check output contains welcome message
        welcome_msg = WelcomeMessage()
        assert welcome_msg.message in result.stdout
        assert welcome_msg.hint in result.stdout

        # Should not have errors
        assert not result.stderr or result.stderr.strip() == ""

    def test_cli_help_command(self) -> None:
        """Test that CLI shows help when --help is used."""
        # Run the CLI with --help
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "clean_interfaces.main", "--help"],
            capture_output=True,
            text=True,
            env=self.env,
            check=False,
        )

        # Check exit code
        assert result.returncode == 0

        # Check help text elements
        assert "Clean Interfaces CLI" in result.stdout
        # Typer uses Unicode box characters, check for actual command
        assert "welcome" in result.stdout
        assert "Display welcome message" in result.stdout

    def test_cli_invalid_command(self) -> None:
        """Test that CLI handles invalid commands gracefully."""
        # Run the CLI with an invalid command
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "clean_interfaces.main", "invalid-command"],
            capture_output=True,
            text=True,
            env=self.env,
            check=False,
        )

        # Should exit with non-zero status
        assert result.returncode != 0

        # Should show error message
        output = result.stdout + result.stderr
        assert any(word in output for word in ["Error", "No such command", "Invalid"])

    def test_cli_explicit_welcome_command(self) -> None:
        """Test running the welcome command explicitly."""
        # Run the CLI with welcome command
        result = subprocess.run(  # noqa: S603
            [sys.executable, "-m", "clean_interfaces.main", "welcome"],
            capture_output=True,
            text=True,
            env=self.env,
            check=False,
        )

        # Check exit code
        assert result.returncode == 0

        # Check output
        welcome_msg = WelcomeMessage()
        assert welcome_msg.message in result.stdout
        assert welcome_msg.hint in result.stdout
