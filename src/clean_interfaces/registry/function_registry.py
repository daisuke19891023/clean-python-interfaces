"""Function registry for managing registered functions."""

import ast
import re
from datetime import UTC, datetime
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field


class FunctionRegistryError(Exception):
    """Exception raised when function registry operations fail."""


class FunctionInfo(BaseModel):
    """Information about a registered function."""

    name: str = Field(
        ...,
        description="Name of the function",
    )
    function: Callable[..., Any] = Field(
        ...,
        description="The actual function object",
    )
    is_async: bool = Field(
        ...,
        description="Whether the function is async or sync",
    )
    code: str = Field(
        ...,
        description="Source code of the function",
    )
    registered_at: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="Timestamp when the function was registered",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class FunctionRegistry:
    """Registry for managing dynamically registered functions."""

    def __init__(self) -> None:
        """Initialize the function registry."""
        self._functions: dict[str, FunctionInfo] = {}

    def register_function(self, name: str, code: str, is_async: bool) -> FunctionInfo:
        """Register a function in the registry.
        
        Args:
            name: Name of the function
            code: Python code containing the function definition
            is_async: Whether the function is async or sync
            
        Returns:
            FunctionInfo: Information about the registered function
            
        Raises:
            FunctionRegistryError: If registration fails
        """
        # Validate function name
        self._validate_function_name(name)
        
        # Check if function already exists
        if name in self._functions:
            raise FunctionRegistryError(f"Function '{name}' already exists")
        
        # Parse and compile the code
        function = self._compile_function(name, code)
        
        # Create function info
        function_info = FunctionInfo(
            name=name,
            function=function,
            is_async=is_async,
            code=code,
        )
        
        # Store in registry
        self._functions[name] = function_info
        
        return function_info

    def get_function(self, name: str) -> FunctionInfo | None:
        """Get a registered function by name.
        
        Args:
            name: Name of the function
            
        Returns:
            FunctionInfo or None if not found
        """
        return self._functions.get(name)

    def list_functions(self) -> list[FunctionInfo]:
        """List all registered functions.
        
        Returns:
            List of FunctionInfo objects
        """
        return list(self._functions.values())

    def delete_function(self, name: str) -> bool:
        """Delete a function from the registry.
        
        Args:
            name: Name of the function to delete
            
        Returns:
            True if function was deleted, False if not found
        """
        if name in self._functions:
            del self._functions[name]
            return True
        return False

    def _validate_function_name(self, name: str) -> None:
        """Validate function name.
        
        Args:
            name: Function name to validate
            
        Raises:
            FunctionRegistryError: If name is invalid
        """
        if not name:
            raise FunctionRegistryError("Function name cannot be empty")
        
        if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
            raise FunctionRegistryError(
                f"Invalid function name '{name}'. Name must be a valid Python identifier"
            )

    def _compile_function(self, name: str, code: str) -> Callable[..., Any]:
        """Compile function code and extract the function.
        
        Args:
            name: Expected function name
            code: Python code containing the function
            
        Returns:
            Compiled function object
            
        Raises:
            FunctionRegistryError: If compilation fails
        """
        try:
            # Parse the code to validate syntax
            parsed = ast.parse(code)
        except SyntaxError as e:
            raise FunctionRegistryError(f"Syntax error in function code: {e}") from e
        
        # Create namespace for execution with common imports
        namespace: dict[str, Any] = {
            "asyncio": __import__("asyncio"),
            "time": __import__("time"),
        }
        
        try:
            # Execute the code to define the function
            exec(code, namespace)  # noqa: S102
        except Exception as e:
            raise FunctionRegistryError(f"Error compiling function: {e}") from e
        
        # Extract the function from the namespace
        if name not in namespace:
            raise FunctionRegistryError(
                f"Function '{name}' not found in code. "
                "Make sure the function name matches the provided name."
            )
        
        function = namespace[name]
        
        if not callable(function):
            raise FunctionRegistryError(
                f"'{name}' is not a callable function"
            )
        
        return function