"""Application builder for clean interfaces.

This module handles the construction and configuration of the application,
including interface selection, storage configuration, and future database setup.
"""

from clean_interfaces.interfaces.factory import InterfaceFactory
from clean_interfaces.utils.logger import configure_logging, get_logger
from clean_interfaces.utils.settings import get_interface_settings, get_settings


class Application:
    """Main application class that orchestrates components."""

    def __init__(self) -> None:
        """Initialize the application."""
        # Configure logging first
        settings = get_settings()
        configure_logging(
            log_level=settings.log_level,
            log_format=settings.log_format,
            log_file=settings.log_file_path,
        )
        self.logger = get_logger(__name__)

        # Initialize interface
        self.interface_factory = InterfaceFactory()
        self.interface = self.interface_factory.create_from_settings()

        self.logger.info(
            "Application initialized",
            interface=self.interface.name,
            settings=get_interface_settings().model_dump(),
        )

    def run(self) -> None:
        """Run the application."""
        self.logger.info("Starting application", interface=self.interface.name)

        try:
            self.interface.run()
        except Exception as e:
            self.logger.error("Application error", error=str(e))
            raise
        finally:
            self.logger.info("Application shutting down")


def create_app() -> Application:
    """Create an application instance.

    Returns:
        Application: Configured application instance

    """
    return Application()


def run_app() -> None:
    """Create and run the application."""
    app = create_app()
    app.run()
