"""Type definitions for clean interfaces."""

from enum import Enum


class InterfaceType(str, Enum):
    """Available interface types."""

    CLI = "cli"
    RESTAPI = "restapi"


class JobManagerType(str, Enum):
    """Available job manager types."""

    MEMORY = "memory"
