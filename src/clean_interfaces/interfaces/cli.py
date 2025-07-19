"""CLI interface implementation using Typer."""

import typer
from rich.console import Console

from clean_interfaces.models.io import WelcomeMessage

from .base import BaseInterface

console = Console()


class CLIInterface(BaseInterface):
    """Command Line Interface implementation."""

    def __init__(self) -> None:
        """Initialize the CLI interface."""
        super().__init__()  # Call BaseComponent's __init__ for logger initialization
        self.app = typer.Typer(
            name="clean-interfaces",
            help="Clean Interfaces CLI",
            add_completion=False,
        )
        self._setup_commands()

    @property
    def name(self) -> str:
        """Get the interface name.

        Returns:
            str: The interface name

        """
        return "CLI"

    def _setup_commands(self) -> None:
        """Set up CLI commands."""
        # Set the default command to welcome
        self.app.command()(self.welcome)

    def welcome(self) -> None:
        """Display welcome message."""
        msg = WelcomeMessage()
        console.print(f"[bold green]{msg.message}[/bold green]")
        console.print(f"[dim]{msg.hint}[/dim]")

    def run(self) -> None:
        """Run the CLI interface."""
        # If no arguments provided, show welcome
        import sys

        if len(sys.argv) == 1:
            self.welcome()
        else:
            self.app()
