"""Function-related models for async adaptation functionality."""

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class FunctionRegisterRequest(BaseModel):
    """Request model for function registration."""

    name: str = Field(
        ...,
        description="Name of the function to register",
        min_length=1,
        pattern=r"^[a-zA-Z_][a-zA-Z0-9_]*$",
    )
    code: str = Field(
        ...,
        description="Python code containing the function definition",
        min_length=1,
    )
    is_async: bool = Field(
        ...,
        description="Whether the function is async or sync",
    )


class FunctionRegisterResponse(BaseModel):
    """Response model for function registration."""

    name: str = Field(
        ...,
        description="Name of the registered function",
    )
    is_async: bool = Field(
        ...,
        description="Whether the function is async or sync",
    )
    registered_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="Timestamp when the function was registered",
    )


class FunctionExecuteRequest(BaseModel):
    """Request model for function execution."""

    args: list[Any] = Field(
        default_factory=list,
        description="Positional arguments to pass to the function",
    )
    kwargs: dict[str, Any] = Field(
        default_factory=dict,
        description="Keyword arguments to pass to the function",
    )


class FunctionExecuteResponse(BaseModel):
    """Response model for function execution."""

    result: Any = Field(
        ...,
        description="Result returned by the function",
    )
    execution_time: float = Field(
        ...,
        description="Time taken to execute the function in seconds",
        ge=0,
    )
    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="Timestamp when the function was executed",
    )


class FunctionInfo(BaseModel):
    """Model for function information in listings."""

    name: str = Field(
        ...,
        description="Name of the function",
    )
    is_async: bool = Field(
        ...,
        description="Whether the function is async or sync",
    )
    registered_at: datetime = Field(
        ...,
        description="Timestamp when the function was registered",
    )


class FunctionListResponse(BaseModel):
    """Response model for listing registered functions."""

    functions: list[dict[str, Any]] = Field(
        ...,
        description="List of registered functions",
    )


class FunctionErrorResponse(BaseModel):
    """Response model for function execution errors."""

    error: str = Field(
        ...,
        description="Error message describing what went wrong",
    )
    error_type: str = Field(
        ...,
        description="Type of error that occurred",
    )
    function_name: str = Field(
        ...,
        description="Name of the function that caused the error",
    )
    executed_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="Timestamp when the error occurred",
    )