"""Tests for function registry functionality."""

import inspect
from datetime import datetime
from typing import Any, Callable

import pytest

from clean_interfaces.registry.function_registry import (
    FunctionInfo,
    FunctionRegistry,
    FunctionRegistryError,
)


class TestFunctionInfo:
    """Test FunctionInfo model."""

    def test_function_info_creation(self) -> None:
        """Test FunctionInfo can be created with valid data."""
        def test_func() -> str:
            return "test"

        info = FunctionInfo(
            name="test_func",
            function=test_func,
            is_async=False,
            code="def test_func(): return 'test'",
        )
        
        assert info.name == "test_func"
        assert info.function == test_func
        assert info.is_async is False
        assert info.code == "def test_func(): return 'test'"
        assert isinstance(info.registered_at, datetime)

    def test_function_info_with_async_function(self) -> None:
        """Test FunctionInfo with async function."""
        async def async_test_func() -> str:
            return "async test"

        info = FunctionInfo(
            name="async_test_func",
            function=async_test_func,
            is_async=True,
            code="async def async_test_func(): return 'async test'",
        )
        
        assert info.is_async is True
        assert inspect.iscoroutinefunction(info.function)


class TestFunctionRegistry:
    """Test function registry functionality."""

    @pytest.fixture
    def registry(self) -> FunctionRegistry:
        """Create a fresh FunctionRegistry instance."""
        return FunctionRegistry()

    def test_registry_initialization(self, registry: FunctionRegistry) -> None:
        """Test registry initializes empty."""
        assert len(registry.list_functions()) == 0

    def test_register_sync_function(self, registry: FunctionRegistry) -> None:
        """Test registering a sync function."""
        code = "def test_func(x: int) -> int:\n    return x * 2"
        
        function_info = registry.register_function("test_func", code, is_async=False)
        
        assert function_info.name == "test_func"
        assert function_info.is_async is False
        assert callable(function_info.function)
        assert function_info.code == code

    def test_register_async_function(self, registry: FunctionRegistry) -> None:
        """Test registering an async function."""
        code = "async def async_test_func(x: int) -> int:\n    return x * 3"
        
        function_info = registry.register_function("async_test_func", code, is_async=True)
        
        assert function_info.name == "async_test_func"
        assert function_info.is_async is True
        assert inspect.iscoroutinefunction(function_info.function)
        assert function_info.code == code

    def test_register_duplicate_function_name(self, registry: FunctionRegistry) -> None:
        """Test registering function with duplicate name raises error."""
        code = "def duplicate_func(): return 1"
        
        # First registration should succeed
        registry.register_function("duplicate_func", code, is_async=False)
        
        # Second registration with same name should fail
        with pytest.raises(FunctionRegistryError, match="already exists"):
            registry.register_function("duplicate_func", code, is_async=False)

    def test_register_invalid_syntax(self, registry: FunctionRegistry) -> None:
        """Test registering function with invalid syntax raises error."""
        invalid_code = "this is not valid python code"
        
        with pytest.raises(FunctionRegistryError, match="syntax"):
            registry.register_function("invalid_func", invalid_code, is_async=False)

    def test_register_function_compilation_error(self, registry: FunctionRegistry) -> None:
        """Test registering function that fails to compile raises error."""
        # Valid syntax but invalid function definition
        invalid_code = "x = 1"  # Not a function definition
        
        with pytest.raises(FunctionRegistryError, match="function"):
            registry.register_function("not_a_func", invalid_code, is_async=False)

    def test_get_function(self, registry: FunctionRegistry) -> None:
        """Test retrieving registered function."""
        code = "def get_test_func(): return 'found'"
        
        registry.register_function("get_test_func", code, is_async=False)
        function_info = registry.get_function("get_test_func")
        
        assert function_info is not None
        assert function_info.name == "get_test_func"
        assert function_info.function() == "found"

    def test_get_nonexistent_function(self, registry: FunctionRegistry) -> None:
        """Test retrieving non-existent function returns None."""
        function_info = registry.get_function("nonexistent_func")
        assert function_info is None

    def test_list_functions(self, registry: FunctionRegistry) -> None:
        """Test listing all registered functions."""
        # Initially empty
        assert len(registry.list_functions()) == 0
        
        # Register some functions
        registry.register_function("func1", "def func1(): return 1", is_async=False)
        registry.register_function("func2", "async def func2(): return 2", is_async=True)
        
        functions = registry.list_functions()
        assert len(functions) == 2
        
        function_names = [f.name for f in functions]
        assert "func1" in function_names
        assert "func2" in function_names

    def test_delete_function(self, registry: FunctionRegistry) -> None:
        """Test deleting registered function."""
        code = "def delete_test_func(): return 'delete me'"
        
        registry.register_function("delete_test_func", code, is_async=False)
        assert registry.get_function("delete_test_func") is not None
        
        success = registry.delete_function("delete_test_func")
        assert success is True
        assert registry.get_function("delete_test_func") is None

    def test_delete_nonexistent_function(self, registry: FunctionRegistry) -> None:
        """Test deleting non-existent function returns False."""
        success = registry.delete_function("nonexistent_func")
        assert success is False

    def test_function_execution(self, registry: FunctionRegistry) -> None:
        """Test that registered functions can be executed correctly."""
        # Test sync function
        sync_code = """
def math_func(a: int, b: int, operation: str = "add") -> int:
    if operation == "add":
        return a + b
    elif operation == "multiply":
        return a * b
    return 0
"""
        
        registry.register_function("math_func", sync_code, is_async=False)
        math_func_info = registry.get_function("math_func")
        assert math_func_info is not None
        
        # Test function execution
        result1 = math_func_info.function(5, 3)
        assert result1 == 8
        
        result2 = math_func_info.function(5, 3, operation="multiply")
        assert result2 == 15

    def test_async_function_is_coroutine(self, registry: FunctionRegistry) -> None:
        """Test that registered async functions are coroutines."""
        async_code = """
async def async_math_func(a: int, b: int) -> int:
    return a + b
"""
        
        registry.register_function("async_math_func", async_code, is_async=True)
        async_func_info = registry.get_function("async_math_func")
        assert async_func_info is not None
        
        # Function should be a coroutine function
        assert inspect.iscoroutinefunction(async_func_info.function)

    def test_register_function_with_imports(self, registry: FunctionRegistry) -> None:
        """Test registering function that uses imports."""
        code_with_imports = """
import math

def math_func(x: float) -> float:
    return math.sqrt(x)
"""
        
        registry.register_function("math_func", code_with_imports, is_async=False)
        math_func_info = registry.get_function("math_func")
        assert math_func_info is not None
        
        result = math_func_info.function(16.0)
        assert result == 4.0

    def test_register_function_with_complex_types(self, registry: FunctionRegistry) -> None:
        """Test registering function with complex parameter and return types."""
        complex_code = """
def process_data(data: dict[str, any], multiplier: int = 2) -> dict[str, any]:
    result = {}
    for key, value in data.items():
        if isinstance(value, (int, float)):
            result[key] = value * multiplier
        else:
            result[key] = value
    return result
"""
        
        registry.register_function("process_data", complex_code, is_async=False)
        process_func_info = registry.get_function("process_data")
        assert process_func_info is not None
        
        test_data = {"a": 5, "b": "text", "c": 3.14}
        result = process_func_info.function(test_data)
        
        assert result["a"] == 10
        assert result["b"] == "text"
        assert result["c"] == 6.28

    def test_function_names_validation(self, registry: FunctionRegistry) -> None:
        """Test that function names are validated."""
        # Empty name should fail
        with pytest.raises(FunctionRegistryError, match="name"):
            registry.register_function("", "def func(): pass", is_async=False)
        
        # Name with spaces should fail
        with pytest.raises(FunctionRegistryError, match="name"):
            registry.register_function("invalid name", "def func(): pass", is_async=False)
        
        # Name starting with number should fail
        with pytest.raises(FunctionRegistryError, match="name"):
            registry.register_function("1invalid", "def func(): pass", is_async=False)

    def test_registry_state_persistence(self, registry: FunctionRegistry) -> None:
        """Test that registry maintains state correctly."""
        # Register multiple functions
        for i in range(5):
            code = f"def func_{i}(): return {i}"
            registry.register_function(f"func_{i}", code, is_async=False)
        
        # Verify all functions are present
        functions = registry.list_functions()
        assert len(functions) == 5
        
        # Delete some functions
        registry.delete_function("func_1")
        registry.delete_function("func_3")
        
        # Verify correct functions remain
        remaining_functions = registry.list_functions()
        assert len(remaining_functions) == 3
        
        remaining_names = [f.name for f in remaining_functions]
        assert "func_0" in remaining_names
        assert "func_2" in remaining_names
        assert "func_4" in remaining_names
        assert "func_1" not in remaining_names
        assert "func_3" not in remaining_names