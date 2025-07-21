"""Unit tests for job system settings."""

import pytest
from unittest.mock import patch
from pydantic import ValidationError

from clean_interfaces.jobs.types import JobManagerType
from clean_interfaces.utils.settings import JobSettings, get_job_settings, reset_job_settings


class TestJobSettings:
    """Unit tests for JobSettings configuration."""

    def teardown_method(self) -> None:
        """Reset settings after each test."""
        reset_job_settings()

    def test_job_settings_default_values(self) -> None:
        """Test JobSettings default configuration values."""
        settings = JobSettings()
        
        assert settings.job_manager_type == "memory"
        assert settings.max_concurrent_jobs == 10
        assert settings.job_timeout_seconds == 3600
        assert settings.queue_size_limit == 1000
        assert settings.cleanup_completed_jobs_after_seconds == 86400

    def test_job_settings_validation_valid_manager_type(self) -> None:
        """Test validation accepts valid job manager types."""
        valid_types = ["memory"]
        
        for manager_type in valid_types:
            settings = JobSettings(job_manager_type=manager_type)
            assert settings.job_manager_type == manager_type

    def test_job_settings_validation_invalid_manager_type(self) -> None:
        """Test validation rejects invalid job manager types."""
        with pytest.raises(ValidationError) as exc_info:
            JobSettings(job_manager_type="invalid_type")
        
        errors = exc_info.value.errors()
        assert any(
            error["loc"] == ("job_manager_type",) and "Invalid job manager type" in error["msg"]
            for error in errors
        )

    def test_job_settings_case_insensitive_manager_type(self) -> None:
        """Test job manager type validation is case insensitive."""
        settings = JobSettings(job_manager_type="MEMORY")
        assert settings.job_manager_type == "memory"

    def test_job_settings_positive_integer_validation(self) -> None:
        """Test positive integer field validation."""
        # Valid positive integers
        settings = JobSettings(
            max_concurrent_jobs=5,
            job_timeout_seconds=1800,
            queue_size_limit=500,
            cleanup_completed_jobs_after_seconds=43200
        )
        
        assert settings.max_concurrent_jobs == 5
        assert settings.job_timeout_seconds == 1800
        assert settings.queue_size_limit == 500
        assert settings.cleanup_completed_jobs_after_seconds == 43200

    def test_job_settings_invalid_negative_values(self) -> None:
        """Test validation rejects negative values."""
        with pytest.raises(ValidationError):
            JobSettings(max_concurrent_jobs=-1)
        
        with pytest.raises(ValidationError):
            JobSettings(job_timeout_seconds=-10)
        
        with pytest.raises(ValidationError):
            JobSettings(queue_size_limit=-5)
        
        with pytest.raises(ValidationError):
            JobSettings(cleanup_completed_jobs_after_seconds=-100)

    def test_job_settings_invalid_zero_values(self) -> None:
        """Test validation rejects zero values where inappropriate."""
        with pytest.raises(ValidationError):
            JobSettings(max_concurrent_jobs=0)
        
        with pytest.raises(ValidationError):
            JobSettings(job_timeout_seconds=0)
        
        with pytest.raises(ValidationError):
            JobSettings(queue_size_limit=0)

    def test_job_settings_zero_cleanup_allowed(self) -> None:
        """Test zero cleanup seconds is allowed (means no cleanup)."""
        settings = JobSettings(cleanup_completed_jobs_after_seconds=0)
        assert settings.cleanup_completed_jobs_after_seconds == 0

    def test_job_settings_manager_type_enum_property(self) -> None:
        """Test job_manager_type_enum property returns correct enum."""
        settings = JobSettings(job_manager_type="memory")
        
        assert settings.job_manager_type_enum == JobManagerType.MEMORY
        assert isinstance(settings.job_manager_type_enum, JobManagerType)

    def test_job_settings_from_environment_variables(self) -> None:
        """Test JobSettings can be configured from environment variables."""
        env_vars = {
            "JOB_MANAGER_TYPE": "memory",
            "MAX_CONCURRENT_JOBS": "20",
            "JOB_TIMEOUT_SECONDS": "7200",
            "QUEUE_SIZE_LIMIT": "2000",
            "CLEANUP_COMPLETED_JOBS_AFTER_SECONDS": "172800"
        }
        
        with patch.dict("os.environ", env_vars):
            settings = JobSettings()
            
            assert settings.job_manager_type == "memory"
            assert settings.max_concurrent_jobs == 20
            assert settings.job_timeout_seconds == 7200
            assert settings.queue_size_limit == 2000
            assert settings.cleanup_completed_jobs_after_seconds == 172800

    def test_job_settings_serialization(self) -> None:
        """Test JobSettings model serialization."""
        settings = JobSettings(
            job_manager_type="memory",
            max_concurrent_jobs=15,
            job_timeout_seconds=1800
        )
        
        settings_dict = settings.model_dump()
        
        assert settings_dict["job_manager_type"] == "memory"
        assert settings_dict["max_concurrent_jobs"] == 15
        assert settings_dict["job_timeout_seconds"] == 1800
        assert "job_manager_type_enum" in settings_dict

    def test_job_settings_deserialization(self) -> None:
        """Test JobSettings model deserialization."""
        settings_data = {
            "job_manager_type": "memory",
            "max_concurrent_jobs": 25,
            "job_timeout_seconds": 900,
            "queue_size_limit": 500,
            "cleanup_completed_jobs_after_seconds": 3600
        }
        
        settings = JobSettings.model_validate(settings_data)
        
        assert settings.job_manager_type == "memory"
        assert settings.max_concurrent_jobs == 25
        assert settings.job_timeout_seconds == 900
        assert settings.queue_size_limit == 500
        assert settings.cleanup_completed_jobs_after_seconds == 3600

    def test_job_settings_field_descriptions(self) -> None:
        """Test JobSettings fields have proper descriptions."""
        schema = JobSettings.model_json_schema()
        properties = schema["properties"]
        
        # Check that important fields have descriptions
        assert "description" in properties["job_manager_type"]
        assert "description" in properties["max_concurrent_jobs"]
        assert "description" in properties["job_timeout_seconds"]
        assert "description" in properties["queue_size_limit"]

    def test_job_settings_model_config(self) -> None:
        """Test JobSettings model configuration."""
        # Settings should be configured to read from .env
        assert JobSettings.model_config.env_file == ".env"
        assert JobSettings.model_config.case_sensitive is False
        assert JobSettings.model_config.extra == "ignore"


class TestJobSettingsGlobalInstance:
    """Unit tests for global job settings instance management."""

    def teardown_method(self) -> None:
        """Reset settings after each test."""
        reset_job_settings()

    def test_get_job_settings_singleton(self) -> None:
        """Test get_job_settings returns singleton instance."""
        settings1 = get_job_settings()
        settings2 = get_job_settings()
        
        # Should be the same instance
        assert settings1 is settings2

    def test_get_job_settings_creates_instance(self) -> None:
        """Test get_job_settings creates instance on first call."""
        # Ensure no instance exists
        reset_job_settings()
        
        settings = get_job_settings()
        
        assert settings is not None
        assert isinstance(settings, JobSettings)

    def test_reset_job_settings_clears_instance(self) -> None:
        """Test reset_job_settings clears the global instance."""
        # Create instance
        settings1 = get_job_settings()
        
        # Reset
        reset_job_settings()
        
        # Get new instance
        settings2 = get_job_settings()
        
        # Should be different instances
        assert settings1 is not settings2

    def test_job_settings_instance_with_environment(self) -> None:
        """Test global instance picks up environment variables."""
        env_vars = {
            "JOB_MANAGER_TYPE": "memory",
            "MAX_CONCURRENT_JOBS": "5"
        }
        
        reset_job_settings()
        
        with patch.dict("os.environ", env_vars):
            settings = get_job_settings()
            
            assert settings.job_manager_type == "memory"
            assert settings.max_concurrent_jobs == 5

    def test_job_settings_thread_safety(self) -> None:
        """Test job settings singleton is thread-safe."""
        import threading
        from typing import Any
        
        instances: list[Any] = []
        
        def get_settings() -> None:
            instances.append(get_job_settings())
        
        # Create multiple threads
        threads = [threading.Thread(target=get_settings) for _ in range(10)]
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # All instances should be the same
        assert len(set(id(instance) for instance in instances)) == 1