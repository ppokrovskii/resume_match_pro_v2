"""Tests for model generation functionality."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest

# Add scripts directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from generate_models import (
    SERVICES,
    add_generation_header,
    create_generated_init_file,
    create_init_file,
    fetch_openapi_spec,
    generate_models_for_service,
    load_openapi_spec_from_file,
)


class TestOpenAPIFetching:
    """Test OpenAPI specification fetching functionality."""

    @pytest.mark.asyncio
    async def test_fetch_openapi_spec_success(self):
        """Test successful OpenAPI spec fetching."""
        mock_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Test Service", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}},
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.json.return_value = mock_spec
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            result = await fetch_openapi_spec("document_service", "local")

            assert result == mock_spec
            assert result["info"]["title"] == "Test Service"

    @pytest.mark.asyncio
    async def test_fetch_openapi_spec_invalid_service(self):
        """Test fetching spec for invalid service name."""
        with pytest.raises(ValueError, match="Unknown service: invalid_service"):
            await fetch_openapi_spec("invalid_service", "local")

    @pytest.mark.asyncio
    async def test_fetch_openapi_spec_invalid_environment(self):
        """Test fetching spec for invalid environment."""
        with pytest.raises(ValueError, match="Unknown environment: invalid_env"):
            await fetch_openapi_spec("document_service", "invalid_env")

    @pytest.mark.asyncio
    async def test_fetch_openapi_spec_http_error(self):
        """Test handling of HTTP errors during fetching."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = httpx.HTTPError(
                "Connection failed"
            )

            mock_client.return_value.__aenter__.return_value.get.return_value = (
                mock_response
            )

            with pytest.raises(RuntimeError, match="Failed to fetch OpenAPI spec"):
                await fetch_openapi_spec("document_service", "local")


class TestFileOperations:
    """Test file-based OpenAPI operations."""

    def test_load_openapi_spec_from_file_success(self):
        """Test successful loading of OpenAPI spec from file."""
        mock_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Test Service", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}},
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(mock_spec, f)
            temp_file = f.name

        try:
            result = load_openapi_spec_from_file(temp_file)
            assert result == mock_spec
            assert result["info"]["title"] == "Test Service"
        finally:
            Path(temp_file).unlink()

    def test_load_openapi_spec_from_file_not_found(self):
        """Test loading spec from non-existent file."""
        with pytest.raises(RuntimeError, match="Failed to load OpenAPI spec"):
            load_openapi_spec_from_file("non_existent_file.json")

    def test_load_openapi_spec_from_file_invalid_json(self):
        """Test loading spec from file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            temp_file = f.name

        try:
            with pytest.raises(RuntimeError, match="Failed to load OpenAPI spec"):
                load_openapi_spec_from_file(temp_file)
        finally:
            Path(temp_file).unlink()


class TestModelGeneration:
    """Test model generation functionality."""

    def test_services_configuration(self):
        """Test that SERVICES configuration is properly defined."""
        assert "document_service" in SERVICES
        assert "local" in SERVICES["document_service"]
        assert "dev" in SERVICES["document_service"]
        assert "staging" in SERVICES["document_service"]
        assert "prod" in SERVICES["document_service"]

        # Verify URLs are properly formatted
        for service_name, environments in SERVICES.items():
            for env_name, url in environments.items():
                assert url.startswith(
                    "http"
                ), f"Invalid URL for {service_name}/{env_name}: {url}"
                assert url.endswith(
                    "/openapi.json"
                ), f"URL should end with /openapi.json: {url}"

    @patch("subprocess.run")
    def test_generate_models_for_service_success(self, mock_subprocess):
        """Test successful model generation."""
        mock_spec = {
            "openapi": "3.1.0",
            "info": {
                "title": "Document Service API",
                "version": "1.0.0",
                "description": "Test service",
            },
            "paths": {},
            "components": {
                "schemas": {
                    "TestModel": {
                        "type": "object",
                        "properties": {"name": {"type": "string"}},
                    }
                }
            },
        }

        # Mock successful subprocess run
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = ""
        mock_subprocess.return_value = mock_result

        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir) / "test_service"
            output_dir.mkdir(parents=True)

            # Create a mock output file that would be generated by datamodel-codegen
            output_file = output_dir / "models.py"
            output_file.write_text(
                """
class TestModel(BaseModel):
    name: str
"""
            )

            # Mock the path operations
            with (
                patch("pathlib.Path.mkdir"),
                patch("pathlib.Path.unlink"),
                patch("pathlib.Path.exists", return_value=True),
                patch("builtins.open", create=True) as mock_open,
            ):

                mock_open.return_value.__enter__.return_value.read.return_value = (
                    "class TestModel(BaseModel):\n    name: str"
                )
                mock_open.return_value.__enter__.return_value.write.return_value = None

                # This should not raise an exception
                generate_models_for_service("test_service", mock_spec)

                # Verify subprocess was called
                mock_subprocess.assert_called_once()
                args = mock_subprocess.call_args[0][0]
                # Check that the command uses datamodel_codegen module
                assert any("datamodel_codegen" in str(arg) for arg in args)
                assert "--input" in args
                assert "--output" in args

    @patch("subprocess.run")
    def test_generate_models_for_service_subprocess_failure(self, mock_subprocess):
        """Test handling of subprocess failure during generation."""
        mock_spec = {
            "openapi": "3.1.0",
            "info": {"title": "Test Service", "version": "1.0.0"},
            "paths": {},
            "components": {"schemas": {}},
        }

        # Mock failed subprocess run
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "Generation failed"
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            1, "datamodel-codegen", stderr="Generation failed"
        )

        with pytest.raises(subprocess.CalledProcessError):
            generate_models_for_service("test_service", mock_spec)


class TestFileGeneration:
    """Test file generation utilities."""

    def test_add_generation_header(self):
        """Test adding generation header to model files."""
        original_content = """
from pydantic import BaseModel

class TestModel(BaseModel):
    name: str
"""

        mock_spec = {
            "info": {
                "title": "Test Service API",
                "version": "1.0.0",
                "description": "Test description",
            }
        }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(original_content)
            temp_file = f.name

        try:
            with patch("generate_models.datetime") as mock_datetime:
                mock_datetime.utcnow.return_value.isoformat.return_value = (
                    "2025-01-01T00:00:00"
                )

                add_generation_header(Path(temp_file), "test_service", mock_spec)

                with open(temp_file, "r") as f:
                    result = f.read()

                    # Check that header was added
                    assert (
                        "Auto-generated Pydantic models from Test Service API" in result
                    )
                assert "Version: 1.0.0" in result
                assert "Description: Test description" in result
                assert "Generated: 2025-01-01T00:00:00Z" in result
                assert "DO NOT EDIT MANUALLY" in result

                # Check that imports were enhanced
                assert "from ..base import BaseSharedModel" in result

                # Check that original content is preserved
                assert "class TestModel(BaseModel):" in result
        finally:
            Path(temp_file).unlink()

    def test_create_init_file(self):
        """Test creation of __init__.py files."""
        models_content = """
class ModelA(BaseModel):
    name: str

class ModelB(BaseModel):
    value: int

class ModelC(BaseModel):
    flag: bool
"""

        with tempfile.TemporaryDirectory() as temp_dir:
            service_dir = Path(temp_dir)
            models_file = service_dir / "models.py"
            models_file.write_text(models_content)

            create_init_file(service_dir, "test_service")

            init_file = service_dir / "__init__.py"
            assert init_file.exists()

            init_content = init_file.read_text()

            # Check that all models are imported
            assert "ModelA," in init_content
            assert "ModelB," in init_content
            assert "ModelC," in init_content

            # Check __all__ exports
            assert '"ModelA",' in init_content
            assert '"ModelB",' in init_content
            assert '"ModelC",' in init_content

            # Check service documentation
            assert "test_service service" in init_content

    def test_create_generated_init_file(self):
        """Test creation of generated package __init__.py."""
        with tempfile.TemporaryDirectory() as temp_dir:
            generated_dir = Path(temp_dir)

            # Create some service directories
            (generated_dir / "service_a").mkdir()
            (generated_dir / "service_b").mkdir()
            (generated_dir / ".hidden").mkdir()  # Should be ignored

            # Mock the GENERATED_DIR to point to our test directory
            with patch("generate_models.GENERATED_DIR", generated_dir):
                create_generated_init_file()

                init_file = generated_dir / "__init__.py"
                assert init_file.exists()

                init_content = init_file.read_text()

                # Check basic structure
                assert (
                    "Generated models from microservice OpenAPI specifications"
                    in init_content
                )
                assert "__all__ = []" in init_content


class TestIntegrationScenarios:
    """Test integration scenarios."""

    def test_full_generation_workflow_simulation(self):
        """Test the complete generation workflow with mocked components."""
        mock_spec = {
            "openapi": "3.1.0",
            "info": {
                "title": "Document Service API",
                "version": "1.0.0",
                "description": "Document management service",
            },
            "paths": {"/documents": {"get": {"operationId": "list_documents"}}},
            "components": {
                "schemas": {
                    "Document": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                        },
                    }
                }
            },
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            # Setup directories
            output_dir = Path(temp_dir) / "document_service"
            output_dir.mkdir(parents=True)

            # Mock the datamodel-codegen subprocess call
            with patch("subprocess.run") as mock_subprocess:
                mock_result = Mock()
                mock_result.returncode = 0
                mock_result.stderr = ""
                mock_subprocess.return_value = mock_result

                # Mock file operations
                with (
                    patch("pathlib.Path.unlink"),
                    patch("builtins.open", create=True) as mock_open,
                ):

                    # Mock reading the generated models file
                    mock_open.return_value.__enter__.return_value.read.return_value = """
class Document(BaseModel):
    id: str
    name: str
"""

                    # This should complete without errors
                    generate_models_for_service("document_service", mock_spec)

                    # Verify the subprocess was called with correct arguments
                    assert mock_subprocess.called
                    call_args = mock_subprocess.call_args[0][0]
                    assert any("datamodel_codegen" in str(arg) for arg in call_args)

    def test_error_handling_in_generation(self):
        """Test error handling during model generation."""
        invalid_spec = {
            "openapi": "3.1.0",
            # Missing required fields
        }

        with patch("subprocess.run") as mock_subprocess:
            # Simulate subprocess failure
            mock_subprocess.side_effect = subprocess.CalledProcessError(
                1, "datamodel-codegen", stderr="Invalid OpenAPI spec"
            )

            with pytest.raises(subprocess.CalledProcessError):
                generate_models_for_service("test_service", invalid_spec)


class TestModelValidation:
    """Test validation of generated models."""

    def test_generated_models_can_be_imported(self):
        """Test that generated models can be imported successfully."""
        # This tests the actual generated models
        try:
            from shared_models.generated.document_service import (
                DocumentResponse,
                DocumentUpdateRequest,
                Feature,
            )

            # Basic functionality test
            feature = Feature(name="Python", type="skill")
            assert feature.name == "Python"
            assert feature.type == "skill"

            # Validation test
            with pytest.raises(Exception):  # Should raise validation error
                Feature()  # Missing required fields

        except ImportError as e:
            pytest.fail(f"Could not import generated models: {e}")

    def test_generated_models_validation_works(self):
        """Test that validation works correctly in generated models."""
        from pydantic import ValidationError

        from shared_models.generated.document_service import DocumentUpdateRequest

        # Valid request should work
        valid_request = DocumentUpdateRequest(file_type="cv", role="Developer")
        assert valid_request.file_type == "cv"

        # Invalid file_type should fail
        with pytest.raises(ValidationError):
            DocumentUpdateRequest(file_type="invalid_type")

    def test_generated_models_serialization(self):
        """Test that generated models can be serialized/deserialized."""
        from shared_models.generated.document_service import Feature, FeatureProperties

        # Create a feature
        feature = Feature(
            name="Python",
            type="skill",
            properties=FeatureProperties(years=5, level="expert"),
        )

        # Test serialization
        data = feature.model_dump()
        assert data["name"] == "Python"
        assert data["type"] == "skill"
        assert data["properties"]["years"] == 5

        # Test deserialization
        restored_feature = Feature(**data)
        assert restored_feature.name == feature.name
        assert restored_feature.type == feature.type
        assert restored_feature.properties.years == feature.properties.years
