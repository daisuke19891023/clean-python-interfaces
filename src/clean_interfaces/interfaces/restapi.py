"""REST API interface implementation using FastAPI."""

from typing import Any

import uvicorn
import uvicorn.config
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse

from clean_interfaces.models.api import (
    HealthResponse,
    SwaggerAnalysisResponse,
    WelcomeResponse,
)
from clean_interfaces.utils.doc_generator import DocumentGenerator

from .base import BaseInterface


class RestAPIInterface(BaseInterface):
    """REST API Interface implementation."""

    def __init__(self) -> None:
        """Initialize the REST API interface."""
        super().__init__()  # Call BaseComponent's __init__ for logger initialization

        self.app = FastAPI(
            title="Clean Interfaces API",
            description="A clean interface REST API implementation",
            version="1.0.0",
        )

        # Initialize document generator for dynamic Swagger UI content
        self.doc_generator = DocumentGenerator()

        self._setup_routes()
        self.logger.info("RestAPI interface initialized")

    @property
    def name(self) -> str:
        """Get the interface name.

        Returns:
            str: The interface name

        """
        return "RestAPI"

    def _setup_routes(self) -> None:
        """Set up API routes."""
        self.logger.info("Setting up API routes")

        @self.app.get("/", response_class=RedirectResponse)
        async def root() -> str:  # type: ignore[misc]
            """Redirect root to API documentation."""
            return "/docs"  # type: ignore[return-value]

        @self.app.get("/health", response_model=HealthResponse)
        async def health() -> HealthResponse:  # type: ignore[misc]
            """Health check endpoint."""
            return HealthResponse()

        @self.app.get("/api/v1/welcome", response_model=WelcomeResponse)
        async def welcome() -> WelcomeResponse:  # type: ignore[misc]
            """Welcome message endpoint."""
            return WelcomeResponse()

        @self.app.get("/api/v1/swagger-ui", response_class=HTMLResponse)
        async def enhanced_swagger_ui() -> str:  # type: ignore[misc]
            """Enhanced Swagger UI with dynamic content generation."""
            schema_url = "/api/v1/swagger-ui/schema"
            html_content = self.doc_generator.generate_swagger_ui_html(schema_url)
            return html_content

        @self.app.get("/api/v1/swagger-ui/schema")
        async def swagger_ui_schema() -> dict[str, Any]:  # type: ignore[misc]
            """Enhanced OpenAPI schema with dynamic content metadata."""
            # Get the base OpenAPI schema from FastAPI
            base_schema = self.app.openapi()
            
            # Enhance it with dynamic content
            enhanced_schema = self.doc_generator.generate_enhanced_openapi_schema(base_schema)
            return enhanced_schema

        @self.app.get("/api/v1/swagger-ui/analysis", response_model=SwaggerAnalysisResponse)
        async def swagger_ui_analysis() -> SwaggerAnalysisResponse:  # type: ignore[misc]
            """Source code and documentation analysis for Swagger UI."""
            source_analysis = self.doc_generator.analyze_source_files()
            docs_analysis = self.doc_generator.analyze_documentation_files()
            
            analysis_summary = self.doc_generator.generate_analysis_summary(
                source_analysis, docs_analysis
            )
            
            return SwaggerAnalysisResponse(**analysis_summary)

    def run(self) -> None:
        """Run the REST API interface."""
        self.logger.info("Starting RestAPI server", host="0.0.0.0", port=8000)  # noqa: S104

        # Configure uvicorn logging to use structlog format
        log_config: dict[str, Any] = uvicorn.config.LOGGING_CONFIG.copy()
        log_config["formatters"]["default"]["fmt"] = "%(message)s"
        log_config["formatters"]["access"]["fmt"] = "%(message)s"

        # Disable uvicorn's default logging to avoid conflicts
        log_config["loggers"]["uvicorn"]["handlers"] = []
        log_config["loggers"]["uvicorn.access"]["handlers"] = []

        # Run the server
        uvicorn.run(
            self.app,
            host="0.0.0.0",  # noqa: S104
            port=8000,
            log_config=log_config,
            log_level="info",
        )
