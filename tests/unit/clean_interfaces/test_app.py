"""Tests for application module."""

from unittest.mock import MagicMock, patch

import pytest

from clean_interfaces.app import Application, create_app, run_app


class TestApplication:
    """Test Application class."""

    @patch("clean_interfaces.app.configure_logging")
    @patch("clean_interfaces.app.get_settings")
    @patch("clean_interfaces.app.get_interface_settings")
    @patch("clean_interfaces.app.InterfaceFactory")
    def test_application_initialization(
        self,
        mock_factory_class: MagicMock,
        mock_get_interface_settings: MagicMock,
        mock_get_settings: MagicMock,
        mock_configure_logging: MagicMock,
    ) -> None:
        """Test Application initialization."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_settings.log_level = "INFO"
        mock_settings.log_format = "json"
        mock_settings.log_file_path = None
        mock_get_settings.return_value = mock_settings

        mock_interface_settings = MagicMock()
        mock_interface_settings.model_dump.return_value = {"interface_type": "cli"}
        mock_get_interface_settings.return_value = mock_interface_settings

        mock_interface = MagicMock()
        mock_interface.name = "CLI"
        mock_factory = MagicMock()
        mock_factory.create_from_settings.return_value = mock_interface
        mock_factory_class.return_value = mock_factory

        # Create application
        app = Application()

        # Verify logging was configured
        mock_configure_logging.assert_called_once_with(
            log_level="INFO",
            log_format="json",
            log_file=None,
        )

        # Verify interface was created
        mock_factory.create_from_settings.assert_called_once()
        assert app.interface == mock_interface

    @patch("clean_interfaces.app.configure_logging")
    @patch("clean_interfaces.app.get_settings")
    @patch("clean_interfaces.app.InterfaceFactory")
    def test_application_run(
        self,
        mock_factory_class: MagicMock,
        mock_get_settings: MagicMock,
        mock_configure_logging: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test Application run method."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings

        mock_interface = MagicMock()
        mock_interface.name = "CLI"
        mock_factory = MagicMock()
        mock_factory.create_from_settings.return_value = mock_interface
        mock_factory_class.return_value = mock_factory

        # Create and run application
        app = Application()
        app.run()

        # Verify interface was run
        mock_interface.run.assert_called_once()

    @patch("clean_interfaces.app.configure_logging")
    @patch("clean_interfaces.app.get_settings")
    @patch("clean_interfaces.app.InterfaceFactory")
    def test_application_run_with_exception(
        self,
        mock_factory_class: MagicMock,
        mock_get_settings: MagicMock,
        mock_configure_logging: MagicMock,  # noqa: ARG002
    ) -> None:
        """Test Application run method with exception."""
        # Setup mocks
        mock_settings = MagicMock()
        mock_get_settings.return_value = mock_settings

        mock_interface = MagicMock()
        mock_interface.name = "CLI"
        mock_interface.run.side_effect = RuntimeError("Test error")
        mock_factory = MagicMock()
        mock_factory.create_from_settings.return_value = mock_interface
        mock_factory_class.return_value = mock_factory

        # Create application and verify exception is raised
        app = Application()
        with pytest.raises(RuntimeError, match="Test error"):
            app.run()

        # Verify interface was attempted to run
        mock_interface.run.assert_called_once()


def test_create_app() -> None:
    """Test create_app factory function."""
    with patch("clean_interfaces.app.Application") as mock_app_class:
        mock_app = MagicMock()
        mock_app_class.return_value = mock_app

        result = create_app()

        assert result == mock_app
        mock_app_class.assert_called_once()


def test_run_app() -> None:
    """Test run_app function."""
    with patch("clean_interfaces.app.create_app") as mock_create_app:
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app

        run_app()

        mock_create_app.assert_called_once()
        mock_app.run.assert_called_once()
