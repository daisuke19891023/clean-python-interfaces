"""Fixtures and utilities for CLI E2E tests using pexpect."""

import os
import sys
from collections.abc import Generator

import pexpect
import pytest


class CLIRunner:
    """Helper class for running CLI commands with pexpect."""

    def __init__(self, timeout: int = 10) -> None:
        """Initialize the CLI runner.

        Args:
            timeout: Default timeout for expect operations in seconds

        """
        self.timeout = timeout
        self.process: pexpect.spawn | None = None

    def run(
        self,
        command: str | None = None,
        args: list[str] | None = None,
        env: dict[str, str] | None = None,
    ) -> pexpect.spawn:
        """Run a CLI command.

        Args:
            command: Command to run (defaults to clean-interfaces)
            args: Command line arguments
            env: Environment variables

        Returns:
            pexpect.spawn[str]: The spawned process

        """
        if command is None:
            # Use the installed script entry point
            command = sys.executable
            base_args = ["-m", "clean_interfaces.main"]
        else:
            base_args = []

        if args is None:
            args = []

        full_args = base_args + args

        # Merge environment variables
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)

        # Spawn the process
        # Note: pexpect accepts dict[str, str] despite type hints
        self.process = pexpect.spawn(
            command,
            args=full_args,
            env=cmd_env if env else None,
            encoding="utf-8",
            timeout=self.timeout,
        )

        return self.process

    def expect(self, pattern: str | list[str], timeout: int | None = None) -> int:
        """Expect a pattern in the output.

        Args:
            pattern: Pattern(s) to expect
            timeout: Timeout override

        Returns:
            int: Index of matched pattern

        """
        if self.process is None:
            msg = "No process is running"
            raise RuntimeError(msg)

        return self.process.expect(pattern, timeout=timeout or self.timeout)

    def send(self, text: str) -> None:
        """Send text to the process.

        Args:
            text: Text to send

        """
        if self.process is None:
            msg = "No process is running"
            raise RuntimeError(msg)

        self.process.send(text)

    def sendline(self, line: str = "") -> None:
        """Send a line to the process.

        Args:
            line: Line to send (newline is added automatically)

        """
        if self.process is None:
            msg = "No process is running"
            raise RuntimeError(msg)

        self.process.sendline(line)

    def close(self) -> None:
        """Close the process."""
        if self.process:
            self.process.close()
            self.process = None

    @property
    def output(self) -> str:
        """Get the current output buffer.

        Returns:
            str: The output buffer content

        """
        if self.process is None:
            return ""
        before = self.process.before
        return str(before) if before is not None else ""

    @property
    def exitstatus(self) -> int | None:
        """Get the exit status of the process.

        Returns:
            int | None: Exit status or None if still running

        """
        if self.process is None:
            return None
        return self.process.exitstatus


@pytest.fixture
def cli_runner() -> Generator[CLIRunner, None, None]:
    """Provide a CLI runner for tests.

    Yields:
        CLIRunner: A CLI runner instance

    """
    runner = CLIRunner()
    yield runner
    runner.close()


@pytest.fixture
def clean_env() -> dict[str, str]:
    """Provide a clean environment for CLI tests.

    Returns:
        dict[str, str]: Clean environment variables

    """
    # Start with minimal environment
    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "USER": os.environ.get("USER", ""),
        # Disable any color/formatting that might interfere with tests
        "NO_COLOR": "1",
        "TERM": "dumb",
        # Set log level to ERROR to reduce output
        "LOG_LEVEL": "ERROR",
    }

    # Add Python path to ensure our package is importable
    if "PYTHONPATH" in os.environ:
        env["PYTHONPATH"] = os.environ["PYTHONPATH"]

    return env
