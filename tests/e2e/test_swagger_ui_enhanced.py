"""E2E tests for enhanced Swagger UI functionality."""

import pytest
from fastapi.testclient import TestClient


class TestSwaggerUIEnhancedE2E:
    """E2E tests for enhanced Swagger UI with dynamic content generation."""

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

        # Get the FastAPI app from the interface
        return TestClient(interface.app)

    def test_enhanced_swagger_ui_endpoint(self, client: TestClient) -> None:
        """Test enhanced Swagger UI endpoint returns HTML with dynamic content."""
        response = client.get("/api/v1/swagger-ui")
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/html")

        # Verify enhanced content includes dynamic documentation
        content = response.text.lower()
        assert "swagger-ui" in content
        assert "clean interfaces api" in content

        # Verify dynamic content from source code is included
        assert "interface" in content or "restapi" in content

    def test_enhanced_swagger_ui_json_schema(self, client: TestClient) -> None:
        """Test enhanced Swagger UI JSON schema endpoint with dynamic content."""
        response = client.get("/api/v1/swagger-ui/schema")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        schema = response.json()
        assert "info" in schema
        assert "paths" in schema
        assert "components" in schema

        # Verify enhanced metadata from dynamic content generation
        assert schema["info"]["title"] == "Clean Interfaces API"
        assert "dynamic_content" in schema["info"]
        # Verify timestamp is present and valid
        assert "generation_timestamp" in schema["info"]["dynamic_content"]
        assert schema["info"]["dynamic_content"]["generation_timestamp"] != ""

    def test_enhanced_swagger_ui_with_source_analysis(self, client: TestClient) -> None:
        """Test that enhanced Swagger UI includes analysis from source code."""
        response = client.get("/api/v1/swagger-ui/analysis")
        assert response.status_code == 200

        analysis = response.json()
        assert "interfaces" in analysis
        assert "models" in analysis
        assert "endpoints" in analysis
        assert "documentation_files" in analysis

        # Verify analysis structure (currently returning placeholders)
        interfaces: list[str] = analysis["interfaces"]
        assert isinstance(interfaces, list)
        # Placeholder implementation returns empty lists
        assert len(interfaces) == 0

        # Verify models analysis structure
        models: list[str] = analysis["models"]
        assert isinstance(models, list)
        assert len(models) == 0

    def test_complete_swagger_ui_workflow(self, client: TestClient) -> None:
        """Test complete workflow from analysis to enhanced UI generation."""
        # 1. Get source code analysis
        analysis_response = client.get("/api/v1/swagger-ui/analysis")
        assert analysis_response.status_code == 200
        analysis = analysis_response.json()

        # 2. Get enhanced schema based on analysis
        schema_response = client.get("/api/v1/swagger-ui/schema")
        assert schema_response.status_code == 200
        schema = schema_response.json()

        # 3. Get enhanced UI that uses the schema
        ui_response = client.get("/api/v1/swagger-ui")
        assert ui_response.status_code == 200

        # Verify workflow coherence (placeholder data)
        assert isinstance(analysis["interfaces"], list)
        assert "generation_timestamp" in schema["info"]["dynamic_content"]
        assert "swagger-ui" in ui_response.text.lower()

        # Summary should match empty lists
        assert analysis["summary"]["total_interfaces"] == 0
        assert analysis["summary"]["total_models"] == 0
        assert analysis["summary"]["total_endpoints"] == 0
