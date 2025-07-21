"""CLI interface implementation using Typer."""

import typer
from rich.console import Console

from clean_interfaces.models.io import WelcomeMessage

from .base import BaseInterface

# Configure console for better test compatibility
# Force terminal mode even in non-TTY environments
console = Console(force_terminal=True, force_interactive=False)


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
        self.app.command(name="welcome")(self.welcome)
        
        # Add help command for dynamic help generation
        self.app.command(name="help")(self.help)

        # Add a callback that shows welcome when no command is specified
        self.app.callback(invoke_without_command=True)(self._main_callback)

    def _main_callback(self, ctx: typer.Context) -> None:  # pragma: no cover
        """Run when no subcommand is provided."""
        if ctx.invoked_subcommand is None:
            self.welcome()
            # Ensure we exit cleanly after showing welcome
            raise typer.Exit(0)

    def welcome(self) -> None:
        """Display welcome message."""
        msg = WelcomeMessage()
        # Use console for output (configured for E2E test compatibility)
        console.print(msg.message)
        console.print(msg.hint)
        # Force flush to ensure output is visible
        console.file.flush()

    def help(self, command_name: str | None = None) -> None:
        """Show available commands and their usage.
        
        Args:
            command_name: Optional specific command to show help for
        """
        if command_name:
            self._show_command_help(command_name)
        else:
            self._show_all_commands_help()

    def _get_available_commands(self) -> dict[str, str]:
        """Get all available commands with their descriptions.
        
        Returns:
            dict: Mapping of command names to descriptions
        """
        commands = {}
        
        # Get commands from the Typer app
        for command in self.app.registered_commands.values():
            command_name = command.name or "unknown"
            # Get the command description from the function docstring
            description = self._get_command_description(command.callback)
            commands[command_name] = description
            
        return commands

    def _get_command_description(self, command_func: object) -> str:
        """Extract description from command function.
        
        Args:
            command_func: The command function
            
        Returns:
            str: The command description
        """
        if hasattr(command_func, "__doc__") and command_func.__doc__:
            # Get first line of docstring as description
            return command_func.__doc__.strip().split('\n')[0]
        return "No description available"

    def _show_all_commands_help(self) -> None:
        """Display help for all available commands."""
        console.print("[bold blue]Available Commands:[/bold blue]")
        console.print()
        
        commands = self._get_available_commands()
        
        for command_name, description in commands.items():
            console.print(f"  [green]{command_name}[/green] - {description}")
        
        console.print()
        console.print("[dim]Use 'help <command>' for detailed help on a specific command.[/dim]")
        console.file.flush()

    def _show_command_help(self, command_name: str) -> None:
        """Display help for a specific command.
        
        Args:
            command_name: Name of the command to show help for
        """
        commands = self._get_available_commands()
        
        if command_name not in commands:
            console.print(f"[red]Error:[/red] Unknown command '{command_name}'")
            console.print("Use 'help' to see all available commands.")
            console.file.flush()
            return
            
        description = commands[command_name]
        console.print(f"[bold blue]Command:[/bold blue] {command_name}")
        console.print(f"[bold blue]Description:[/bold blue] {description}")
        console.file.flush()

    def run(self) -> None:
        """Run the CLI interface."""
        # Let Typer handle the command parsing
        self.app()
