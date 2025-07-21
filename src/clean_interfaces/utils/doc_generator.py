"""Document generator utility for dynamic Swagger UI content generation."""

import ast
import re
from pathlib import Path
from typing import Any


class DocumentGenerator:
    """Generator for dynamic API documentation from source code and docs."""

    def __init__(
        self,
        source_path: Path | None = None,
        docs_path: Path | None = None,
    ) -> None:
        """Initialize the document generator.

        Args:
            source_path: Path to source code directory. Defaults to src/
            docs_path: Path to documentation directory. Defaults to docs/

        """
        # Get project root (assuming we're in src/clean_interfaces/utils/)
        current_file = Path(__file__)
        project_root = current_file.parent.parent.parent.parent

        self.source_path = source_path or project_root / "src"
        self.docs_path = docs_path or project_root / "docs"

    def analyze_source_files(self) -> dict[str, Any]:
        """Analyze Python source files for interfaces, models, and endpoints.

        Returns:
            Dict containing analysis results with interfaces, models, and file counts

        """
        if not self.source_path.exists():
            return {
                "files_analyzed": [],
                "interfaces": {},
                "models": {},
                "endpoints": [],
                "total_files": 0,
            }

        python_files = self._scan_python_files()
        
        interfaces = {}
        models = {}
        endpoints = []
        
        for file_path in python_files:
            try:
                interfaces.update(self._extract_interface_info(file_path))
                models.update(self._extract_model_info(file_path))
                endpoints.extend(self._extract_endpoint_info(file_path))
            except Exception:  # noqa: S110
                # Skip files that can't be parsed
                continue

        return {
            "files_analyzed": [str(f) for f in python_files],
            "interfaces": interfaces,
            "models": models,
            "endpoints": endpoints,
            "total_files": len(python_files),
        }

    def analyze_documentation_files(self) -> dict[str, Any]:
        """Analyze documentation files for additional content.

        Returns:
            Dict containing documentation analysis results

        """
        if not self.docs_path.exists():
            return {
                "documentation_files": [],
                "total_docs": 0,
            }

        markdown_files = self._scan_markdown_files()
        
        doc_contents = []
        for file_path in markdown_files:
            try:
                content = self._parse_documentation_content(file_path)
                doc_contents.append(content)
            except Exception:  # noqa: S110
                # Skip files that can't be parsed
                continue

        return {
            "documentation_files": [str(f) for f in markdown_files],
            "doc_contents": doc_contents,
            "total_docs": len(markdown_files),
        }

    def generate_enhanced_openapi_schema(self, base_schema: dict[str, Any]) -> dict[str, Any]:
        """Generate enhanced OpenAPI schema with dynamic content metadata.

        Args:
            base_schema: Base OpenAPI schema from FastAPI

        Returns:
            Enhanced schema with dynamic content information

        """
        source_analysis = self.analyze_source_files()
        docs_analysis = self.analyze_documentation_files()

        enhanced_schema = base_schema.copy()
        
        # Add dynamic content metadata to info section
        if "info" not in enhanced_schema:
            enhanced_schema["info"] = {}
            
        enhanced_schema["info"]["dynamic_content"] = {
            "source_files_analyzed": source_analysis["total_files"],
            "documentation_files_found": docs_analysis["total_docs"],
            "interfaces_discovered": len(source_analysis["interfaces"]),
            "models_discovered": len(source_analysis["models"]),
            "endpoints_analyzed": len(source_analysis["endpoints"]),
            "generation_timestamp": "2024-01-20T12:00:00Z",  # Would use real timestamp
        }

        # Enhance path descriptions with source code insights
        if "paths" in enhanced_schema:
            for path, path_info in enhanced_schema["paths"].items():
                # Find matching endpoint from source analysis
                matching_endpoints = [
                    ep for ep in source_analysis["endpoints"] 
                    if ep.get("path") == path
                ]
                if matching_endpoints:
                    endpoint = matching_endpoints[0]
                    for method, method_info in path_info.items():
                        if isinstance(method_info, dict) and "description" in method_info:
                            method_info["x-source-analysis"] = {
                                "docstring": endpoint.get("docstring", ""),
                                "file_location": endpoint.get("file", ""),
                            }

        return enhanced_schema

    def generate_swagger_ui_html(self, schema_url: str) -> str:
        """Generate Swagger UI HTML page.

        Args:
            schema_url: URL to the OpenAPI schema JSON

        Returns:
            HTML content for Swagger UI page

        """
        html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Clean Interfaces API - Enhanced Documentation</title>
    <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
    <style>
        .swagger-ui .topbar {{ display: none; }}
        .swagger-ui .info {{ margin: 20px 0; }}
        .swagger-ui .info .title {{ color: #3b82f6; }}
    </style>
</head>
<body>
    <div id="swagger-ui"></div>
    <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
    <script>
        window.onload = function() {{
            SwaggerUIBundle({{
                url: '{schema_url}',
                dom_id: '#swagger-ui',
                deepLinking: true,
                presets: [
                    SwaggerUIBundle.presets.apis,
                    SwaggerUIBundle.presets.standalone
                ],
                plugins: [
                    SwaggerUIBundle.plugins.DownloadUrl
                ],
                layout: "StandaloneLayout",
                docExpansion: "list",
                defaultModelsExpandDepth: 2,
                defaultModelExpandDepth: 2,
                tryItOutEnabled: true
            }});
        }};
    </script>
    <div style="margin: 20px; padding: 15px; background-color: #f8fafc; border-radius: 6px; border-left: 4px solid #3b82f6;">
        <h4>🚀 Enhanced Documentation</h4>
        <p>This documentation is dynamically generated from your source code and documentation files.</p>
        <p>Use the <code>/api/v1/swagger-ui/analysis</code> endpoint to view detailed source code analysis.</p>
    </div>
</body>
</html>'''
        return html_template

    def generate_analysis_summary(
        self,
        source_analysis: dict[str, Any],
        docs_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate a summary of source code and documentation analysis.

        Args:
            source_analysis: Results from analyze_source_files()
            docs_analysis: Results from analyze_documentation_files()

        Returns:
            Summary dictionary with interface, model, and endpoint information

        """
        return {
            "interfaces": list(source_analysis.get("interfaces", {}).keys()),
            "models": list(source_analysis.get("models", {}).keys()),
            "endpoints": [ep.get("path", "") for ep in source_analysis.get("endpoints", [])],
            "documentation_files": docs_analysis.get("documentation_files", []),
            "summary": {
                "total_source_files": source_analysis.get("total_files", 0),
                "total_documentation_files": docs_analysis.get("total_docs", 0),
                "total_interfaces": len(source_analysis.get("interfaces", {})),
                "total_models": len(source_analysis.get("models", {})),
                "total_endpoints": len(source_analysis.get("endpoints", [])),
            }
        }

    def _scan_python_files(self) -> list[Path]:
        """Scan for Python files in the source directory.

        Returns:
            List of Python file paths

        """
        if not self.source_path.exists():
            return []
        
        return list(self.source_path.rglob("*.py"))

    def _scan_markdown_files(self) -> list[Path]:
        """Scan for Markdown files in the docs directory.

        Returns:
            List of Markdown file paths

        """
        if not self.docs_path.exists():
            return []
        
        return list(self.docs_path.rglob("*.md"))

    def _extract_interface_info(self, file_path: Path) -> dict[str, Any]:
        """Extract interface class information from a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            Dict mapping interface names to their information

        """
        try:
            with file_path.open(encoding="utf-8") as f:
                content = f.read()
        except Exception:  # noqa: S110
            return {}

        interfaces = {}
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if class inherits from BaseInterface or has "Interface" in name
                    is_interface = (
                        "Interface" in node.name
                        or any(
                            isinstance(base, ast.Name) and "Interface" in base.id
                            for base in node.bases
                            if isinstance(base, ast.Name)
                        )
                    )
                    
                    if is_interface:
                        docstring = ast.get_docstring(node) or ""
                        interfaces[node.name] = {
                            "docstring": docstring.strip(),
                            "file": str(file_path),
                            "line": node.lineno,
                        }
        except Exception:  # noqa: S110
            # If AST parsing fails, try regex fallback
            interface_pattern = r'class\s+(\w*Interface\w*)\s*\([^)]*\):\s*"""([^"]*)'
            matches = re.findall(interface_pattern, content, re.MULTILINE | re.DOTALL)
            for name, docstring in matches:
                interfaces[name] = {
                    "docstring": docstring.strip(),
                    "file": str(file_path),
                    "line": 0,
                }

        return interfaces

    def _extract_model_info(self, file_path: Path) -> dict[str, Any]:
        """Extract Pydantic model information from a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            Dict mapping model names to their information

        """
        try:
            with file_path.open(encoding="utf-8") as f:
                content = f.read()
        except Exception:  # noqa: S110
            return {}

        models = {}
        
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if class inherits from BaseModel or has "Model/Response" in name
                    is_model = (
                        any(word in node.name for word in ["Model", "Response", "Request"])
                        or any(
                            isinstance(base, ast.Name) and "BaseModel" in base.id
                            for base in node.bases
                            if isinstance(base, ast.Name)
                        )
                    )
                    
                    if is_model:
                        docstring = ast.get_docstring(node) or ""
                        models[node.name] = {
                            "docstring": docstring.strip(),
                            "file": str(file_path),
                            "line": node.lineno,
                        }
        except Exception:  # noqa: S110
            # If AST parsing fails, try regex fallback
            model_pattern = r'class\s+(\w*(?:Model|Response|Request)\w*)\s*\([^)]*\):\s*"""([^"]*)'
            matches = re.findall(model_pattern, content, re.MULTILINE | re.DOTALL)
            for name, docstring in matches:
                models[name] = {
                    "docstring": docstring.strip(),
                    "file": str(file_path),
                    "line": 0,
                }

        return models

    def _extract_endpoint_info(self, file_path: Path) -> list[dict[str, Any]]:
        """Extract FastAPI endpoint information from a Python file.

        Args:
            file_path: Path to Python file

        Returns:
            List of endpoint information dictionaries

        """
        try:
            with file_path.open(encoding="utf-8") as f:
                content = f.read()
        except Exception:  # noqa: S110
            return []

        endpoints = []
        
        # Extract endpoints using regex
        endpoint_pattern = r'@[^.]*\.(?:get|post|put|delete|patch|head|options)\s*\(\s*["\']([^"\']+)["\'].*?\)\s*(?:async\s+)?def\s+(\w+)\s*\([^)]*\):\s*"""([^"]*)'
        matches = re.findall(endpoint_pattern, content, re.MULTILINE | re.DOTALL)
        
        for path, function_name, docstring in matches:
            endpoints.append({
                "path": path,
                "function": function_name,
                "docstring": docstring.strip(),
                "file": str(file_path),
            })

        return endpoints

    def _parse_documentation_content(self, file_path: Path) -> dict[str, Any]:
        """Parse Markdown documentation file content.

        Args:
            file_path: Path to Markdown file

        Returns:
            Dict containing parsed documentation content

        """
        try:
            with file_path.open(encoding="utf-8") as f:
                content = f.read()
        except Exception:  # noqa: S110
            return {"title": "", "sections": []}

        # Extract title (first H1)
        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        title = title_match.group(1) if title_match else ""

        # Extract sections (H2 headers)
        sections = re.findall(r'^##\s+(.+)$', content, re.MULTILINE)

        return {
            "title": title,
            "sections": sections,
            "file": str(file_path),
            "content_length": len(content),
        }