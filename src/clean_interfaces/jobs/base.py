"""Base classes for job management system."""

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Awaitable

from clean_interfaces.base import BaseComponent
from clean_interfaces.jobs.models import Job, JobStatus, JobType
from clean_interfaces.jobs.types import JobManagerType


EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


class BaseJobManager(ABC, BaseComponent):
    """Abstract base class for job managers."""

    def __init__(self, manager_type: JobManagerType) -> None:
        """Initialize the job manager.
        
        Args:
            manager_type: Type of job manager implementation
        """
        super().__init__()
        self._manager_type = manager_type
        self._is_running = False
        self._event_handlers: list[EventHandler] = []

    @property
    def manager_type(self) -> JobManagerType:
        """Get the job manager type.
        
        Returns:
            JobManagerType: The manager type
        """
        return self._manager_type

    @property
    def is_running(self) -> bool:
        """Check if the job manager is running.
        
        Returns:
            bool: True if running, False otherwise
        """
        return self._is_running

    @abstractmethod
    async def start(self) -> None:
        """Start the job manager.
        
        This method should initialize any resources needed
        for job management and set the running state.
        """

    @abstractmethod
    async def stop(self) -> None:
        """Stop the job manager.
        
        This method should clean up resources and
        set the running state to False.
        """

    @abstractmethod
    async def create_job(
        self,
        name: str,
        job_type: JobType,
        payload: dict[str, Any],
        **kwargs: Any
    ) -> Job:
        """Create a new job.
        
        Args:
            name: Job name
            job_type: Type of job (async/sync)
            payload: Job input data
            **kwargs: Additional job parameters
            
        Returns:
            Job: The created job
        """

    @abstractmethod
    async def get_job(self, job_id: str) -> Job:
        """Get a job by ID.
        
        Args:
            job_id: Unique job identifier
            
        Returns:
            Job: The job instance
            
        Raises:
            JobNotFoundError: If job doesn't exist
        """

    @abstractmethod
    async def list_jobs(
        self,
        status: JobStatus | None = None,
        limit: int | None = None,
        offset: int = 0
    ) -> list[Job]:
        """List jobs with optional filtering.
        
        Args:
            status: Filter by job status (optional)
            limit: Maximum number of jobs to return (optional)
            offset: Number of jobs to skip (default: 0)
            
        Returns:
            list[Job]: List of jobs matching criteria
        """

    @abstractmethod
    async def submit_job(self, job_id: str) -> None:
        """Submit a job to the processing queue.
        
        Args:
            job_id: Unique job identifier
            
        Raises:
            JobNotFoundError: If job doesn't exist
            JobStateError: If job is not in valid state for queuing
        """

    @abstractmethod
    async def start_job(self, job_id: str) -> None:
        """Start processing a job.
        
        Args:
            job_id: Unique job identifier
            
        Raises:
            JobNotFoundError: If job doesn't exist
            JobStateError: If job is not in valid state for starting
        """

    @abstractmethod
    async def complete_job(self, job_id: str, result: dict[str, Any]) -> None:
        """Mark a job as completed with result.
        
        Args:
            job_id: Unique job identifier
            result: Job execution result
            
        Raises:
            JobNotFoundError: If job doesn't exist
            JobStateError: If job is not in valid state for completion
        """

    @abstractmethod
    async def fail_job(self, job_id: str, error: dict[str, Any]) -> None:
        """Mark a job as failed with error information.
        
        Args:
            job_id: Unique job identifier
            error: Error information
            
        Raises:
            JobNotFoundError: If job doesn't exist
            JobStateError: If job is not in valid state for failure
        """

    @abstractmethod
    async def cancel_job(self, job_id: str) -> None:
        """Cancel a queued job.
        
        Args:
            job_id: Unique job identifier
            
        Raises:
            JobNotFoundError: If job doesn't exist
            JobStateError: If job cannot be cancelled
        """

    @abstractmethod
    async def get_next_job(self) -> Job | None:
        """Get the next job from the queue for processing.
        
        Returns:
            Job | None: Next job to process, or None if queue is empty
        """

    async def subscribe_to_events(self, handler: EventHandler) -> None:
        """Subscribe to job events.
        
        Args:
            handler: Async function to handle job events
        """
        self._event_handlers.append(handler)
        self.logger.info("Event handler subscribed", handler_count=len(self._event_handlers))

    async def unsubscribe_from_events(self, handler: EventHandler) -> None:
        """Unsubscribe from job events.
        
        Args:
            handler: Event handler to remove
        """
        if handler in self._event_handlers:
            self._event_handlers.remove(handler)
            self.logger.info("Event handler unsubscribed", handler_count=len(self._event_handlers))

    async def _publish_event(
        self,
        event_type: str,
        job_id: str,
        **additional_data: Any
    ) -> None:
        """Publish an event to all subscribers.
        
        Args:
            event_type: Type of event (e.g., 'job_created', 'job_completed')
            job_id: ID of the job the event relates to
            **additional_data: Additional event data
        """
        if not self._event_handlers:
            return

        event_data = {
            "type": event_type,
            "job_id": job_id,
            "timestamp": asyncio.get_event_loop().time(),
            **additional_data
        }

        # Publish to all handlers concurrently
        tasks = [handler(event_data) for handler in self._event_handlers]
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            self.logger.error(
                "Error publishing event",
                event_type=event_type,
                job_id=job_id,
                error=str(e)
            )