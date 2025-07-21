"""Factory pattern implementation for creating job managers."""

from clean_interfaces.jobs.base import BaseJobManager
from clean_interfaces.jobs.memory import MemoryJobManager
from clean_interfaces.jobs.types import JobManagerType
from clean_interfaces.utils.settings import get_job_settings


class JobManagerFactory:
    """Factory for creating job manager instances."""

    def create(self, manager_type: JobManagerType) -> BaseJobManager:
        """Create a job manager instance based on the type.

        Args:
            manager_type: The type of job manager to create

        Returns:
            BaseJobManager: The created job manager instance

        Raises:
            ValueError: If the job manager type is unknown
        """
        if manager_type == JobManagerType.MEMORY:
            return MemoryJobManager()

        msg = f"Unknown job manager type: {manager_type}"
        raise ValueError(msg)

    def create_from_settings(self) -> BaseJobManager:
        """Create a job manager instance from settings.

        Returns:
            BaseJobManager: The created job manager instance
        """
        settings = get_job_settings()
        manager_type = JobManagerType(settings.job_manager_type)
        return self.create(manager_type)