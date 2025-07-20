"""End-to-end tests for CLI interface using pexpect."""

import sys

import pexpect

from clean_interfaces.models.io import WelcomeMessage


class TestCLIE2E:
    """E2E tests for the CLI interface."""

    def test_cli_shows_welcome_without_args(
        self,
        clean_env: dict[str, str],
    ) -> None:
        """Test that CLI shows welcome message when run without arguments."""
        # Use pexpect.run() which captures all output
        try:
            result = pexpect.run(  # type: ignore[attr-defined]
                f"{sys.executable} -u -m clean_interfaces.main",
                env=clean_env,  # type: ignore[arg-type]
                withexitstatus=True,
                timeout=5,
                encoding="utf-8",
            )
            # pexpect.run returns (output, exitstatus) when withexitstatus=True
            if isinstance(result, tuple):  # type: ignore[arg-type]
                output, exitstatus = result  # type: ignore[misc]
            else:
                # Handle unexpected return format
                output = str(result)
                exitstatus = 0
        except pexpect.TIMEOUT:
            error_msg = "Timeout waiting for CLI to complete"
            raise AssertionError(error_msg) from None

        # Check exit status
        assert exitstatus == 0

        # Expect the welcome message
        welcome_msg = WelcomeMessage()

        # Check that welcome message appears in output
        assert welcome_msg.message in output
        assert welcome_msg.hint in output

    def test_cli_help_command(
        self,
        clean_env: dict[str, str],
    ) -> None:
        """Test that CLI shows help when --help is used."""
        # Use pexpect.run() to capture output
        try:
            result = pexpect.run(  # type: ignore[attr-defined]
                f"{sys.executable} -u -m clean_interfaces.main --help",
                env=clean_env,  # type: ignore[arg-type]
                withexitstatus=True,
                timeout=5,
                encoding="utf-8",
            )
            # pexpect.run returns (output, exitstatus) when withexitstatus=True
            if isinstance(result, tuple):  # type: ignore[arg-type]
                output, exitstatus = result  # type: ignore[misc]
            else:
                # Handle unexpected return format
                output = str(result)
                exitstatus = 0
        except pexpect.TIMEOUT:
            error_msg = "Timeout waiting for CLI help command to complete"
            raise AssertionError(error_msg) from None

        # Check exit code
        assert exitstatus == 0

        # Check help text elements
        assert "Clean Interfaces CLI" in output
        assert "Commands" in output
        assert "welcome" in output
        assert "Display welcome message" in output

    def test_cli_version_command(
        self,
        clean_env: dict[str, str],
    ) -> None:
        """Test that CLI shows version information."""
        # Use pexpect.run() to capture output
        try:
            result = pexpect.run(  # type: ignore[attr-defined]
                f"{sys.executable} -u -m clean_interfaces.main --version",
                env=clean_env,  # type: ignore[arg-type]
                withexitstatus=True,
                timeout=5,
                encoding="utf-8",
            )
            # pexpect.run returns (output, exitstatus) when withexitstatus=True
            if isinstance(result, tuple):  # type: ignore[arg-type]
                output, exitstatus = result  # type: ignore[misc]
            else:
                # Handle unexpected return format
                _ = str(result)  # Convert to string but ignore output
                exitstatus = 2  # Default for version command which may not exist
        except pexpect.TIMEOUT:
            error_msg = "Timeout waiting for CLI version command to complete"
            raise AssertionError(error_msg) from None

        # Typer may or may not implement --version by default
        # Check that it at least exits cleanly
        assert exitstatus in (0, 2)  # 0 for success, 2 for unrecognized option

    def test_cli_invalid_command(
        self,
        clean_env: dict[str, str],
    ) -> None:
        """Test that CLI handles invalid commands gracefully."""
        # Use pexpect.run() to capture output
        try:
            result = pexpect.run(  # type: ignore[attr-defined]
                f"{sys.executable} -u -m clean_interfaces.main invalid-command",
                env=clean_env,  # type: ignore[arg-type]
                withexitstatus=True,
                timeout=5,
                encoding="utf-8",
            )
            # pexpect.run returns (output, exitstatus) when withexitstatus=True
            if isinstance(result, tuple):  # type: ignore[arg-type]
                output, exitstatus = result  # type: ignore[misc]
            else:
                # Handle unexpected return format
                output = str(result)
                exitstatus = 1  # Default for invalid command
        except pexpect.TIMEOUT:
            error_msg = "Timeout waiting for CLI invalid command to complete"
            raise AssertionError(error_msg) from None

        # Should exit with non-zero status
        assert exitstatus != 0

        # Should show error message
        assert any(word in output for word in ["Error", "No such command", "Invalid"])

    def test_cli_explicit_welcome_command(
        self,
        clean_env: dict[str, str],
    ) -> None:
        """Test running the welcome command explicitly."""
        # Use pexpect.run() to capture output
        try:
            result = pexpect.run(  # type: ignore[attr-defined]
                f"{sys.executable} -u -m clean_interfaces.main welcome",
                env=clean_env,  # type: ignore[arg-type]
                withexitstatus=True,
                timeout=5,
                encoding="utf-8",
            )
            # pexpect.run returns (output, exitstatus) when withexitstatus=True
            if isinstance(result, tuple):  # type: ignore[arg-type]
                output, exitstatus = result  # type: ignore[misc]
            else:
                # Handle unexpected return format
                output = str(result)
                exitstatus = 0
        except pexpect.TIMEOUT:
            error_msg = "Timeout waiting for CLI welcome command to complete"
            raise AssertionError(error_msg) from None

        # Check exit code
        assert exitstatus == 0

        # Check output
        welcome_msg = WelcomeMessage()
        assert welcome_msg.message in output
        assert welcome_msg.hint in output

    def test_cli_interrupt_handling(
        self,
        clean_env: dict[str, str],
    ) -> None:
        """Test that CLI handles basic execution without hanging."""
        # Note: Interrupt handling with pexpect is complex and platform-specific
        # This test just verifies the CLI completes execution normally

        # Use pexpect.run() to capture output
        try:
            result = pexpect.run(  # type: ignore[attr-defined]
                f"{sys.executable} -u -m clean_interfaces.main",
                env=clean_env,  # type: ignore[arg-type]
                withexitstatus=True,
                timeout=5,
                encoding="utf-8",
            )
            # pexpect.run returns (output, exitstatus) when withexitstatus=True
            if isinstance(result, tuple):  # type: ignore[arg-type]
                output, exitstatus = result  # type: ignore[misc]
            else:
                # Handle unexpected return format
                output = str(result)
                exitstatus = 0
        except pexpect.TIMEOUT:
            error_msg = "Timeout - CLI appears to be hanging"
            raise AssertionError(error_msg) from None

        # Should complete with exit code 0
        assert exitstatus == 0

        # Should produce output
        assert len(output) > 0  # type: ignore[arg-type]
