"""Tests for document generator utility."""

from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from clean_interfaces.utils.doc_generator import DocumentGenerator


class TestDocumentGenerator:
    """Test document generator functionality."""

    def test_document_generator_initialization(self) -> None:
        """Test DocumentGenerator initializes correctly."""
        generator = DocumentGenerator()
        assert generator.source_path is not None
        assert generator.docs_path is not None

    def test_document_generator_with_custom_paths(self) -> None:
        """Test DocumentGenerator with custom source and docs paths."""
        source_path = Path("/custom/source")
        docs_path = Path("/custom/docs")
        
        generator = DocumentGenerator(source_path=source_path, docs_path=docs_path)
        assert generator.source_path == source_path
        assert generator.docs_path == docs_path

    def test_analyze_source_files(self) -> None:
        """Test source file analysis functionality."""
        generator = DocumentGenerator()
        
        with patch.object(generator, "_scan_python_files") as mock_scan:
            mock_scan.return_value = ["file1.py", "file2.py"]
            
            result = generator.analyze_source_files()
            
            assert isinstance(result, dict)
            assert "files_analyzed" in result
            assert "interfaces" in result
            assert "models" in result
            assert "total_files" in result

    def test_analyze_documentation_files(self) -> None:
        """Test documentation file analysis functionality."""
        generator = DocumentGenerator()
        
        with patch.object(generator, "_scan_markdown_files") as mock_scan:
            mock_scan.return_value = ["doc1.md", "doc2.md"]
            
            result = generator.analyze_documentation_files()
            
            assert isinstance(result, dict)
            assert "documentation_files" in result
            assert "total_docs" in result

    def test_generate_enhanced_openapi_schema(self) -> None:
        """Test enhanced OpenAPI schema generation."""
        generator = DocumentGenerator()
        
        base_schema = {
            "info": {"title": "Test API", "version": "1.0.0"},
            "paths": {},
            "components": {}
        }
        
        enhanced_schema = generator.generate_enhanced_openapi_schema(base_schema)
        
        assert "info" in enhanced_schema
        assert "dynamic_content" in enhanced_schema["info"]
        assert "source_files_analyzed" in enhanced_schema["info"]["dynamic_content"]
        assert "documentation_files_found" in enhanced_schema["info"]["dynamic_content"]

    def test_generate_swagger_ui_html(self) -> None:
        """Test Swagger UI HTML generation."""
        generator = DocumentGenerator()
        
        schema_url = "/api/v1/swagger-ui/schema"
        html_content = generator.generate_swagger_ui_html(schema_url)
        
        assert isinstance(html_content, str)
        assert "swagger-ui" in html_content.lower()
        assert schema_url in html_content
        assert "<!DOCTYPE html>" in html_content

    def test_scan_python_files(self) -> None:
        """Test Python file scanning functionality."""
        generator = DocumentGenerator()
        
        mock_files = [
            Path("src/module1/__init__.py"),
            Path("src/module1/main.py"),
            Path("src/module2/utils.py"),
        ]
        
        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_rglob.return_value = mock_files
            
            files = generator._scan_python_files()
            
            assert len(files) == 3
            assert all(isinstance(f, Path) for f in files)

    def test_scan_markdown_files(self) -> None:
        """Test Markdown file scanning functionality."""
        generator = DocumentGenerator()
        
        mock_files = [
            Path("docs/readme.md"),
            Path("docs/api.md"),
        ]
        
        with patch("pathlib.Path.rglob") as mock_rglob:
            mock_rglob.return_value = mock_files
            
            files = generator._scan_markdown_files()
            
            assert len(files) == 2
            assert all(isinstance(f, Path) for f in files)

    def test_extract_interface_info(self) -> None:
        """Test interface information extraction from Python files."""
        generator = DocumentGenerator()
        
        sample_code = '''
class RestAPIInterface(BaseInterface):
    """REST API Interface implementation."""
    
    def __init__(self) -> None:
        super().__init__()
        
    @property
    def name(self) -> str:
        return "RestAPI"
'''
        
        with patch("builtins.open", mock_open(read_data=sample_code)):
            interface_info = generator._extract_interface_info(Path("test.py"))
            
            assert "RestAPIInterface" in interface_info
            assert interface_info["RestAPIInterface"]["docstring"] == "REST API Interface implementation."

    def test_extract_model_info(self) -> None:
        """Test model information extraction from Python files."""
        generator = DocumentGenerator()
        
        sample_code = '''
class HealthResponse(BaseModel):
    """Health check response model."""
    
    status: str = Field(default="healthy")
    timestamp: datetime = Field(default_factory=datetime.now)
'''
        
        with patch("builtins.open", mock_open(read_data=sample_code)):
            model_info = generator._extract_model_info(Path("test.py"))
            
            assert "HealthResponse" in model_info
            assert model_info["HealthResponse"]["docstring"] == "Health check response model."

    def test_extract_endpoint_info(self) -> None:
        """Test endpoint information extraction from Python files."""
        generator = DocumentGenerator()
        
        sample_code = '''
@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse()

@app.get("/api/v1/welcome")
async def welcome():
    """Welcome message endpoint."""
    return {"message": "Welcome!"}
'''
        
        with patch("builtins.open", mock_open(read_data=sample_code)):
            endpoint_info = generator._extract_endpoint_info(Path("test.py"))
            
            assert len(endpoint_info) == 2
            assert any(ep["path"] == "/health" for ep in endpoint_info)
            assert any(ep["path"] == "/api/v1/welcome" for ep in endpoint_info)

    def test_parse_documentation_content(self) -> None:
        """Test documentation content parsing."""
        generator = DocumentGenerator()
        
        sample_markdown = '''
# API Documentation

## Overview
This is the API documentation.

## Endpoints
- GET /health - Health check
- GET /welcome - Welcome message
'''
        
        with patch("builtins.open", mock_open(read_data=sample_markdown)):
            doc_content = generator._parse_documentation_content(Path("api.md"))
            
            assert "title" in doc_content
            assert "sections" in doc_content
            assert doc_content["title"] == "API Documentation"

    def test_generate_analysis_summary(self) -> None:
        """Test analysis summary generation."""
        generator = DocumentGenerator()
        
        source_analysis = {
            "files_analyzed": ["file1.py", "file2.py"],
            "interfaces": {"RestAPIInterface": {"docstring": "REST API"}},
            "models": {"HealthResponse": {"docstring": "Health model"}},
            "total_files": 2
        }
        
        docs_analysis = {
            "documentation_files": ["api.md", "readme.md"],
            "total_docs": 2
        }
        
        summary = generator.generate_analysis_summary(source_analysis, docs_analysis)
        
        assert "interfaces" in summary
        assert "models" in summary
        assert "endpoints" in summary
        assert "documentation_files" in summary
        assert len(summary["interfaces"]) == 1
        assert len(summary["models"]) == 1

    def test_error_handling_missing_source_path(self) -> None:
        """Test error handling when source path doesn't exist."""
        non_existent_path = Path("/non/existent/path")
        generator = DocumentGenerator(source_path=non_existent_path)
        
        with patch("pathlib.Path.exists", return_value=False):
            result = generator.analyze_source_files()
            
            # Should handle gracefully and return empty analysis
            assert result["total_files"] == 0
            assert len(result["files_analyzed"]) == 0

    def test_error_handling_missing_docs_path(self) -> None:
        """Test error handling when docs path doesn't exist."""
        non_existent_path = Path("/non/existent/docs")
        generator = DocumentGenerator(docs_path=non_existent_path)
        
        with patch("pathlib.Path.exists", return_value=False):
            result = generator.analyze_documentation_files()
            
            # Should handle gracefully and return empty analysis
            assert result["total_docs"] == 0
            assert len(result["documentation_files"]) == 0