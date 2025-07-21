"""E2E tests for job management system.

These tests verify the complete job system lifecycle from job creation
to completion, including pubsub functionality and integration with the
application.
"""

import asyncio
import pytest
from typing import Any

from clean_interfaces.jobs.factory import JobManagerFactory
from clean_interfaces.jobs.models import Job, JobStatus, JobType
from clean_interfaces.jobs.types import JobManagerType


class TestJobSystemLifecycle:
    """E2E tests for complete job system lifecycle."""

    @pytest.mark.asyncio
    async def test_complete_job_lifecycle(self) -> None:
        """Test complete job lifecycle from creation to completion."""
        # Create job manager
        factory = JobManagerFactory()
        job_manager = factory.create(JobManagerType.MEMORY)
        
        # Start job manager
        await job_manager.start()
        
        try:
            # Create a job
            job_data = {
                "name": "test_job",
                "job_type": JobType.ASYNC,
                "payload": {"key": "value", "number": 42}
            }
            
            job = await job_manager.create_job(**job_data)
            
            # Verify job was created with correct status
            assert job.status == JobStatus.PENDING
            assert job.name == "test_job"
            assert job.payload == {"key": "value", "number": 42}
            assert job.id is not None
            
            # Submit job to queue
            await job_manager.submit_job(job.id)
            
            # Verify job is now queued
            queued_job = await job_manager.get_job(job.id)
            assert queued_job.status == JobStatus.QUEUED
            
            # Process the job (simulate worker picking it up)
            await job_manager.start_job(job.id)
            
            # Verify job is running
            running_job = await job_manager.get_job(job.id)
            assert running_job.status == JobStatus.RUNNING
            
            # Complete the job
            result = {"result": "success", "processed_count": 1}
            await job_manager.complete_job(job.id, result)
            
            # Verify job completed successfully
            completed_job = await job_manager.get_job(job.id)
            assert completed_job.status == JobStatus.COMPLETED
            assert completed_job.result == result
            
        finally:
            await job_manager.stop()

    @pytest.mark.asyncio
    async def test_job_failure_scenario(self) -> None:
        """Test job failure handling in complete lifecycle."""
        factory = JobManagerFactory()
        job_manager = factory.create(JobManagerType.MEMORY)
        
        await job_manager.start()
        
        try:
            # Create and submit job
            job = await job_manager.create_job(
                name="failing_job",
                job_type=JobType.ASYNC,
                payload={"action": "fail"}
            )
            
            await job_manager.submit_job(job.id)
            await job_manager.start_job(job.id)
            
            # Fail the job
            error_info = {"error": "Simulated failure", "code": 500}
            await job_manager.fail_job(job.id, error_info)
            
            # Verify job failed
            failed_job = await job_manager.get_job(job.id)
            assert failed_job.status == JobStatus.FAILED
            assert failed_job.error == error_info
            
        finally:
            await job_manager.stop()


class TestJobPubSubIntegration:
    """E2E tests for job system pubsub functionality."""

    @pytest.mark.asyncio
    async def test_job_event_publishing(self) -> None:
        """Test that job events are properly published to subscribers."""
        factory = JobManagerFactory()
        job_manager = factory.create(JobManagerType.MEMORY)
        
        # Track received events
        received_events: list[dict[str, Any]] = []
        
        async def event_handler(event: dict[str, Any]) -> None:
            """Handle job events."""
            received_events.append(event)
        
        # Subscribe to job events
        await job_manager.subscribe_to_events(event_handler)
        
        await job_manager.start()
        
        try:
            # Create and process a job
            job = await job_manager.create_job(
                name="pubsub_test_job",
                job_type=JobType.ASYNC,
                payload={"test": "pubsub"}
            )
            
            await job_manager.submit_job(job.id)
            await job_manager.start_job(job.id)
            await job_manager.complete_job(job.id, {"status": "done"})
            
            # Allow time for events to be processed
            await asyncio.sleep(0.1)
            
            # Verify events were published
            assert len(received_events) >= 4  # created, queued, started, completed
            
            event_types = [event["type"] for event in received_events]
            assert "job_created" in event_types
            assert "job_queued" in event_types
            assert "job_started" in event_types
            assert "job_completed" in event_types
            
            # Verify event data
            for event in received_events:
                assert event["job_id"] == job.id
                assert "timestamp" in event
                
        finally:
            await job_manager.stop()

    @pytest.mark.asyncio
    async def test_multiple_subscribers(self) -> None:
        """Test multiple subscribers can receive job events."""
        factory = JobManagerFactory()
        job_manager = factory.create(JobManagerType.MEMORY)
        
        subscriber1_events: list[dict[str, Any]] = []
        subscriber2_events: list[dict[str, Any]] = []
        
        async def subscriber1(event: dict[str, Any]) -> None:
            subscriber1_events.append(event)
        
        async def subscriber2(event: dict[str, Any]) -> None:
            subscriber2_events.append(event)
        
        await job_manager.subscribe_to_events(subscriber1)
        await job_manager.subscribe_to_events(subscriber2)
        
        await job_manager.start()
        
        try:
            job = await job_manager.create_job(
                name="multi_subscriber_test",
                job_type=JobType.ASYNC,
                payload={}
            )
            
            await job_manager.submit_job(job.id)
            await asyncio.sleep(0.1)
            
            # Both subscribers should receive events
            assert len(subscriber1_events) > 0
            assert len(subscriber2_events) > 0
            assert len(subscriber1_events) == len(subscriber2_events)
            
        finally:
            await job_manager.stop()