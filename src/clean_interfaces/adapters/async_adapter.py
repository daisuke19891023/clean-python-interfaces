"""Async adapter for executing both sync and async functions without blocking."""

import asyncio
import inspect
from typing import Any, Callable


class AsyncFunctionAdapter:
    """Adapter for executing both sync and async functions in async context."""

    def __init__(self) -> None:
        """Initialize the async function adapter."""
        self._executor = None

    async def execute(
        self,
        function: Callable[..., Any],
        args: list[Any],
        kwargs: dict[str, Any],
    ) -> Any:
        """Execute a function (sync or async) in async context.
        
        Args:
            function: The function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            
        Returns:
            The result of the function execution
            
        Raises:
            Any exception raised by the function
        """
        if self._is_async_function(function):
            # Execute async function directly
            return await function(*args, **kwargs)
        else:
            # Execute sync function in thread executor to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self._executor,
                self._execute_sync_function,
                function,
                args,
                kwargs,
            )

    def _is_async_function(self, function: Callable[..., Any]) -> bool:
        """Check if a function is async.
        
        Args:
            function: Function to check
            
        Returns:
            True if function is async, False otherwise
        """
        return inspect.iscoroutinefunction(function)

    def _execute_sync_function(
        self,
        function: Callable[..., Any],
        args: list[Any],
        kwargs: dict[str, Any],
    ) -> Any:
        """Execute a sync function with given arguments.
        
        This method is designed to be called from run_in_executor.
        
        Args:
            function: The sync function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            
        Returns:
            The result of the function execution
        """
        return function(*args, **kwargs)