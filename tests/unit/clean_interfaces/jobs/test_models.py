"""Unit tests for job models."""

import pytest
from datetime import datetime, timezone
from uuid import UUID
from typing import Any

from pydantic import ValidationError

from clean_interfaces.jobs.models import Job, JobStatus, JobType


class TestJobModel:
    """Unit tests for Job Pydantic model."""

    def test_job_creation_with_minimal_data(self) -> None:
        """Test creating a job with minimal required data."""
        job = Job(
            name="test_job",
            job_type=JobType.ASYNC,
            payload={"key": "value"}
        )
        
        assert job.name == "test_job"
        assert job.job_type == JobType.ASYNC
        assert job.payload == {"key": "value"}
        assert job.status == JobStatus.PENDING  # Default status
        assert isinstance(job.id, str)
        assert len(job.id) > 0
        assert isinstance(job.created_at, datetime)
        assert job.started_at is None
        assert job.completed_at is None
        assert job.result is None
        assert job.error is None

    def test_job_creation_with_full_data(self) -> None:
        """Test creating a job with all data provided."""
        created_at = datetime.now(timezone.utc)
        started_at = datetime.now(timezone.utc)
        completed_at = datetime.now(timezone.utc)
        
        job = Job(
            id="custom-id",
            name="full_job",
            job_type=JobType.SYNC,
            payload={"data": "test"},
            status=JobStatus.COMPLETED,
            created_at=created_at,
            started_at=started_at,
            completed_at=completed_at,
            result={"output": "success"},
            error=None
        )
        
        assert job.id == "custom-id"
        assert job.name == "full_job"
        assert job.job_type == JobType.SYNC
        assert job.status == JobStatus.COMPLETED
        assert job.created_at == created_at
        assert job.started_at == started_at
        assert job.completed_at == completed_at
        assert job.result == {"output": "success"}

    def test_job_name_validation_required(self) -> None:
        """Test that job name is required."""
        with pytest.raises(ValidationError) as exc_info:
            Job(
                job_type=JobType.ASYNC,
                payload={}
            )
        
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("name",) for error in errors)

    def test_job_name_validation_not_empty(self) -> None:
        """Test that job name cannot be empty."""
        with pytest.raises(ValidationError) as exc_info:
            Job(
                name="",
                job_type=JobType.ASYNC,
                payload={}
            )
        
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("name",) and "at least 1 character" in error["msg"]
            for error in errors
        )

    def test_job_type_validation(self) -> None:
        """Test job type validation."""
        # Valid job types
        job_async = Job(name="test", job_type=JobType.ASYNC, payload={})
        job_sync = Job(name="test", job_type=JobType.SYNC, payload={})
        
        assert job_async.job_type == JobType.ASYNC
        assert job_sync.job_type == JobType.SYNC
        
        # Invalid job type should raise validation error
        with pytest.raises(ValidationError):
            Job(name="test", job_type="invalid", payload={})  # type: ignore

    def test_job_status_validation(self) -> None:
        """Test job status validation."""
        # All valid statuses should work
        for status in JobStatus:
            job = Job(
                name="test",
                job_type=JobType.ASYNC,
                payload={},
                status=status
            )
            assert job.status == status

    def test_job_payload_validation(self) -> None:
        """Test job payload validation."""
        # Empty payload should be allowed
        job1 = Job(name="test", job_type=JobType.ASYNC, payload={})
        assert job1.payload == {}
        
        # Complex payload should be allowed
        complex_payload = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "array": [1, 2, 3],
            "nested": {"key": "value"}
        }
        job2 = Job(name="test", job_type=JobType.ASYNC, payload=complex_payload)
        assert job2.payload == complex_payload

    def test_job_timestamps_validation(self) -> None:
        """Test timestamp field validation."""
        job = Job(name="test", job_type=JobType.ASYNC, payload={})
        
        # created_at should be set automatically
        assert isinstance(job.created_at, datetime)
        
        # Other timestamps should be None initially
        assert job.started_at is None
        assert job.completed_at is None

    def test_job_result_and_error_validation(self) -> None:
        """Test result and error field validation."""
        # Result can be any JSON-serializable data
        job1 = Job(
            name="test",
            job_type=JobType.ASYNC,
            payload={},
            result={"success": True, "data": [1, 2, 3]}
        )
        assert job1.result == {"success": True, "data": [1, 2, 3]}
        
        # Error can be any JSON-serializable data
        job2 = Job(
            name="test",
            job_type=JobType.ASYNC,
            payload={},
            error={"message": "Failed", "code": 500}
        )
        assert job2.error == {"message": "Failed", "code": 500}

    def test_job_serialization(self) -> None:
        """Test job model serialization."""
        job = Job(
            name="serialize_test",
            job_type=JobType.ASYNC,
            payload={"key": "value"}
        )
        
        # Should be serializable to dict
        job_dict = job.model_dump()
        
        assert job_dict["name"] == "serialize_test"
        assert job_dict["job_type"] == "async"
        assert job_dict["payload"] == {"key": "value"}
        assert job_dict["status"] == "pending"
        assert "id" in job_dict
        assert "created_at" in job_dict

    def test_job_deserialization(self) -> None:
        """Test job model deserialization."""
        job_data = {
            "id": "test-id",
            "name": "deserialize_test",
            "job_type": "sync",
            "payload": {"data": "test"},
            "status": "running",
            "created_at": "2024-01-01T00:00:00Z",
            "started_at": "2024-01-01T00:01:00Z",
            "completed_at": None,
            "result": None,
            "error": None
        }
        
        job = Job.model_validate(job_data)
        
        assert job.id == "test-id"
        assert job.name == "deserialize_test"
        assert job.job_type == JobType.SYNC
        assert job.status == JobStatus.RUNNING
        assert job.payload == {"data": "test"}

    def test_job_equality(self) -> None:
        """Test job equality comparison."""
        job1 = Job(name="test", job_type=JobType.ASYNC, payload={}, id="same-id")
        job2 = Job(name="test", job_type=JobType.ASYNC, payload={}, id="same-id")
        job3 = Job(name="test", job_type=JobType.ASYNC, payload={}, id="different-id")
        
        # Jobs with same ID should be equal
        assert job1 == job2
        
        # Jobs with different IDs should not be equal
        assert job1 != job3

    def test_job_hash(self) -> None:
        """Test job hash for use in sets and dicts."""
        job1 = Job(name="test", job_type=JobType.ASYNC, payload={}, id="same-id")
        job2 = Job(name="test", job_type=JobType.ASYNC, payload={}, id="same-id")
        
        # Jobs with same ID should have same hash
        assert hash(job1) == hash(job2)
        
        # Should be able to use in sets
        job_set = {job1, job2}
        assert len(job_set) == 1

    def test_job_string_representation(self) -> None:
        """Test job string representation."""
        job = Job(
            name="repr_test",
            job_type=JobType.ASYNC,
            payload={},
            id="test-id"
        )
        
        job_str = str(job)
        assert "test-id" in job_str
        assert "repr_test" in job_str
        assert "async" in job_str.lower()


class TestJobEnums:
    """Unit tests for job-related enums."""

    def test_job_status_enum_values(self) -> None:
        """Test JobStatus enum has expected values."""
        expected_statuses = {
            "pending", "queued", "running", "completed", "failed", "cancelled"
        }
        actual_statuses = {status.value for status in JobStatus}
        
        assert actual_statuses == expected_statuses

    def test_job_type_enum_values(self) -> None:
        """Test JobType enum has expected values."""
        expected_types = {"async", "sync"}
        actual_types = {job_type.value for job_type in JobType}
        
        assert actual_types == expected_types

    def test_enum_string_conversion(self) -> None:
        """Test enum string conversion."""
        assert str(JobStatus.PENDING) == "pending"
        assert str(JobType.ASYNC) == "async"

    def test_enum_comparison(self) -> None:
        """Test enum comparison."""
        assert JobStatus.PENDING == JobStatus.PENDING
        assert JobStatus.PENDING != JobStatus.RUNNING
        assert JobType.ASYNC == JobType.ASYNC
        assert JobType.ASYNC != JobType.SYNC