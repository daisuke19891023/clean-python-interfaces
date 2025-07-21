"""Tests for CLI interface implementation."""

from unittest.mock import MagicMock, patch

import typer

from clean_interfaces.interfaces.base import BaseInterface
from clean_interfaces.interfaces.cli import CLIInterface


class TestCLIInterface:
    """Test CLI interface functionality."""

    def test_cli_interface_inherits_base(self) -> None:
        """Test that CLIInterface inherits from BaseInterface."""
        assert issubclass(CLIInterface, BaseInterface)

    def test_cli_interface_has_name(self) -> None:
        """Test that CLIInterface has correct name."""
        cli = CLIInterface()
        assert cli.name == "CLI"

    def test_cli_interface_has_typer_app(self) -> None:
        """Test that CLIInterface has Typer app."""
        cli = CLIInterface()
        assert hasattr(cli, "app")
        assert isinstance(cli.app, typer.Typer)

    def test_cli_welcome_command(self) -> None:
        """Test CLI welcome command functionality."""
        cli = CLIInterface()

        # Mock the console output
        with patch("clean_interfaces.interfaces.cli.console") as mock_console:
            cli.welcome()

            # Check that welcome message was printed (should be called twice)
            assert mock_console.print.call_count == 2
            # First call is the welcome message
            first_call = mock_console.print.call_args_list[0][0]
            assert "Welcome to Clean Interfaces!" in str(first_call)
            # Second call is the hint
            second_call = mock_console.print.call_args_list[1][0]
            assert "Type --help for more information" in str(second_call)

    def test_cli_run_method(self) -> None:
        """Test CLI run method executes typer app."""
        cli = CLIInterface()

        # Mock the typer app
        cli.app = MagicMock()

        cli.run()

        cli.app.assert_called_once()

    def test_help_command_exists(self) -> None:
        """Test that help command is registered."""
        cli = CLIInterface()
        
        # Check that help command is in the app's commands
        commands = [cmd.name for cmd in cli.app.registered_commands.values()]
        assert "help" in commands

    def test_help_generation_methods(self) -> None:
        """Test help generation logic."""
        cli = CLIInterface()
        
        # Test that help generation method exists
        assert hasattr(cli, "help")
        assert callable(cli.help)

    def test_command_discovery(self) -> None:
        """Test command discovery functionality."""
        cli = CLIInterface()
        
        # Test that CLI can discover its own commands
        commands = cli._get_available_commands()
        assert isinstance(commands, dict)
        assert "welcome" in commands
        assert "help" in commands

    def test_help_formatting(self) -> None:
        """Test help text formatting."""
        cli = CLIInterface()
        
        # Mock the console output
        with patch("clean_interfaces.interfaces.cli.console") as mock_console:
            cli.help()
            
            # Check that help was displayed
            assert mock_console.print.called
            
            # Get the call args to check content
            call_args = mock_console.print.call_args_list
            output_text = str(call_args)
            
            # Check for expected help content
            assert "Available Commands:" in output_text or any("Available Commands:" in str(call) for call in call_args)

    def test_help_with_specific_command(self) -> None:
        """Test help for specific command."""
        cli = CLIInterface()
        
        # Mock the console output
        with patch("clean_interfaces.interfaces.cli.console") as mock_console:
            cli.help("welcome")
            
            # Check that specific command help was displayed
            assert mock_console.print.called
