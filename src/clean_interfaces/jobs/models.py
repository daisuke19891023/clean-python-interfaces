"""Job data models using Pydantic."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class JobStatus(str, Enum):
    """Job execution status."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Job execution type."""

    ASYNC = "async"
    SYNC = "sync"


class Job(BaseModel):
    """Job data model with complete lifecycle tracking."""

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique job identifier"
    )
    
    name: str = Field(
        min_length=1,
        description="Human-readable job name"
    )
    
    job_type: JobType = Field(
        description="Type of job execution (async/sync)"
    )
    
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Job input data"
    )
    
    status: JobStatus = Field(
        default=JobStatus.PENDING,
        description="Current job execution status"
    )
    
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Job creation timestamp"
    )
    
    started_at: datetime | None = Field(
        default=None,
        description="Job execution start timestamp"
    )
    
    completed_at: datetime | None = Field(
        default=None,
        description="Job completion timestamp"
    )
    
    result: dict[str, Any] | None = Field(
        default=None,
        description="Job execution result data"
    )
    
    error: dict[str, Any] | None = Field(
        default=None,
        description="Job execution error information"
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_empty(cls, v: str) -> str:
        """Validate job name is not empty."""
        if not v.strip():
            msg = "Job name cannot be empty or whitespace only"
            raise ValueError(msg)
        return v.strip()

    def __eq__(self, other: object) -> bool:
        """Compare jobs by ID."""
        if not isinstance(other, Job):
            return False
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash job by ID for use in sets and dicts."""
        return hash(self.id)

    def __str__(self) -> str:
        """String representation of job."""
        return f"Job(id={self.id}, name={self.name}, type={self.job_type}, status={self.status})"