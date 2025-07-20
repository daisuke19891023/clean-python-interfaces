"""Tests for RestAPI interface implementation."""

from unittest.mock import MagicMock, patch

from fastapi import FastAPI

from clean_interfaces.interfaces.base import BaseInterface
from clean_interfaces.interfaces.restapi import RestAPIInterface


class TestRestAPIInterface:
    """Test RestAPI interface functionality."""

    def test_restapi_interface_inherits_base(self) -> None:
        """Test that RestAPIInterface inherits from BaseInterface."""
        assert issubclass(RestAPIInterface, BaseInterface)

    def test_restapi_interface_has_name(self) -> None:
        """Test that RestAPIInterface has correct name."""
        api = RestAPIInterface()
        assert api.name == "RestAPI"

    def test_restapi_interface_has_fastapi_app(self) -> None:
        """Test that RestAPIInterface has FastAPI app."""
        api = RestAPIInterface()
        assert hasattr(api, "app")
        assert isinstance(api.app, FastAPI)

    def test_restapi_interface_app_title(self) -> None:
        """Test that FastAPI app has correct title."""
        api = RestAPIInterface()
        assert api.app.title == "Clean Interfaces API"
        assert api.app.version == "1.0.0"

    def test_restapi_interface_has_endpoints(self) -> None:
        """Test that RestAPIInterface has required endpoints."""
        api = RestAPIInterface()
        routes = [route.path for route in api.app.routes]  # type: ignore[attr-defined]
        assert "/health" in routes
        assert "/api/v1/welcome" in routes
        assert "/" in routes  # Root redirect

    @patch("clean_interfaces.interfaces.restapi.uvicorn")
    def test_restapi_run_method(self, mock_uvicorn: MagicMock) -> None:
        """Test RestAPI run method configures uvicorn."""
        api = RestAPIInterface()

        # Mock to prevent actual server start
        api.run()

        # Verify uvicorn.run was called with correct parameters
        mock_uvicorn.run.assert_called_once()
        call_args = mock_uvicorn.run.call_args

        # Check app parameter
        assert call_args[0][0] == api.app

        # Check kwargs
        kwargs = call_args[1]
        assert kwargs.get("host") == "0.0.0.0"  # noqa: S104
        assert kwargs.get("port") == 8000
        assert kwargs.get("log_config") is not None

    def test_restapi_interface_initialization_logs(self) -> None:
        """Test that RestAPIInterface logs initialization."""
        with patch("clean_interfaces.base.get_logger") as mock_get_logger:
            # Setup mock logger
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Create instance which will trigger logging
            RestAPIInterface()

            # Check that logger was used during initialization
            assert mock_logger.info.called
