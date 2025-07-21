"""Tests for async adapter functionality."""

import asyncio
import time
from typing import Any, Callable
from unittest.mock import MagicMock, patch

import pytest

from clean_interfaces.adapters.async_adapter import AsyncFunctionAdapter


class TestAsyncFunctionAdapter:
    """Test async function adapter functionality."""

    @pytest.fixture
    def adapter(self) -> AsyncFunctionAdapter:
        """Create an AsyncFunctionAdapter instance."""
        return AsyncFunctionAdapter()

    def test_adapter_initialization(self, adapter: AsyncFunctionAdapter) -> None:
        """Test that adapter initializes correctly."""
        assert adapter is not None
        assert hasattr(adapter, "execute")

    @pytest.mark.asyncio
    async def test_async_adapter_async_function(self, adapter: AsyncFunctionAdapter) -> None:
        """Test adapter handles async functions directly."""
        async def test_async_func(x: int, y: int) -> int:
            await asyncio.sleep(0.01)  # Simulate async work
            return x + y

        result = await adapter.execute(test_async_func, [5, 3], {})
        
        assert result == 8

    @pytest.mark.asyncio
    async def test_async_adapter_sync_function(self, adapter: AsyncFunctionAdapter) -> None:
        """Test adapter handles sync functions in executor."""
        def test_sync_func(x: int, y: int) -> int:
            time.sleep(0.01)  # Simulate blocking work
            return x * y

        result = await adapter.execute(test_sync_func, [5, 3], {})
        
        assert result == 15

    @pytest.mark.asyncio 
    async def test_adapter_with_kwargs(self, adapter: AsyncFunctionAdapter) -> None:
        """Test adapter handles keyword arguments correctly."""
        def test_func_with_kwargs(a: int, b: int, operation: str = "add") -> int:
            if operation == "add":
                return a + b
            elif operation == "multiply":
                return a * b
            return 0

        # Test with positional args only
        result1 = await adapter.execute(test_func_with_kwargs, [5, 3], {})
        assert result1 == 8

        # Test with kwargs
        result2 = await adapter.execute(test_func_with_kwargs, [5, 3], {"operation": "multiply"})
        assert result2 == 15

    @pytest.mark.asyncio
    async def test_adapter_handles_function_errors(self, adapter: AsyncFunctionAdapter) -> None:
        """Test adapter properly propagates function errors."""
        def error_func() -> None:
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            await adapter.execute(error_func, [], {})

    @pytest.mark.asyncio
    async def test_adapter_handles_async_function_errors(self, adapter: AsyncFunctionAdapter) -> None:
        """Test adapter properly propagates async function errors."""
        async def async_error_func() -> None:
            raise RuntimeError("Async test error")

        with pytest.raises(RuntimeError, match="Async test error"):
            await adapter.execute(async_error_func, [], {})

    @pytest.mark.asyncio
    async def test_adapter_preserves_return_types(self, adapter: AsyncFunctionAdapter) -> None:
        """Test adapter preserves different return types."""
        def string_func() -> str:
            return "hello"

        def dict_func() -> dict[str, int]:
            return {"value": 42}

        def list_func() -> list[int]:
            return [1, 2, 3]

        async def async_none_func() -> None:
            return None

        assert await adapter.execute(string_func, [], {}) == "hello"
        assert await adapter.execute(dict_func, [], {}) == {"value": 42}
        assert await adapter.execute(list_func, [], {}) == [1, 2, 3]
        assert await adapter.execute(async_none_func, [], {}) is None

    @pytest.mark.asyncio
    async def test_adapter_concurrent_execution(self, adapter: AsyncFunctionAdapter) -> None:
        """Test adapter can handle concurrent executions without blocking."""
        def slow_sync_func(delay: float, result: int) -> int:
            time.sleep(delay)
            return result

        async def slow_async_func(delay: float, result: int) -> int:
            await asyncio.sleep(delay)
            return result

        # Execute multiple functions concurrently
        start_time = time.time()
        
        tasks = [
            adapter.execute(slow_sync_func, [0.1, 1], {}),
            adapter.execute(slow_sync_func, [0.1, 2], {}),
            adapter.execute(slow_async_func, [0.1, 3], {}),
            adapter.execute(slow_async_func, [0.1, 4], {}),
        ]
        
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time
        
        # Results should be correct
        assert sorted(results) == [1, 2, 3, 4]
        
        # Total time should be closer to 0.1s (concurrent) than 0.4s (sequential)
        assert total_time < 0.3  # Allow some overhead

    @pytest.mark.asyncio
    async def test_adapter_executor_usage(self, adapter: AsyncFunctionAdapter) -> None:
        """Test that sync functions are executed in thread executor."""
        def sync_func() -> str:
            return "sync result"

        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = MagicMock()
            mock_get_loop.return_value = mock_loop
            mock_loop.run_in_executor.return_value = asyncio.Future()
            mock_loop.run_in_executor.return_value.set_result("sync result")

            result = await adapter.execute(sync_func, [], {})
            
            # Verify run_in_executor was called for sync function
            mock_loop.run_in_executor.assert_called_once()
            assert result == "sync result"

    def test_adapter_detects_async_functions(self, adapter: AsyncFunctionAdapter) -> None:
        """Test adapter correctly detects async vs sync functions."""
        def sync_func() -> None:
            pass

        async def async_func() -> None:
            pass

        assert adapter._is_async_function(async_func) is True
        assert adapter._is_async_function(sync_func) is False

    @pytest.mark.asyncio
    async def test_adapter_with_complex_arguments(self, adapter: AsyncFunctionAdapter) -> None:
        """Test adapter handles complex argument types."""
        def complex_func(
            data: dict[str, Any], 
            items: list[int], 
            callback: Callable[[int], int] | None = None
        ) -> dict[str, Any]:
            result = {
                "data_keys": list(data.keys()),
                "items_sum": sum(items),
            }
            if callback:
                result["callback_result"] = callback(10)
            return result

        test_data = {"key1": "value1", "key2": "value2"}
        test_items = [1, 2, 3, 4, 5]
        test_callback = lambda x: x * 2

        result = await adapter.execute(
            complex_func, 
            [test_data, test_items], 
            {"callback": test_callback}
        )
        
        assert result["data_keys"] == ["key1", "key2"]
        assert result["items_sum"] == 15
        assert result["callback_result"] == 20