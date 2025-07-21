"""Tests for function-related models."""

import pytest
from pydantic import ValidationError

from clean_interfaces.models.function import (
    FunctionExecuteRequest,
    FunctionExecuteResponse,
    FunctionRegisterRequest,
    FunctionRegisterResponse,
    FunctionListResponse,
)


class TestFunctionModels:
    """Test function-related Pydantic models."""

    def test_function_register_request_valid(self) -> None:
        """Test FunctionRegisterRequest with valid data."""
        request = FunctionRegisterRequest(
            name="test_func",
            code="def test_func(): return 'test'",
            is_async=False,
        )
        
        assert request.name == "test_func"
        assert request.code == "def test_func(): return 'test'"
        assert request.is_async is False

    def test_function_register_request_validation(self) -> None:
        """Test FunctionRegisterRequest validation."""
        # Missing name
        with pytest.raises(ValidationError):
            FunctionRegisterRequest(
                code="def test(): pass",
                is_async=False,
            )
        
        # Missing code
        with pytest.raises(ValidationError):
            FunctionRegisterRequest(
                name="test_func",
                is_async=False,
            )
        
        # Missing is_async
        with pytest.raises(ValidationError):
            FunctionRegisterRequest(
                name="test_func",
                code="def test(): pass",
            )

    def test_function_register_response(self) -> None:
        """Test FunctionRegisterResponse model."""
        response = FunctionRegisterResponse(
            name="test_func",
            is_async=False,
        )
        
        assert response.name == "test_func"
        assert response.is_async is False
        assert response.registered_at is not None

    def test_function_execute_request_valid(self) -> None:
        """Test FunctionExecuteRequest with valid data."""
        request = FunctionExecuteRequest(
            args=[1, 2, 3],
            kwargs={"option": "value"},
        )
        
        assert request.args == [1, 2, 3]
        assert request.kwargs == {"option": "value"}

    def test_function_execute_request_defaults(self) -> None:
        """Test FunctionExecuteRequest with default values."""
        request = FunctionExecuteRequest()
        
        assert request.args == []
        assert request.kwargs == {}

    def test_function_execute_response(self) -> None:
        """Test FunctionExecuteResponse model."""
        response = FunctionExecuteResponse(
            result={"data": "test"},
            execution_time=0.123,
        )
        
        assert response.result == {"data": "test"}
        assert response.execution_time == 0.123
        assert response.executed_at is not None

    def test_function_list_response(self) -> None:
        """Test FunctionListResponse model."""
        functions = [
            {
                "name": "func1",
                "is_async": False,
                "registered_at": "2023-01-01T00:00:00",
            },
            {
                "name": "func2", 
                "is_async": True,
                "registered_at": "2023-01-01T00:01:00",
            },
        ]
        
        response = FunctionListResponse(functions=functions)
        
        assert len(response.functions) == 2
        assert response.functions[0]["name"] == "func1"
        assert response.functions[1]["name"] == "func2"

    def test_function_execute_request_complex_types(self) -> None:
        """Test FunctionExecuteRequest with complex argument types."""
        complex_args = [
            {"nested": {"data": [1, 2, 3]}},
            [{"item": "value"}],
            "string_arg",
            42,
            3.14,
        ]
        
        complex_kwargs = {
            "config": {"setting1": True, "setting2": "value"},
            "callback": "function_name",
            "options": [1, 2, 3],
        }
        
        request = FunctionExecuteRequest(
            args=complex_args,
            kwargs=complex_kwargs,
        )
        
        assert request.args == complex_args
        assert request.kwargs == complex_kwargs

    def test_function_execute_response_various_result_types(self) -> None:
        """Test FunctionExecuteResponse with various result types."""
        # String result
        response1 = FunctionExecuteResponse(result="string result", execution_time=0.1)
        assert response1.result == "string result"
        
        # Number result
        response2 = FunctionExecuteResponse(result=42, execution_time=0.1)
        assert response2.result == 42
        
        # List result
        response3 = FunctionExecuteResponse(result=[1, 2, 3], execution_time=0.1)
        assert response3.result == [1, 2, 3]
        
        # Dict result
        response4 = FunctionExecuteResponse(result={"key": "value"}, execution_time=0.1)
        assert response4.result == {"key": "value"}
        
        # None result
        response5 = FunctionExecuteResponse(result=None, execution_time=0.1)
        assert response5.result is None

    def test_function_register_request_name_constraints(self) -> None:
        """Test function name constraints in register request."""
        # Valid names should work
        valid_names = ["func", "func_name", "functionName", "func123", "_private_func"]
        
        for name in valid_names:
            request = FunctionRegisterRequest(
                name=name,
                code="def func(): pass",
                is_async=False,
            )
            assert request.name == name

    def test_function_models_json_serialization(self) -> None:
        """Test that function models can be serialized to/from JSON."""
        # Register request
        register_req = FunctionRegisterRequest(
            name="test_func",
            code="def test_func(): return 1",
            is_async=False,
        )
        
        json_data = register_req.model_dump()
        restored = FunctionRegisterRequest(**json_data)
        assert restored.name == register_req.name
        assert restored.code == register_req.code
        assert restored.is_async == register_req.is_async

        # Execute request
        execute_req = FunctionExecuteRequest(
            args=[1, "test"],
            kwargs={"option": True},
        )
        
        json_data = execute_req.model_dump()
        restored = FunctionExecuteRequest(**json_data)
        assert restored.args == execute_req.args
        assert restored.kwargs == execute_req.kwargs

        # Execute response
        execute_resp = FunctionExecuteResponse(
            result={"output": "test"},
            execution_time=0.5,
        )
        
        json_data = execute_resp.model_dump()
        restored = FunctionExecuteResponse(**json_data)
        assert restored.result == execute_resp.result
        assert restored.execution_time == execute_resp.execution_time