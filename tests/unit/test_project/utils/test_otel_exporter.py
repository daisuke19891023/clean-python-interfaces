"""Unit tests for OpenTelemetry exporter module."""

import json
import tempfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from structlog.types import EventDict

from test_project.utils.otel_exporter import (
    FileLogExporter,
    LogExporter,
    LogExporterFactory,
    OTLPLogExporter,
    StructlogOTelProcessor,
)
from test_project.utils.settings import LoggingSettings, OTelExportMode


class TestLogExporterInterface:
    """Test the LogExporter abstract base class."""

    def test_log_exporter_is_abstract(self) -> None:
        """Test that LogExporter cannot be instantiated."""
        with pytest.raises(TypeError):
            LogExporter()  # type: ignore[abstract]

    def test_log_exporter_requires_export_method(self) -> None:
        """Test that subclasses must implement export method."""

        class IncompleteExporter(LogExporter):
            pass

        with pytest.raises(TypeError):
            IncompleteExporter()  # type: ignore[abstract]

    def test_log_exporter_requires_shutdown_method(self) -> None:
        """Test that subclasses must implement shutdown method."""

        class IncompleteExporter(LogExporter):
            def export(self, event_dict: EventDict) -> None:
                pass

        with pytest.raises(TypeError):
            IncompleteExporter()  # type: ignore[abstract]


class TestFileLogExporter:
    """Test FileLogExporter implementation."""

    def test_file_exporter_creates_log_file(self) -> None:
        """Test that FileLogExporter creates log file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "test.log"
            exporter = FileLogExporter(str(log_path))

            event: EventDict = {
                "event": "Test message",
                "level": "info",
                "timestamp": "2024-01-01T00:00:00Z",
            }

            exporter.export(event)

            assert log_path.exists()
            content = log_path.read_text()
            log_entry: dict[str, Any] = json.loads(content.strip())
            assert log_entry["event"] == "Test message"

    def test_file_exporter_appends_to_existing_file(self) -> None:
        """Test that FileLogExporter appends to existing file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "test.log"
            exporter = FileLogExporter(str(log_path))

            # Write first event
            event1: EventDict = {"event": "First", "level": "info"}
            exporter.export(event1)

            # Write second event
            event2: EventDict = {"event": "Second", "level": "error"}
            exporter.export(event2)

            content = log_path.read_text()
            lines = content.strip().split("\n")
            assert len(lines) == 2

            log1: dict[str, Any] = json.loads(lines[0])
            log2: dict[str, Any] = json.loads(lines[1])
            assert log1["event"] == "First"
            assert log2["event"] == "Second"

    def test_file_exporter_handles_invalid_path(self) -> None:
        """Test FileLogExporter handles invalid file paths gracefully."""
        # Use an invalid path (directory that doesn't exist)
        exporter = FileLogExporter("/nonexistent/path/test.log")

        # Should not raise exception, but log error internally
        event: EventDict = {"event": "Test", "level": "info"}
        exporter.export(event)  # Should handle error gracefully

    def test_file_exporter_shutdown(self) -> None:
        """Test FileLogExporter shutdown method."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_path = Path(temp_dir) / "test.log"
            exporter = FileLogExporter(str(log_path))

            # Shutdown should complete without error
            exporter.shutdown()


class TestOTLPLogExporter:
    """Test OTLPLogExporter implementation."""

    def test_otlp_exporter_initialization(self) -> None:
        """Test OTLPLogExporter initialization."""
        with (
            patch("test_project.utils.otel_exporter._otel_available", new=True),
            patch(
                "test_project.utils.otel_exporter.socket.socket",
            ) as mock_socket_class,
            patch("test_project.utils.otel_exporter.Resource") as mock_resource_class,
            patch(
                "test_project.utils.otel_exporter.BatchLogRecordProcessor",
            ) as mock_batch_processor_class,
            patch(
                "test_project.utils.otel_exporter.LoggerProvider",
            ) as mock_logger_provider_class,
            patch(
                "test_project.utils.otel_exporter.OTLPLogsExporter",
            ) as mock_otlp_class,
        ):
            # Mock successful connection
            mock_socket = MagicMock()
            mock_socket.connect_ex.return_value = 0  # Success
            mock_socket_class.return_value = mock_socket

            # Setup other mocks
            mock_otlp = MagicMock()
            mock_otlp_class.return_value = mock_otlp
            mock_provider = MagicMock()
            mock_logger_provider_class.return_value = mock_provider
            mock_processor = MagicMock()
            mock_batch_processor_class.return_value = mock_processor
            mock_resource = MagicMock()
            mock_resource_class.create.return_value = mock_resource

            _ = OTLPLogExporter(
                endpoint="http://localhost:4317",
                service_name="test-service",
                timeout=5000,
            )

            # Verify OTLP exporter was created with correct parameters
            mock_otlp_class.assert_called_once()
            call_kwargs = mock_otlp_class.call_args.kwargs
            assert call_kwargs["endpoint"] == "http://localhost:4317"
            assert call_kwargs["timeout"] == 5

    @patch("test_project.utils.otel_exporter.socket.socket")
    @patch("test_project.utils.otel_exporter.OTLPLogsExporter")
    @patch("test_project.utils.otel_exporter.LoggerProvider")
    def test_otlp_exporter_export(
        self,
        mock_logger_provider_class: MagicMock,
        mock_otlp_class: MagicMock,
        mock_socket_class: MagicMock,
    ) -> None:
        """Test OTLPLogExporter export functionality."""
        # Mock successful connection
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 0  # Success
        mock_socket_class.return_value = mock_socket

        # Setup mocks
        mock_otlp = MagicMock()
        mock_otlp_class.return_value = mock_otlp

        mock_logger = MagicMock()
        mock_provider = MagicMock()
        mock_provider.get_logger.return_value = mock_logger
        mock_logger_provider_class.return_value = mock_provider

        exporter = OTLPLogExporter(
            endpoint="http://localhost:4317",
            service_name="test-service",
        )

        # Export an event
        event: EventDict = {
            "event": "Test OTLP message",
            "level": "warning",
            "user_id": "user123",
        }

        exporter.export(event)

        # Verify logger was called
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert call_args.args[0] == "Test OTLP message"
        assert call_args.kwargs["extra"]["attributes"]["user_id"] == "user123"

    @patch("test_project.utils.otel_exporter.socket.socket")
    @patch("test_project.utils.otel_exporter.OTLPLogsExporter")
    def test_otlp_exporter_shutdown(
        self,
        mock_otlp_class: MagicMock,
        mock_socket_class: MagicMock,
    ) -> None:
        """Test OTLPLogExporter shutdown."""
        # Mock successful connection
        mock_socket = MagicMock()
        mock_socket.connect_ex.return_value = 0  # Success
        mock_socket_class.return_value = mock_socket

        mock_otlp = MagicMock()
        mock_otlp_class.return_value = mock_otlp

        # Need to mock LoggerProvider to test shutdown
        with patch(
            "test_project.utils.otel_exporter.LoggerProvider",
        ) as mock_provider_class:
            mock_provider = MagicMock()
            mock_provider_class.return_value = mock_provider

            exporter = OTLPLogExporter(endpoint="http://localhost:4317")
            exporter.shutdown()

            # Verify shutdown was called on provider
            mock_provider.shutdown.assert_called_once()


class TestLogExporterFactory:
    """Test LogExporterFactory implementation."""

    def test_factory_creates_file_exporter(self) -> None:
        """Test factory creates FileLogExporter for file mode."""
        settings = LoggingSettings(
            otel_logs_export_mode=OTelExportMode.FILE,
            log_file_path="/tmp/test.log",  # noqa: S108
        )

        exporters = LogExporterFactory.create(settings)

        assert len(exporters) == 1
        assert isinstance(exporters[0], FileLogExporter)

    def test_factory_creates_otlp_exporter(self) -> None:
        """Test factory creates OTLPLogExporter for otlp mode."""
        settings = LoggingSettings(
            otel_logs_export_mode=OTelExportMode.OTLP,
            otel_endpoint="http://otel:4317",
            otel_service_name="test-svc",
        )

        with patch("test_project.utils.otel_exporter.OTLPLogsExporter"):
            exporters = LogExporterFactory.create(settings)

        assert len(exporters) == 1
        assert isinstance(exporters[0], OTLPLogExporter)

    def test_factory_creates_both_exporters(self) -> None:
        """Test factory creates both exporters for both mode."""
        settings = LoggingSettings(
            otel_logs_export_mode=OTelExportMode.BOTH,
            log_file_path="/tmp/test.log",  # noqa: S108
            otel_endpoint="http://otel:4317",
        )

        with patch("test_project.utils.otel_exporter.OTLPLogsExporter"):
            exporters = LogExporterFactory.create(settings)

        assert len(exporters) == 2
        assert any(isinstance(exp, FileLogExporter) for exp in exporters)
        assert any(isinstance(exp, OTLPLogExporter) for exp in exporters)

    def test_factory_returns_empty_for_file_mode_without_path(self) -> None:
        """Test factory returns empty list when file path not provided."""
        settings = LoggingSettings(
            otel_logs_export_mode=OTelExportMode.FILE,
            log_file_path=None,
        )

        exporters = LogExporterFactory.create(settings)
        assert len(exporters) == 0


class TestStructlogOTelProcessor:
    """Test StructlogOTelProcessor implementation."""

    def test_processor_with_no_exporters(self) -> None:
        """Test processor handles no exporters gracefully."""
        processor = StructlogOTelProcessor([])

        event: EventDict = {"event": "Test", "level": "info"}
        result = processor(None, "info", event)

        # Should return event unchanged
        assert result == event

    def test_processor_with_single_exporter(self) -> None:
        """Test processor with single exporter."""
        mock_exporter = MagicMock(spec=LogExporter)
        processor = StructlogOTelProcessor([mock_exporter])

        event: EventDict = {"event": "Test message", "level": "info"}
        result = processor(None, "info", event)

        # Verify exporter was called
        mock_exporter.export.assert_called_once_with(event)
        assert result == event

    def test_processor_with_multiple_exporters(self) -> None:
        """Test processor with multiple exporters."""
        mock_exporter1 = MagicMock(spec=LogExporter)
        mock_exporter2 = MagicMock(spec=LogExporter)
        processor = StructlogOTelProcessor([mock_exporter1, mock_exporter2])

        event: EventDict = {"event": "Multi export", "level": "error"}
        result = processor(None, "error", event)

        # Verify both exporters were called
        mock_exporter1.export.assert_called_once_with(event)
        mock_exporter2.export.assert_called_once_with(event)
        assert result == event

    def test_processor_handles_exporter_errors(self) -> None:
        """Test processor continues when exporter raises error."""
        # Create exporter that raises exception
        failing_exporter = MagicMock(spec=LogExporter)
        failing_exporter.export.side_effect = Exception("Export failed")

        working_exporter = MagicMock(spec=LogExporter)

        processor = StructlogOTelProcessor([failing_exporter, working_exporter])

        event: EventDict = {"event": "Error test", "level": "warning"}
        result = processor(None, "warning", event)

        # Both exporters should be called despite first one failing
        failing_exporter.export.assert_called_once()
        working_exporter.export.assert_called_once()
        assert result == event

    def test_processor_shutdown(self) -> None:
        """Test processor shutdown calls all exporter shutdowns."""
        mock_exporter1 = MagicMock(spec=LogExporter)
        mock_exporter2 = MagicMock(spec=LogExporter)
        processor = StructlogOTelProcessor([mock_exporter1, mock_exporter2])

        processor.shutdown()

        # Verify both exporters were shut down
        mock_exporter1.shutdown.assert_called_once()
        mock_exporter2.shutdown.assert_called_once()
