"""API response models for RestAPI interface."""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(
        default="healthy",
        description="Health status of the API",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="Current server timestamp",
    )


class WelcomeResponse(BaseModel):
    """Welcome message response model."""

    message: str = Field(
        default="Welcome to Clean Interfaces!",
        description="Welcome message",
    )
    hint: str = Field(
        default="Type --help for more information",
        description="Hint for users",
    )
    interface: str = Field(
        default="RestAPI",
        description="Current interface type",
    )


class ErrorResponse(BaseModel):
    """Error response model."""

    error: str = Field(
        description="Error message",
    )
    detail: str | None = Field(
        default=None,
        description="Detailed error information",
    )
    status_code: int = Field(
        description="HTTP status code",
    )
