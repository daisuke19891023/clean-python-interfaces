"""API tests for function registration and execution endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestFunctionAPI:
    """API tests for function management endpoints."""

    @pytest.fixture
    def client(self, monkeypatch: pytest.MonkeyPatch) -> TestClient:
        """Create test client with RestAPI interface."""
        # Set environment variable to use RestAPI interface
        monkeypatch.setenv("INTERFACE_TYPE", "restapi")

        # Import here to ensure environment variable is set
        from clean_interfaces.interfaces.factory import InterfaceFactory
        from clean_interfaces.interfaces.restapi import RestAPIInterface
        from clean_interfaces.types import InterfaceType

        factory = InterfaceFactory()
        interface = factory.create(InterfaceType.RESTAPI)

        # Type narrow to RestAPIInterface to access app attribute
        assert isinstance(interface, RestAPIInterface)

        return TestClient(interface.app)

    def test_register_async_function_endpoint(self, client: TestClient) -> None:
        """Test async function registration endpoint."""
        function_data = {
            "name": "test_async_func",
            "code": """
async def test_async_func(x: int) -> int:
    return x * 2
""",
            "is_async": True,
        }
        
        response = client.post("/api/v1/functions/register", json=function_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test_async_func"
        assert data["is_async"] is True
        assert "registered_at" in data

    def test_register_sync_function_endpoint(self, client: TestClient) -> None:
        """Test sync function registration endpoint."""
        function_data = {
            "name": "test_sync_func",
            "code": """
def test_sync_func(x: int) -> int:
    return x + 10
""",
            "is_async": False,
        }
        
        response = client.post("/api/v1/functions/register", json=function_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "test_sync_func"
        assert data["is_async"] is False
        assert "registered_at" in data

    def test_register_function_validation_errors(self, client: TestClient) -> None:
        """Test function registration validation errors."""
        # Test missing name
        response = client.post("/api/v1/functions/register", json={
            "code": "def test(): pass",
            "is_async": False,
        })
        assert response.status_code == 422

        # Test missing code
        response = client.post("/api/v1/functions/register", json={
            "name": "test_func",
            "is_async": False,
        })
        assert response.status_code == 422

        # Test invalid code
        response = client.post("/api/v1/functions/register", json={
            "name": "invalid_func",
            "code": "this is not valid python code",
            "is_async": False,
        })
        assert response.status_code == 400
        assert "syntax" in response.json()["detail"].lower()

    def test_register_duplicate_function_name(self, client: TestClient) -> None:
        """Test registering function with duplicate name."""
        function_data = {
            "name": "duplicate_func",
            "code": "def duplicate_func(): return 1",
            "is_async": False,
        }
        
        # First registration should succeed
        response1 = client.post("/api/v1/functions/register", json=function_data)
        assert response1.status_code == 201

        # Second registration with same name should fail
        response2 = client.post("/api/v1/functions/register", json=function_data)
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()

    def test_list_functions_endpoint(self, client: TestClient) -> None:
        """Test listing registered functions."""
        # Initially empty
        response = client.get("/api/v1/functions")
        assert response.status_code == 200
        data = response.json()
        assert "functions" in data
        initial_count = len(data["functions"])

        # Register a function
        function_data = {
            "name": "list_test_func",
            "code": "def list_test_func(): return 'test'",
            "is_async": False,
        }
        client.post("/api/v1/functions/register", json=function_data)

        # List should now include the function
        response = client.get("/api/v1/functions")
        assert response.status_code == 200
        data = response.json()
        assert len(data["functions"]) == initial_count + 1
        function_names = [f["name"] for f in data["functions"]]
        assert "list_test_func" in function_names

    def test_execute_registered_function_endpoint(self, client: TestClient) -> None:
        """Test function execution endpoint."""
        # Register a function first
        function_data = {
            "name": "math_func",
            "code": """
def math_func(a: int, b: int, operation: str = "add") -> int:
    if operation == "add":
        return a + b
    elif operation == "multiply":
        return a * b
    else:
        return 0
""",
            "is_async": False,
        }
        client.post("/api/v1/functions/register", json=function_data)

        # Execute with positional args
        response = client.post(
            "/api/v1/functions/math_func/execute",
            json={"args": [5, 3], "kwargs": {}}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 8
        assert data["execution_time"] > 0

        # Execute with keyword args
        response = client.post(
            "/api/v1/functions/math_func/execute",
            json={"args": [5, 3], "kwargs": {"operation": "multiply"}}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["result"] == 15

    def test_execute_nonexistent_function(self, client: TestClient) -> None:
        """Test executing a function that doesn't exist."""
        response = client.post(
            "/api/v1/functions/nonexistent_func/execute",
            json={"args": [], "kwargs": {}}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_execute_function_with_error(self, client: TestClient) -> None:
        """Test executing a function that raises an error."""
        # Register a function that raises an error
        function_data = {
            "name": "error_func",
            "code": """
def error_func():
    raise RuntimeError("Test error message")
""",
            "is_async": False,
        }
        client.post("/api/v1/functions/register", json=function_data)

        # Execute the function
        response = client.post(
            "/api/v1/functions/error_func/execute",
            json={"args": [], "kwargs": {}}
        )
        assert response.status_code == 500
        data = response.json()
        assert "error" in data["detail"]
        assert data["detail"]["error_type"] == "RuntimeError"

    def test_delete_function_endpoint(self, client: TestClient) -> None:
        """Test function deletion endpoint."""
        # Register a function first
        function_data = {
            "name": "delete_test_func",
            "code": "def delete_test_func(): return 'delete me'",
            "is_async": False,
        }
        client.post("/api/v1/functions/register", json=function_data)

        # Delete the function
        response = client.delete("/api/v1/functions/delete_test_func")
        assert response.status_code == 204

        # Verify function is deleted
        list_response = client.get("/api/v1/functions")
        function_names = [f["name"] for f in list_response.json()["functions"]]
        assert "delete_test_func" not in function_names

    def test_delete_nonexistent_function(self, client: TestClient) -> None:
        """Test deleting a function that doesn't exist."""
        response = client.delete("/api/v1/functions/nonexistent_func")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_mixed_sync_async_execution(self, client: TestClient) -> None:
        """Test that sync and async functions can be executed without blocking."""
        # Register async function
        async_func_data = {
            "name": "async_sleep_func",
            "code": """
import asyncio
async def async_sleep_func(duration: float) -> str:
    await asyncio.sleep(duration)
    return f"async slept for {duration}s"
""",
            "is_async": True,
        }
        client.post("/api/v1/functions/register", json=async_func_data)

        # Register sync function
        sync_func_data = {
            "name": "sync_sleep_func",
            "code": """
import time
def sync_sleep_func(duration: float) -> str:
    time.sleep(duration)
    return f"sync slept for {duration}s"
""",
            "is_async": False,
        }
        client.post("/api/v1/functions/register", json=sync_func_data)

        # Execute both functions - they should both work without blocking each other
        async_response = client.post(
            "/api/v1/functions/async_sleep_func/execute",
            json={"args": [0.1], "kwargs": {}}
        )
        assert async_response.status_code == 200
        assert "async slept for 0.1s" in async_response.json()["result"]

        sync_response = client.post(
            "/api/v1/functions/sync_sleep_func/execute",
            json={"args": [0.1], "kwargs": {}}
        )
        assert sync_response.status_code == 200
        assert "sync slept for 0.1s" in sync_response.json()["result"]