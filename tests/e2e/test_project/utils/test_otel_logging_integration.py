"""End-to-end tests for OpenTelemetry logging integration."""

import json
import os
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, ClassVar

import pytest

from test_project.utils.logger import configure_logging, get_logger
from test_project.utils.settings import LoggingSettings


class MockOTLPServer:
    """Mock OTLP server for testing log export functionality."""

    def __init__(self, port: int = 4317) -> None:
        """Initialize mock OTLP server."""
        self.port = port
        self.server: HTTPServer | None = None
        self.received_data: list[bytes] = []
        self.server_thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the mock server."""
        handler = self._create_handler()
        # Try the requested port, if busy, try a few others
        ports_to_try = [
            self.port,
            self.port + 100,
            self.port + 200,
            self.port + 300,
        ]
        for port in ports_to_try:
            try:
                self.server = HTTPServer(("localhost", port), handler)
                self.port = port  # Update to actual port used
                break
            except OSError as e:
                if port == ports_to_try[-1]:
                    msg = f"Could not bind to any port in {ports_to_try}"
                    raise OSError(msg) from e
                continue

        if self.server:
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            time.sleep(0.1)  # Give server time to start

    def stop(self) -> None:
        """Stop the mock server."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        if self.server_thread:
            self.server_thread.join(timeout=1)

    def _create_handler(self) -> type[BaseHTTPRequestHandler]:
        """Create request handler class with access to server instance."""
        server_instance = self

        class Handler(BaseHTTPRequestHandler):
            received_data: ClassVar[list[bytes]] = server_instance.received_data

            def do_post(self) -> None:
                """Handle POST requests with PEP 8 compliant naming."""
                content_length = int(self.headers.get("Content-Length", 0))
                post_data = self.rfile.read(content_length)
                self.received_data.append(post_data)

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"success": true}')

            def do_POST(self) -> None:
                """Handle POST requests (required by BaseHTTPRequestHandler)."""
                self.do_post()

            def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
                """Suppress server logging."""

        return Handler


class TestOpenTelemetryLoggingIntegration:
    """End-to-end tests for complete OpenTelemetry logging flow."""

    def test_complete_otel_logging_flow_with_local_file(self) -> None:
        """Test complete flow: env config → log generation → local file output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "app.log"

            # Set environment variables for local file logging
            os.environ["OTEL_LOGS_EXPORT_MODE"] = "file"
            os.environ["LOG_FILE_PATH"] = str(log_file)
            os.environ["LOG_LEVEL"] = "INFO"
            os.environ["LOG_FORMAT"] = "json"

            try:
                # Configure logging with OpenTelemetry support
                settings = LoggingSettings()
                configure_logging(
                    log_level=settings.log_level,
                    log_format=settings.log_format,
                    log_file=settings.log_file_path,
                    otel_export_enabled=settings.otel_export_enabled,
                    otel_endpoint=settings.otel_endpoint,
                )

                # Create logger and generate logs
                logger = get_logger("e2e_test")
                logger.info("Test message", user_id="test_user", action="test_action")
                logger.error("Error message", error_code="E001")

                # Verify logs were written to file
                assert log_file.exists()
                content = log_file.read_text()
                lines = [line for line in content.strip().split("\n") if line]
                assert len(lines) == 2

                # Verify log structure
                log1: dict[str, Any] = json.loads(lines[0])
                assert log1["event"] == "Test message"
                assert log1["user_id"] == "test_user"
                assert log1["action"] == "test_action"
                assert log1["level"] == "info"

                log2: dict[str, Any] = json.loads(lines[1])
                assert log2["event"] == "Error message"
                assert log2["error_code"] == "E001"
                assert log2["level"] == "error"

            finally:
                # Clean up environment variables
                for key in [
                    "OTEL_LOGS_EXPORT_MODE",
                    "LOG_FILE_PATH",
                    "LOG_LEVEL",
                    "LOG_FORMAT",
                ]:
                    os.environ.pop(key, None)

    @pytest.mark.skip(reason="Mock OTLP server causing port conflicts in CI")
    def test_complete_otel_logging_flow_with_otlp_export(self) -> None:
        """Test complete flow: environment config → log generation → OTLP export."""
        mock_server = MockOTLPServer(port=4318)
        mock_server.start()

        try:
            # Set environment variables for OTLP export
            os.environ["OTEL_LOGS_EXPORT_MODE"] = "otlp"
            os.environ["OTEL_ENDPOINT"] = f"http://localhost:{mock_server.port}"
            os.environ["LOG_LEVEL"] = "DEBUG"
            os.environ["LOG_FORMAT"] = "json"

            # Configure logging with OpenTelemetry support
            settings = LoggingSettings()
            configure_logging(
                log_level=settings.log_level,
                log_format=settings.log_format,
                otel_export_enabled=settings.otel_export_enabled,
                otel_endpoint=settings.otel_endpoint,
            )

            # Create logger and generate logs
            logger = get_logger("otlp_test")
            logger.debug("Debug message", debug_info="test")
            logger.info("Info message", request_id="req_123")
            logger.warning("Warning message", warning_type="performance")

            # Give time for logs to be exported
            time.sleep(0.5)

            # Verify server received data
            assert len(mock_server.received_data) > 0

            # Basic validation that data was sent
            # (Actual OTLP protocol validation would be more complex)
            for data in mock_server.received_data:
                assert len(data) > 0

        finally:
            mock_server.stop()
            # Clean up environment variables
            for key in [
                "OTEL_LOGS_EXPORT_MODE",
                "OTEL_ENDPOINT",
                "LOG_LEVEL",
                "LOG_FORMAT",
            ]:
                os.environ.pop(key, None)

    @pytest.mark.skip(reason="Mock OTLP server causing port conflicts in CI")
    def test_otel_logging_with_mixed_configuration(self) -> None:
        """Test OpenTelemetry logging with both file and OTLP export."""
        mock_server = MockOTLPServer(port=4319)
        mock_server.start()

        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "mixed.log"

            try:
                # Set environment for mixed mode
                os.environ["OTEL_LOGS_EXPORT_MODE"] = "both"
                os.environ["OTEL_ENDPOINT"] = f"http://localhost:{mock_server.port}"
                os.environ["LOG_FILE_PATH"] = str(log_file)
                os.environ["LOG_LEVEL"] = "INFO"

                # Configure logging
                settings = LoggingSettings()
                configure_logging(
                    log_level=settings.log_level,
                    log_format=settings.log_format,
                    log_file=settings.log_file_path,
                    otel_export_enabled=settings.otel_export_enabled,
                    otel_endpoint=settings.otel_endpoint,
                )

                # Generate logs
                logger = get_logger("mixed_test")
                logger.info("Mixed mode test", mode="both")
                logger.error("Error in mixed mode", severity="high")

                # Give time for async export
                time.sleep(0.5)

                # Verify file output
                assert log_file.exists()
                content = log_file.read_text()
                assert "Mixed mode test" in content
                assert "Error in mixed mode" in content

                # Verify OTLP export
                assert len(mock_server.received_data) > 0

            finally:
                mock_server.stop()
                for key in [
                    "OTEL_LOGS_EXPORT_MODE",
                    "OTEL_ENDPOINT",
                    "LOG_FILE_PATH",
                    "LOG_LEVEL",
                ]:
                    os.environ.pop(key, None)

    def test_otel_logging_graceful_fallback(self) -> None:
        """Test graceful fallback when OTLP endpoint is unavailable."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "fallback.log"

            try:
                # Configure with unavailable OTLP endpoint
                os.environ["OTEL_LOGS_EXPORT_MODE"] = "both"
                os.environ["OTEL_ENDPOINT"] = "http://localhost:9999"  # Non-existent
                os.environ["LOG_FILE_PATH"] = str(log_file)
                os.environ["LOG_LEVEL"] = "WARNING"
                os.environ["OTEL_EXPORT_TIMEOUT"] = "1000"  # 1 second timeout for tests

                # Configure logging
                settings = LoggingSettings()
                configure_logging(
                    log_level=settings.log_level,
                    log_format=settings.log_format,
                    log_file=settings.log_file_path,
                    otel_export_enabled=settings.otel_export_enabled,
                    otel_endpoint=settings.otel_endpoint,
                )

                # Generate logs - should work despite OTLP failure
                logger = get_logger("fallback_test")
                logger.warning("Fallback test warning")
                logger.error("Fallback test error")

                # Verify logs still written to file
                assert log_file.exists()
                content = log_file.read_text()
                assert "Fallback test warning" in content
                assert "Fallback test error" in content

            finally:
                for key in [
                    "OTEL_LOGS_EXPORT_MODE",
                    "OTEL_ENDPOINT",
                    "LOG_FILE_PATH",
                    "LOG_LEVEL",
                    "OTEL_EXPORT_TIMEOUT",
                ]:
                    os.environ.pop(key, None)
