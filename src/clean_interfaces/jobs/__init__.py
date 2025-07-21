"""Job management system for clean interfaces.

This module provides a complete job management system with queue functionality,
asynchronous processing, and Factory pattern for switching implementations.
"""

from clean_interfaces.jobs.factory import JobManagerFactory
from clean_interfaces.jobs.models import Job, JobStatus, JobType
from clean_interfaces.jobs.types import JobManagerType
from clean_interfaces.jobs.exceptions import (
    JobManagerError,
    JobNotFoundError,
    JobValidationError,
    JobStateError,
    JobTimeoutError,
)

__all__ = [
    "JobManagerFactory",
    "Job",
    "JobStatus",
    "JobType",
    "JobManagerType",
    "JobManagerError",
    "JobNotFoundError",
    "JobValidationError",
    "JobStateError",
    "JobTimeoutError",
]