"""Job system exception classes."""


class JobManagerError(Exception):
    """Base exception for job manager errors."""

    def __init__(self, message: str) -> None:
        """Initialize job manager error.
        
        Args:
            message: Error message
        """
        super().__init__(message)
        self.message = message


class JobNotFoundError(JobManagerError):
    """Exception raised when a job cannot be found."""

    def __init__(self, job_id: str, message: str | None = None) -> None:
        """Initialize job not found error.
        
        Args:
            job_id: ID of the job that was not found
            message: Optional custom error message
        """
        if message is None:
            message = f"Job with ID '{job_id}' not found"
        super().__init__(message)
        self.job_id = job_id


class JobValidationError(JobManagerError):
    """Exception raised when job validation fails."""

    def __init__(self, field: str | None = None, message: str | None = None) -> None:
        """Initialize job validation error.
        
        Args:
            field: Field name that failed validation (optional)
            message: Error message or validation failure description
        """
        if field is not None and message is not None:
            formatted_message = f"Validation error for field '{field}': {message}"
        else:
            formatted_message = message or field or "Job validation failed"
        
        super().__init__(formatted_message)
        self.field = field


class JobStateError(JobManagerError):
    """Exception raised when an invalid job state transition is attempted."""

    def __init__(
        self, 
        from_state: str | None = None, 
        to_state: str | None = None, 
        message: str | None = None
    ) -> None:
        """Initialize job state error.
        
        Args:
            from_state: Current job state
            to_state: Attempted target state
            message: Error message or description
        """
        if from_state is not None and to_state is not None and message is not None:
            formatted_message = (
                f"Invalid job state transition from '{from_state}' to '{to_state}': {message}"
            )
        else:
            formatted_message = message or from_state or "Invalid job state transition"
        
        super().__init__(formatted_message)
        self.from_state = from_state
        self.to_state = to_state


class JobTimeoutError(JobManagerError):
    """Exception raised when a job operation times out."""

    def __init__(
        self, 
        job_id: str | None = None, 
        timeout_seconds: float | None = None, 
        message: str | None = None
    ) -> None:
        """Initialize job timeout error.
        
        Args:
            job_id: ID of the job that timed out
            timeout_seconds: Timeout duration in seconds
            message: Error message or description
        """
        if job_id is not None and timeout_seconds is not None and message is not None:
            formatted_message = (
                f"Job '{job_id}' timed out after {timeout_seconds} seconds: {message}"
            )
        else:
            formatted_message = message or job_id or "Job operation timed out"
        
        super().__init__(formatted_message)
        self.job_id = job_id
        self.timeout_seconds = timeout_seconds