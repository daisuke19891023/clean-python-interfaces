"""Unit tests for job system exceptions."""

import pytest

from clean_interfaces.jobs.exceptions import (
    JobManagerError,
    JobNotFoundError,
    JobValidationError,
    JobStateError,
    JobTimeoutError,
)


class TestJobManagerError:
    """Unit tests for JobManagerError base exception."""

    def test_job_manager_error_creation(self) -> None:
        """Test creating JobManagerError with message."""
        error = JobManagerError("Test error message")
        
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)

    def test_job_manager_error_inheritance(self) -> None:
        """Test JobManagerError is base for other job exceptions."""
        assert issubclass(JobNotFoundError, JobManagerError)
        assert issubclass(JobValidationError, JobManagerError)
        assert issubclass(JobStateError, JobManagerError)
        assert issubclass(JobTimeoutError, JobManagerError)

    def test_job_manager_error_with_cause(self) -> None:
        """Test JobManagerError with underlying cause."""
        original_error = ValueError("Original error")
        job_error = JobManagerError("Job error") from original_error
        
        assert str(job_error) == "Job error"
        assert job_error.__cause__ == original_error


class TestJobNotFoundError:
    """Unit tests for JobNotFoundError exception."""

    def test_job_not_found_error_creation(self) -> None:
        """Test creating JobNotFoundError."""
        error = JobNotFoundError("job-123")
        
        expected_message = "Job with ID 'job-123' not found"
        assert str(error) == expected_message

    def test_job_not_found_error_with_custom_message(self) -> None:
        """Test creating JobNotFoundError with custom message."""
        error = JobNotFoundError("job-456", "Custom not found message")
        
        assert str(error) == "Custom not found message"

    def test_job_not_found_error_inheritance(self) -> None:
        """Test JobNotFoundError inherits from JobManagerError."""
        error = JobNotFoundError("job-123")
        
        assert isinstance(error, JobManagerError)
        assert isinstance(error, Exception)

    def test_job_not_found_error_exception_handling(self) -> None:
        """Test JobNotFoundError can be caught as expected."""
        with pytest.raises(JobNotFoundError) as exc_info:
            raise JobNotFoundError("test-job")
        
        assert "test-job" in str(exc_info.value)
        
        # Should also be catchable as JobManagerError
        with pytest.raises(JobManagerError):
            raise JobNotFoundError("test-job")


class TestJobValidationError:
    """Unit tests for JobValidationError exception."""

    def test_job_validation_error_creation(self) -> None:
        """Test creating JobValidationError."""
        error = JobValidationError("Invalid job data")
        
        assert str(error) == "Invalid job data"

    def test_job_validation_error_with_field(self) -> None:
        """Test creating JobValidationError with field information."""
        error = JobValidationError("name", "Name cannot be empty")
        
        expected_message = "Validation error for field 'name': Name cannot be empty"
        assert str(error) == expected_message

    def test_job_validation_error_inheritance(self) -> None:
        """Test JobValidationError inherits from JobManagerError."""
        error = JobValidationError("Validation failed")
        
        assert isinstance(error, JobManagerError)
        assert isinstance(error, Exception)


class TestJobStateError:
    """Unit tests for JobStateError exception."""

    def test_job_state_error_creation(self) -> None:
        """Test creating JobStateError."""
        error = JobStateError("Invalid state transition")
        
        assert str(error) == "Invalid state transition"

    def test_job_state_error_with_transition(self) -> None:
        """Test creating JobStateError with state transition info."""
        error = JobStateError("pending", "completed", "Cannot transition directly")
        
        expected_message = (
            "Invalid job state transition from 'pending' to 'completed': "
            "Cannot transition directly"
        )
        assert str(error) == expected_message

    def test_job_state_error_inheritance(self) -> None:
        """Test JobStateError inherits from JobManagerError."""
        error = JobStateError("State error")
        
        assert isinstance(error, JobManagerError)
        assert isinstance(error, Exception)


class TestJobTimeoutError:
    """Unit tests for JobTimeoutError exception."""

    def test_job_timeout_error_creation(self) -> None:
        """Test creating JobTimeoutError."""
        error = JobTimeoutError("Operation timed out")
        
        assert str(error) == "Operation timed out"

    def test_job_timeout_error_with_timeout(self) -> None:
        """Test creating JobTimeoutError with timeout information."""
        error = JobTimeoutError("job-123", 30.0, "Job execution timeout")
        
        expected_message = (
            "Job 'job-123' timed out after 30.0 seconds: Job execution timeout"
        )
        assert str(error) == expected_message

    def test_job_timeout_error_inheritance(self) -> None:
        """Test JobTimeoutError inherits from JobManagerError."""
        error = JobTimeoutError("Timeout")
        
        assert isinstance(error, JobManagerError)
        assert isinstance(error, Exception)


class TestExceptionHierarchy:
    """Unit tests for exception hierarchy and behavior."""

    def test_all_exceptions_inherit_from_job_manager_error(self) -> None:
        """Test all job exceptions inherit from JobManagerError."""
        exceptions = [
            JobNotFoundError("test"),
            JobValidationError("test"),
            JobStateError("test"),
            JobTimeoutError("test"),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, JobManagerError)

    def test_exception_catching_hierarchy(self) -> None:
        """Test exception catching works with hierarchy."""
        # Can catch specific exception
        with pytest.raises(JobNotFoundError):
            raise JobNotFoundError("test-job")
        
        # Can catch as base JobManagerError
        with pytest.raises(JobManagerError):
            raise JobNotFoundError("test-job")
        
        # Can catch as general Exception
        with pytest.raises(Exception):
            raise JobNotFoundError("test-job")

    def test_exception_type_checking(self) -> None:
        """Test exception type checking."""
        not_found = JobNotFoundError("test")
        validation = JobValidationError("test")
        state = JobStateError("test")
        timeout = JobTimeoutError("test")
        
        # Each should be its own type
        assert type(not_found) == JobNotFoundError
        assert type(validation) == JobValidationError
        assert type(state) == JobStateError
        assert type(timeout) == JobTimeoutError
        
        # But all should be JobManagerError instances
        for exc in [not_found, validation, state, timeout]:
            assert isinstance(exc, JobManagerError)

    def test_exception_message_preservation(self) -> None:
        """Test exception messages are preserved through hierarchy."""
        original_message = "Original error message"
        error = JobNotFoundError("job-id", original_message)
        
        try:
            raise error
        except JobManagerError as caught:
            assert str(caught) == original_message
        except Exception as caught:
            assert str(caught) == original_message