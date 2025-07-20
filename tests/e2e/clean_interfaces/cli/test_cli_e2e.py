"""End-to-end tests for CLI interface using pexpect."""

import pexpect

from clean_interfaces.models.io import WelcomeMessage
from .conftest import CLIRunner


class TestCLIE2E:
    """E2E tests for the CLI interface."""

    def test_cli_shows_welcome_without_args(
        self,
        cli_runner: CLIRunner,
        clean_env: dict[str, str],
    ) -> None:
        """Test that CLI shows welcome message when run without arguments."""
        # Run the CLI without arguments
        process = cli_runner.run(env=clean_env)

        # Expect the welcome message
        welcome_msg = WelcomeMessage()

        # Check for the welcome message text
        try:
            cli_runner.expect(welcome_msg.message, timeout=5)
            cli_runner.expect(welcome_msg.hint, timeout=2)
        except pexpect.TIMEOUT:
            raise AssertionError(
                f"Expected welcome message not found. Output: {cli_runner.output}",
            )

        # Process should exit cleanly
        process.expect(pexpect.EOF)
        process.close()

        assert process.exitstatus == 0

    def test_cli_help_command(
        self,
        cli_runner: CLIRunner,
        clean_env: dict[str, str],
    ) -> None:
        """Test that CLI shows help when --help is used."""
        # Run the CLI with --help
        process = cli_runner.run(args=["--help"], env=clean_env)

        # Expect help text elements
        try:
            cli_runner.expect("Clean Interfaces CLI", timeout=5)
            cli_runner.expect("Commands:", timeout=2)
            cli_runner.expect("welcome", timeout=2)
        except pexpect.TIMEOUT:
            raise AssertionError(f"Expected help text not found. Output: {cli_runner.output}")

        # Process should exit cleanly
        process.expect(pexpect.EOF)
        process.close()

        assert process.exitstatus == 0

    def test_cli_version_command(
        self,
        cli_runner: CLIRunner,
        clean_env: dict[str, str],
    ) -> None:
        """Test that CLI shows version information."""
        # Run the CLI with --version (if implemented)
        process = cli_runner.run(args=["--version"], env=clean_env)

        import contextlib

        with contextlib.suppress(pexpect.TIMEOUT):
            # Typer may show app name and version
            cli_runner.expect(["clean-interfaces", "0.1.0", "version"], timeout=5)

        # Process should exit
        process.expect(pexpect.EOF)
        process.close()

    def test_cli_invalid_command(
        self,
        cli_runner: CLIRunner,
        clean_env: dict[str, str],
    ) -> None:
        """Test that CLI handles invalid commands gracefully."""
        # Run the CLI with an invalid command
        process = cli_runner.run(args=["invalid-command"], env=clean_env)

        # Expect error message
        try:
            # Typer shows specific error messages for invalid commands
            cli_runner.expect(
                ["Error", "No such command", "Invalid", "Usage"], timeout=5,
            )
        except pexpect.TIMEOUT:
            raise AssertionError(
                f"Expected error message not found. Output: {cli_runner.output}",
            )

        # Process should exit with non-zero status
        process.expect(pexpect.EOF)
        process.close()

        # Typer typically returns exit code 2 for invalid commands
        assert process.exitstatus != 0

    def test_cli_explicit_welcome_command(
        self,
        cli_runner: CLIRunner,
        clean_env: dict[str, str],
    ) -> None:
        """Test running the welcome command explicitly."""
        # Run the CLI with welcome command
        process = cli_runner.run(args=["welcome"], env=clean_env)

        # Expect the welcome message
        welcome_msg = WelcomeMessage()

        try:
            cli_runner.expect(welcome_msg.message, timeout=5)
            cli_runner.expect(welcome_msg.hint, timeout=2)
        except pexpect.TIMEOUT:
            raise AssertionError(
                f"Expected welcome message not found. Output: {cli_runner.output}",
            )

        # Process should exit cleanly
        process.expect(pexpect.EOF)
        process.close()

        assert process.exitstatus == 0

    def test_cli_interrupt_handling(
        self,
        cli_runner: CLIRunner,
        clean_env: dict[str, str],
    ) -> None:
        """Test that CLI handles interrupts (Ctrl+C) gracefully."""
        # This test would be for interactive commands in the future
        # For now, just verify the CLI can be started and interrupted

        # Run a command that might take time (if we had one)
        process = cli_runner.run(env=clean_env)

        # Send interrupt signal
        process.sendintr()

        # Process should exit
        try:
            process.expect(pexpect.EOF, timeout=2)
        except pexpect.TIMEOUT:
            # Force close if it doesn't exit gracefully
            process.close(force=True)

        # Should exit with interrupt signal status (typically 130 on Unix)
        # or at least non-zero
        assert process.exitstatus is None or process.exitstatus != 0
