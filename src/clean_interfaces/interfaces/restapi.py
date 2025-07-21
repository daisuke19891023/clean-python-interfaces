"""REST API interface implementation using FastAPI."""

import time
from typing import Any

import uvicorn
import uvicorn.config
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse

from clean_interfaces.adapters.async_adapter import AsyncFunctionAdapter
from clean_interfaces.models.api import HealthResponse, WelcomeResponse
from clean_interfaces.models.function import (
    FunctionExecuteRequest,
    FunctionExecuteResponse,
    FunctionListResponse,
    FunctionRegisterRequest,
    FunctionRegisterResponse,
)
from clean_interfaces.registry.function_registry import (
    FunctionRegistry,
    FunctionRegistryError,
)

from .base import BaseInterface


class RestAPIInterface(BaseInterface):
    """REST API Interface implementation."""

    def __init__(self) -> None:
        """Initialize the REST API interface."""
        super().__init__()  # Call BaseComponent's __init__ for logger initialization

        self.app = FastAPI(
            title="Clean Interfaces API",
            description="A clean interface REST API implementation with async adaptation",
            version="1.0.0",
        )

        # Initialize function registry and async adapter
        self.function_registry = FunctionRegistry()
        self.async_adapter = AsyncFunctionAdapter()

        self._setup_routes()
        self.logger.info("RestAPI interface initialized with async adaptation")

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

        @self.app.post("/api/v1/functions/register", response_model=FunctionRegisterResponse, status_code=201)
        async def register_function(request: FunctionRegisterRequest) -> FunctionRegisterResponse:  # type: ignore[misc]
            """Register a new function."""
            try:
                function_info = self.function_registry.register_function(
                    request.name, request.code, request.is_async
                )
                self.logger.info(
                    "Function registered successfully",
                    function_name=request.name,
                    is_async=request.is_async,
                )
                return FunctionRegisterResponse(
                    name=function_info.name,
                    is_async=function_info.is_async,
                    registered_at=function_info.registered_at,
                )
            except FunctionRegistryError as e:
                if "already exists" in str(e):
                    raise HTTPException(status_code=409, detail=str(e)) from e
                else:
                    raise HTTPException(status_code=400, detail=str(e)) from e

        @self.app.get("/api/v1/functions", response_model=FunctionListResponse)
        async def list_functions() -> FunctionListResponse:  # type: ignore[misc]
            """List all registered functions."""
            functions = self.function_registry.list_functions()
            function_list = [
                {
                    "name": f.name,
                    "is_async": f.is_async,
                    "registered_at": f.registered_at,
                }
                for f in functions
            ]
            return FunctionListResponse(functions=function_list)

        @self.app.post("/api/v1/functions/{function_name}/execute", response_model=FunctionExecuteResponse)
        async def execute_function(  # type: ignore[misc]
            function_name: str, request: FunctionExecuteRequest
        ) -> FunctionExecuteResponse:
            """Execute a registered function."""
            # Get the function from registry
            function_info = self.function_registry.get_function(function_name)
            if function_info is None:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Function '{function_name}' not found"
                )

            try:
                # Execute the function with timing
                start_time = time.time()
                result = await self.async_adapter.execute(
                    function_info.function, request.args, request.kwargs
                )
                execution_time = time.time() - start_time

                self.logger.info(
                    "Function executed successfully",
                    function_name=function_name,
                    execution_time=execution_time,
                )

                return FunctionExecuteResponse(
                    result=result,
                    execution_time=execution_time,
                )
            except Exception as e:
                self.logger.error(
                    "Function execution failed",
                    function_name=function_name,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": str(e),
                        "error_type": type(e).__name__,
                        "function_name": function_name,
                    },
                ) from e

        @self.app.delete("/api/v1/functions/{function_name}", status_code=204)
        async def delete_function(function_name: str) -> None:  # type: ignore[misc]
            """Delete a registered function."""
            success = self.function_registry.delete_function(function_name)
            if not success:
                raise HTTPException(
                    status_code=404,
                    detail=f"Function '{function_name}' not found"
                )
            
            self.logger.info("Function deleted successfully", function_name=function_name)

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
