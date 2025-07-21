"""In-memory job manager implementation."""

import asyncio
from collections import deque
from datetime import datetime, timezone
from typing import Any

from clean_interfaces.jobs.base import BaseJobManager
from clean_interfaces.jobs.exceptions import JobNotFoundError, JobStateError
from clean_interfaces.jobs.models import Job, JobStatus, JobType
from clean_interfaces.jobs.types import JobManagerType


class MemoryJobManager(BaseJobManager):
    """In-memory implementation of job manager.
    
    This implementation stores all job data in memory and provides
    a complete job queue processing system with event publishing.
    """

    def __init__(self) -> None:
        """Initialize the memory job manager."""
        super().__init__(JobManagerType.MEMORY)
        self._jobs: dict[str, Job] = {}
        self._queue: deque[str] = deque()

    async def start(self) -> None:
        """Start the job manager."""
        if self._is_running:
            self.logger.warning("Job manager is already running")
            return

        self._is_running = True
        self.logger.info("Memory job manager started")

    async def stop(self) -> None:
        """Stop the job manager."""
        if not self._is_running:
            self.logger.warning("Job manager is not running")
            return

        self._is_running = False
        
        # Clear all data
        pending_jobs = len(self._jobs)
        queued_jobs = len(self._queue)
        
        self._jobs.clear()
        self._queue.clear()
        
        self.logger.info(
            "Memory job manager stopped",
            pending_jobs_cleared=pending_jobs,
            queued_jobs_cleared=queued_jobs
        )

    async def create_job(
        self,
        name: str,
        job_type: JobType,
        payload: dict[str, Any],
        **kwargs: Any
    ) -> Job:
        """Create a new job."""
        if not self._is_running:
            msg = "Job manager is not running"
            raise JobStateError(message=msg)

        # Create job with provided data
        job_data = {
            "name": name,
            "job_type": job_type,
            "payload": payload,
            **kwargs
        }
        
        job = Job(**job_data)
        
        # Store the job
        self._jobs[job.id] = job
        
        # Publish creation event
        await self._publish_event("job_created", job.id, job_data=job.model_dump())
        
        self.logger.info(
            "Job created",
            job_id=job.id,
            name=job.name,
            job_type=job.job_type,
            total_jobs=len(self._jobs)
        )
        
        return job

    async def get_job(self, job_id: str) -> Job:
        """Get a job by ID."""
        if job_id not in self._jobs:
            raise JobNotFoundError(job_id)
        
        return self._jobs[job_id]

    async def list_jobs(
        self,
        status: JobStatus | None = None,
        limit: int | None = None,
        offset: int = 0
    ) -> list[Job]:
        """List jobs with optional filtering."""
        jobs = list(self._jobs.values())
        
        # Filter by status if provided
        if status is not None:
            jobs = [job for job in jobs if job.status == status]
        
        # Sort by creation time (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        
        # Apply pagination
        start_idx = offset
        end_idx = start_idx + limit if limit is not None else None
        
        return jobs[start_idx:end_idx]

    async def submit_job(self, job_id: str) -> None:
        """Submit a job to the processing queue."""
        job = await self.get_job(job_id)
        
        # Validate state transition
        if job.status != JobStatus.PENDING:
            raise JobStateError(
                job.status.value,
                JobStatus.QUEUED.value,
                "Only pending jobs can be queued"
            )
        
        # Update job status
        job.status = JobStatus.QUEUED
        
        # Add to queue
        self._queue.append(job_id)
        
        # Publish event
        await self._publish_event("job_queued", job_id, queue_size=len(self._queue))
        
        self.logger.info(
            "Job queued",
            job_id=job_id,
            queue_size=len(self._queue)
        )

    async def start_job(self, job_id: str) -> None:
        """Start processing a job."""
        job = await self.get_job(job_id)
        
        # Validate state transition
        if job.status != JobStatus.QUEUED:
            raise JobStateError(
                job.status.value,
                JobStatus.RUNNING.value,
                "Only queued jobs can be started"
            )
        
        # Update job status and timestamp
        job.status = JobStatus.RUNNING
        job.started_at = datetime.now(timezone.utc)
        
        # Remove from queue if present
        try:
            self._queue.remove(job_id)
        except ValueError:
            # Job might not be in queue if started directly
            pass
        
        # Publish event
        await self._publish_event("job_started", job_id, started_at=job.started_at)
        
        self.logger.info(
            "Job started",
            job_id=job_id,
            queue_size=len(self._queue)
        )

    async def complete_job(self, job_id: str, result: dict[str, Any]) -> None:
        """Mark a job as completed with result."""
        job = await self.get_job(job_id)
        
        # Validate state transition
        if job.status != JobStatus.RUNNING:
            raise JobStateError(
                job.status.value,
                JobStatus.COMPLETED.value,
                "Only running jobs can be completed"
            )
        
        # Update job status, result, and timestamp
        job.status = JobStatus.COMPLETED
        job.result = result
        job.completed_at = datetime.now(timezone.utc)
        
        # Publish event
        await self._publish_event(
            "job_completed", 
            job_id, 
            result=result,
            completed_at=job.completed_at
        )
        
        self.logger.info(
            "Job completed",
            job_id=job_id,
            result_keys=list(result.keys()) if result else []
        )

    async def fail_job(self, job_id: str, error: dict[str, Any]) -> None:
        """Mark a job as failed with error information."""
        job = await self.get_job(job_id)
        
        # Validate state transition (can fail from running or queued)
        if job.status not in (JobStatus.RUNNING, JobStatus.QUEUED):
            raise JobStateError(
                job.status.value,
                JobStatus.FAILED.value,
                "Only running or queued jobs can be failed"
            )
        
        # Update job status, error, and timestamp
        job.status = JobStatus.FAILED
        job.error = error
        job.completed_at = datetime.now(timezone.utc)
        
        # Remove from queue if present
        try:
            self._queue.remove(job_id)
        except ValueError:
            # Job might not be in queue
            pass
        
        # Publish event
        await self._publish_event(
            "job_failed", 
            job_id, 
            error=error,
            completed_at=job.completed_at
        )
        
        self.logger.error(
            "Job failed",
            job_id=job_id,
            error=error
        )

    async def cancel_job(self, job_id: str) -> None:
        """Cancel a queued job."""
        job = await self.get_job(job_id)
        
        # Validate state transition (can only cancel pending or queued jobs)
        if job.status not in (JobStatus.PENDING, JobStatus.QUEUED):
            raise JobStateError(
                job.status.value,
                JobStatus.CANCELLED.value,
                "Only pending or queued jobs can be cancelled"
            )
        
        # Update job status and timestamp
        job.status = JobStatus.CANCELLED
        job.completed_at = datetime.now(timezone.utc)
        
        # Remove from queue if present
        try:
            self._queue.remove(job_id)
        except ValueError:
            # Job might not be in queue
            pass
        
        # Publish event
        await self._publish_event(
            "job_cancelled", 
            job_id,
            completed_at=job.completed_at
        )
        
        self.logger.info(
            "Job cancelled",
            job_id=job_id,
            queue_size=len(self._queue)
        )

    async def get_next_job(self) -> Job | None:
        """Get the next job from the queue for processing."""
        if not self._queue:
            return None
        
        # Get next job ID (FIFO)
        job_id = self._queue[0]  # Peek at first item
        
        try:
            job = await self.get_job(job_id)
            # Verify job is still in queued state
            if job.status == JobStatus.QUEUED:
                return job
            else:
                # Remove invalid job from queue
                self._queue.popleft()
                self.logger.warning(
                    "Removed invalid job from queue",
                    job_id=job_id,
                    actual_status=job.status
                )
                # Try next job recursively
                return await self.get_next_job()
        except JobNotFoundError:
            # Remove invalid job reference from queue
            self._queue.popleft()
            self.logger.warning(
                "Removed non-existent job from queue",
                job_id=job_id
            )
            # Try next job recursively
            return await self.get_next_job()