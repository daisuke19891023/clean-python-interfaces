"""Type definitions for job management system."""

from enum import Enum


class JobManagerType(str, Enum):
    """Available job manager implementations."""

    MEMORY = "memory"