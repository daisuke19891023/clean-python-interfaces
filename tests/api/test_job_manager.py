"""API tests for job manager components.

These tests verify the API-level functionality of job managers,
factories, and queue operations without full E2E integration.
"""

import asyncio
import pytest
from typing import Any
from unittest.mock import AsyncMock

from clean_interfaces.jobs.factory import JobManagerFactory
from clean_interfaces.jobs.models import Job, JobStatus, JobType
from clean_interfaces.jobs.types import JobManagerType
from clean_interfaces.jobs.exceptions import JobNotFoundError, JobManagerError


class TestJobManagerFactory:
    """API tests for job manager factory."""

    def test_factory_creates_memory_manager(self) -> None:
        """Test factory creates in-memory job manager."""
        factory = JobManagerFactory()
        manager = factory.create(JobManagerType.MEMORY)
        
        assert manager is not None
        assert manager.manager_type == JobManagerType.MEMORY

    def test_factory_creates_from_settings(self) -> None:
        """Test factory creates manager from settings."""
        factory = JobManagerFactory()
        manager = factory.create_from_settings()
        
        # Should default to memory type
        assert manager is not None
        assert manager.manager_type == JobManagerType.MEMORY

    def test_factory_invalid_type_raises_error(self) -> None:
        """Test factory raises error for invalid manager type."""
        factory = JobManagerFactory()
        
        with pytest.raises(ValueError, match="Unknown job manager type"):
            factory.create("invalid_type")  # type: ignore

    def test_factory_singleton_behavior(self) -> None:
        """Test factory creates separate instances."""
        factory = JobManagerFactory()
        manager1 = factory.create(JobManagerType.MEMORY)
        manager2 = factory.create(JobManagerType.MEMORY)
        
        # Should be separate instances
        assert manager1 is not manager2


class TestMemoryJobManager:
    """API tests for in-memory job manager."""

    @pytest.fixture
    async def job_manager(self) -> Any:
        """Create and start a job manager for testing."""
        factory = JobManagerFactory()
        manager = factory.create(JobManagerType.MEMORY)
        await manager.start()
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    async def test_job_manager_start_stop(self) -> None:
        """Test job manager start and stop operations."""
        factory = JobManagerFactory()
        manager = factory.create(JobManagerType.MEMORY)
        
        # Initially not running
        assert not manager.is_running
        
        # Start manager
        await manager.start()
        assert manager.is_running
        
        # Stop manager
        await manager.stop()
        assert not manager.is_running

    @pytest.mark.asyncio
    async def test_create_job_with_valid_data(self, job_manager: Any) -> None:
        """Test creating a job with valid data."""
        job = await job_manager.create_job(
            name="test_job",
            job_type=JobType.ASYNC,
            payload={"key": "value"}
        )
        
        assert job.id is not None
        assert job.name == "test_job"
        assert job.job_type == JobType.ASYNC
        assert job.status == JobStatus.PENDING
        assert job.payload == {"key": "value"}
        assert job.created_at is not None

    @pytest.mark.asyncio
    async def test_get_existing_job(self, job_manager: Any) -> None:
        """Test retrieving an existing job."""
        # Create job
        created_job = await job_manager.create_job(
            name="get_test",
            job_type=JobType.SYNC,
            payload={}
        )
        
        # Retrieve job
        retrieved_job = await job_manager.get_job(created_job.id)
        
        assert retrieved_job.id == created_job.id
        assert retrieved_job.name == created_job.name
        assert retrieved_job.status == created_job.status

    @pytest.mark.asyncio
    async def test_get_nonexistent_job_raises_error(self, job_manager: Any) -> None:
        """Test retrieving nonexistent job raises JobNotFoundError."""
        with pytest.raises(JobNotFoundError):
            await job_manager.get_job("nonexistent-id")

    @pytest.mark.asyncio
    async def test_list_jobs_empty(self, job_manager: Any) -> None:
        """Test listing jobs when none exist."""
        jobs = await job_manager.list_jobs()
        assert jobs == []

    @pytest.mark.asyncio
    async def test_list_jobs_with_data(self, job_manager: Any) -> None:
        """Test listing jobs with existing data."""
        # Create multiple jobs
        job1 = await job_manager.create_job("job1", JobType.ASYNC, {})
        job2 = await job_manager.create_job("job2", JobType.SYNC, {})
        
        jobs = await job_manager.list_jobs()
        
        assert len(jobs) == 2
        job_ids = {job.id for job in jobs}
        assert job1.id in job_ids
        assert job2.id in job_ids

    @pytest.mark.asyncio
    async def test_list_jobs_with_status_filter(self, job_manager: Any) -> None:
        """Test listing jobs filtered by status."""
        # Create jobs with different statuses
        pending_job = await job_manager.create_job("pending", JobType.ASYNC, {})
        running_job = await job_manager.create_job("running", JobType.ASYNC, {})
        
        # Change one job to running
        await job_manager.submit_job(running_job.id)
        await job_manager.start_job(running_job.id)
        
        # List only pending jobs
        pending_jobs = await job_manager.list_jobs(status=JobStatus.PENDING)
        assert len(pending_jobs) == 1
        assert pending_jobs[0].id == pending_job.id
        
        # List only running jobs
        running_jobs = await job_manager.list_jobs(status=JobStatus.RUNNING)
        assert len(running_jobs) == 1
        assert running_jobs[0].id == running_job.id


class TestJobQueueOperations:
    """API tests for job queue operations."""

    @pytest.fixture
    async def job_manager(self) -> Any:
        """Create and start a job manager for testing."""
        factory = JobManagerFactory()
        manager = factory.create(JobManagerType.MEMORY)
        await manager.start()
        yield manager
        await manager.stop()

    @pytest.mark.asyncio
    async def test_submit_job_to_queue(self, job_manager: Any) -> None:
        """Test submitting a job to the queue."""
        job = await job_manager.create_job("queue_test", JobType.ASYNC, {})
        
        # Initially pending
        assert job.status == JobStatus.PENDING
        
        # Submit to queue
        await job_manager.submit_job(job.id)
        
        # Should now be queued
        queued_job = await job_manager.get_job(job.id)
        assert queued_job.status == JobStatus.QUEUED

    @pytest.mark.asyncio
    async def test_start_job_from_queue(self, job_manager: Any) -> None:
        """Test starting a job from the queue."""
        job = await job_manager.create_job("start_test", JobType.ASYNC, {})
        await job_manager.submit_job(job.id)
        
        # Start the job
        await job_manager.start_job(job.id)
        
        # Should now be running
        running_job = await job_manager.get_job(job.id)
        assert running_job.status == JobStatus.RUNNING
        assert running_job.started_at is not None

    @pytest.mark.asyncio
    async def test_complete_job(self, job_manager: Any) -> None:
        """Test completing a running job."""
        job = await job_manager.create_job("complete_test", JobType.ASYNC, {})
        await job_manager.submit_job(job.id)
        await job_manager.start_job(job.id)
        
        # Complete the job
        result = {"output": "success", "count": 42}
        await job_manager.complete_job(job.id, result)
        
        # Should now be completed
        completed_job = await job_manager.get_job(job.id)
        assert completed_job.status == JobStatus.COMPLETED
        assert completed_job.result == result
        assert completed_job.completed_at is not None

    @pytest.mark.asyncio
    async def test_fail_job(self, job_manager: Any) -> None:
        """Test failing a running job."""
        job = await job_manager.create_job("fail_test", JobType.ASYNC, {})
        await job_manager.submit_job(job.id)
        await job_manager.start_job(job.id)
        
        # Fail the job
        error = {"message": "Something went wrong", "code": "ERR001"}
        await job_manager.fail_job(job.id, error)
        
        # Should now be failed
        failed_job = await job_manager.get_job(job.id)
        assert failed_job.status == JobStatus.FAILED
        assert failed_job.error == error
        assert failed_job.completed_at is not None

    @pytest.mark.asyncio
    async def test_get_next_job_from_queue(self, job_manager: Any) -> None:
        """Test getting the next job from queue for processing."""
        # Create and queue multiple jobs
        job1 = await job_manager.create_job("first", JobType.ASYNC, {})
        job2 = await job_manager.create_job("second", JobType.ASYNC, {})
        
        await job_manager.submit_job(job1.id)
        await job_manager.submit_job(job2.id)
        
        # Get next job (should be FIFO)
        next_job = await job_manager.get_next_job()
        assert next_job is not None
        assert next_job.id == job1.id
        assert next_job.status == JobStatus.QUEUED

    @pytest.mark.asyncio
    async def test_get_next_job_empty_queue(self, job_manager: Any) -> None:
        """Test getting next job when queue is empty."""
        next_job = await job_manager.get_next_job()
        assert next_job is None

    @pytest.mark.asyncio
    async def test_cancel_job(self, job_manager: Any) -> None:
        """Test canceling a queued job."""
        job = await job_manager.create_job("cancel_test", JobType.ASYNC, {})
        await job_manager.submit_job(job.id)
        
        # Cancel the job
        await job_manager.cancel_job(job.id)
        
        # Should now be cancelled
        cancelled_job = await job_manager.get_job(job.id)
        assert cancelled_job.status == JobStatus.CANCELLED
        assert cancelled_job.completed_at is not None

    @pytest.mark.asyncio
    async def test_job_status_transitions(self, job_manager: Any) -> None:
        """Test valid job status transitions."""
        job = await job_manager.create_job("transition_test", JobType.ASYNC, {})
        
        # PENDING -> QUEUED
        await job_manager.submit_job(job.id)
        assert (await job_manager.get_job(job.id)).status == JobStatus.QUEUED
        
        # QUEUED -> RUNNING
        await job_manager.start_job(job.id)
        assert (await job_manager.get_job(job.id)).status == JobStatus.RUNNING
        
        # RUNNING -> COMPLETED
        await job_manager.complete_job(job.id, {"result": "done"})
        assert (await job_manager.get_job(job.id)).status == JobStatus.COMPLETED