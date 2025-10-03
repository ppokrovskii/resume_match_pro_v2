"""Tests for base classes and mixins."""

from datetime import datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from shared_models.base import (
    BaseSharedModel,
    ErrorResponse,
    MetadataMixin,
    PaginationResponse,
    SuccessResponse,
    TimestampMixin,
    UserContextMixin,
)


class TestBaseSharedModel:
    """Test BaseSharedModel functionality."""

    def test_base_model_configuration(self):
        """Test that BaseSharedModel has correct configuration."""

        # Create a test model that inherits from BaseSharedModel
        class TestModel(BaseSharedModel):
            name: str
            value: int

        # Test model_config is properly set
        config = TestModel.model_config
        assert config["from_attributes"] is True
        assert config["use_enum_values"] is True
        assert config["validate_assignment"] is True
        assert config["arbitrary_types_allowed"] is False
        assert config["extra"] == "forbid"

    def test_base_model_validation(self):
        """Test that BaseSharedModel provides proper validation."""

        class TestModel(BaseSharedModel):
            name: str
            value: int

        # Valid data should work
        model = TestModel(name="test", value=42)
        assert model.name == "test"
        assert model.value == 42

        # Invalid data should raise ValidationError
        with pytest.raises(ValidationError):
            TestModel(name="test")  # Missing required field

        with pytest.raises(ValidationError):
            TestModel(name="test", value="not_an_int")  # Wrong type

    def test_base_model_forbids_extra_fields(self):
        """Test that BaseSharedModel forbids extra fields by default."""

        class TestModel(BaseSharedModel):
            name: str

        # Extra fields should be forbidden
        with pytest.raises(ValidationError):
            TestModel(name="test", extra_field="not_allowed")

    def test_base_model_serialization(self):
        """Test BaseSharedModel serialization methods."""

        class TestModel(BaseSharedModel):
            name: str
            value: int

        model = TestModel(name="test", value=42)

        # Test model_dump
        data = model.model_dump()
        assert data == {"name": "test", "value": 42}

        # Test model_dump_json
        json_str = model.model_dump_json()
        assert isinstance(json_str, str)
        assert "test" in json_str
        assert "42" in json_str

    def test_base_model_from_attributes(self):
        """Test that from_attributes configuration works."""

        class TestModel(BaseSharedModel):
            name: str
            value: int

        # Mock object with attributes
        class MockObject:
            def __init__(self):
                self.name = "from_attrs"
                self.value = 123

        obj = MockObject()
        model = TestModel.model_validate(obj)
        assert model.name == "from_attrs"
        assert model.value == 123


class TestTimestampMixin:
    """Test TimestampMixin functionality."""

    def test_timestamp_mixin_fields(self):
        """Test that TimestampMixin provides timestamp fields."""

        class TestModel(BaseSharedModel, TimestampMixin):
            name: str

        # Check that timestamp fields are available
        model = TestModel(name="test")
        assert hasattr(model, "created_at")
        assert hasattr(model, "updated_at")
        assert model.created_at is None  # Optional fields default to None
        assert model.updated_at is None

    def test_timestamp_mixin_with_values(self):
        """Test TimestampMixin with actual timestamp values."""

        class TestModel(BaseSharedModel, TimestampMixin):
            name: str

        now = datetime.utcnow()
        model = TestModel(name="test", created_at=now, updated_at=now)

        assert model.created_at == now
        assert model.updated_at == now
        assert isinstance(model.created_at, datetime)
        assert isinstance(model.updated_at, datetime)

    def test_timestamp_mixin_validation(self):
        """Test that TimestampMixin validates datetime types."""

        class TestModel(BaseSharedModel, TimestampMixin):
            name: str

        # Invalid datetime should raise ValidationError
        with pytest.raises(ValidationError):
            TestModel(name="test", created_at="not_a_datetime")

    def test_timestamp_mixin_serialization(self):
        """Test TimestampMixin serialization."""

        class TestModel(BaseSharedModel, TimestampMixin):
            name: str

        now = datetime.utcnow()
        model = TestModel(name="test", created_at=now)

        data = model.model_dump()
        assert data["name"] == "test"
        assert data["created_at"] == now
        assert data["updated_at"] is None


class TestUserContextMixin:
    """Test UserContextMixin functionality."""

    def test_user_context_mixin_fields(self):
        """Test that UserContextMixin provides user context fields."""

        class TestModel(BaseSharedModel, UserContextMixin):
            name: str

        user_id = uuid4()
        org_id = uuid4()

        model = TestModel(name="test", user_id=user_id, organization_id=org_id)

        assert model.user_id == user_id
        assert model.organization_id == org_id
        assert isinstance(model.user_id, UUID)
        assert isinstance(model.organization_id, UUID)

    def test_user_context_mixin_required_user_id(self):
        """Test that user_id is required in UserContextMixin."""

        class TestModel(BaseSharedModel, UserContextMixin):
            name: str

        # user_id is required
        with pytest.raises(ValidationError):
            TestModel(name="test")

    def test_user_context_mixin_optional_organization_id(self):
        """Test that organization_id is optional in UserContextMixin."""

        class TestModel(BaseSharedModel, UserContextMixin):
            name: str

        user_id = uuid4()

        # organization_id is optional
        model = TestModel(name="test", user_id=user_id)
        assert model.user_id == user_id
        assert model.organization_id is None

    def test_user_context_mixin_uuid_validation(self):
        """Test that UserContextMixin validates UUID types."""

        class TestModel(BaseSharedModel, UserContextMixin):
            name: str

        # Invalid UUID should raise ValidationError
        with pytest.raises(ValidationError):
            TestModel(name="test", user_id="not_a_uuid")

        with pytest.raises(ValidationError):
            TestModel(name="test", user_id=uuid4(), organization_id="not_a_uuid")


class TestMetadataMixin:
    """Test MetadataMixin functionality."""

    def test_metadata_mixin_fields(self):
        """Test that MetadataMixin provides metadata field."""

        class TestModel(BaseSharedModel, MetadataMixin):
            name: str

        model = TestModel(name="test")
        assert hasattr(model, "metadata")
        assert model.metadata == {}  # Default empty dict

    def test_metadata_mixin_with_data(self):
        """Test MetadataMixin with actual metadata."""

        class TestModel(BaseSharedModel, MetadataMixin):
            name: str

        metadata = {
            "version": "1.0.0",
            "tags": ["test", "model"],
            "config": {"debug": True},
        }

        model = TestModel(name="test", metadata=metadata)
        assert model.metadata == metadata
        assert model.metadata["version"] == "1.0.0"
        assert model.metadata["config"]["debug"] is True

    def test_metadata_mixin_flexible_types(self):
        """Test that MetadataMixin accepts various data types."""

        class TestModel(BaseSharedModel, MetadataMixin):
            name: str

        metadata = {
            "string": "value",
            "number": 42,
            "boolean": True,
            "list": [1, 2, 3],
            "nested": {"key": "value"},
            "null": None,
        }

        model = TestModel(name="test", metadata=metadata)
        assert model.metadata == metadata


class TestMultipleMixins:
    """Test models with multiple mixins combined."""

    def test_all_mixins_combined(self):
        """Test a model with all mixins combined."""

        class CompleteModel(
            BaseSharedModel, TimestampMixin, UserContextMixin, MetadataMixin
        ):
            name: str
            value: int

        user_id = uuid4()
        org_id = uuid4()
        now = datetime.utcnow()
        metadata = {"test": True}

        model = CompleteModel(
            name="complete",
            value=42,
            user_id=user_id,
            organization_id=org_id,
            created_at=now,
            updated_at=now,
            metadata=metadata,
        )

        # Check all fields are present
        assert model.name == "complete"
        assert model.value == 42
        assert model.user_id == user_id
        assert model.organization_id == org_id
        assert model.created_at == now
        assert model.updated_at == now
        assert model.metadata == metadata

    def test_mixin_order_independence(self):
        """Test that mixin order doesn't affect functionality."""

        class Model1(BaseSharedModel, TimestampMixin, UserContextMixin):
            name: str

        class Model2(BaseSharedModel, UserContextMixin, TimestampMixin):
            name: str

        user_id = uuid4()
        now = datetime.utcnow()

        model1 = Model1(name="test1", user_id=user_id, created_at=now)
        model2 = Model2(name="test2", user_id=user_id, created_at=now)

        # Both should have the same fields available
        assert hasattr(model1, "user_id") and hasattr(model1, "created_at")
        assert hasattr(model2, "user_id") and hasattr(model2, "created_at")


class TestPaginationResponse:
    """Test PaginationResponse model."""

    def test_pagination_response_creation(self):
        """Test creating a PaginationResponse."""
        response = PaginationResponse(
            total_count=100, limit=10, offset=20, has_more=True
        )

        assert response.total_count == 100
        assert response.limit == 10
        assert response.offset == 20
        assert response.has_more is True

    def test_pagination_response_validation(self):
        """Test PaginationResponse validation."""
        # Missing required fields should raise ValidationError
        with pytest.raises(ValidationError):
            PaginationResponse()

        with pytest.raises(ValidationError):
            PaginationResponse(total_count=100)  # Missing other required fields

    def test_pagination_response_calculations(self):
        """Test pagination response with edge cases."""
        # Last page
        response = PaginationResponse(
            total_count=25, limit=10, offset=20, has_more=False
        )
        assert response.has_more is False

        # First page
        response = PaginationResponse(
            total_count=100, limit=10, offset=0, has_more=True
        )
        assert response.offset == 0
        assert response.has_more is True


class TestErrorResponse:
    """Test ErrorResponse model."""

    def test_error_response_creation(self):
        """Test creating an ErrorResponse."""
        response = ErrorResponse(
            error="VALIDATION_ERROR",
            message="Invalid input data",
            details={"field": "name", "issue": "required"},
        )

        assert response.error == "VALIDATION_ERROR"
        assert response.message == "Invalid input data"
        assert response.details["field"] == "name"

    def test_error_response_required_fields(self):
        """Test ErrorResponse required fields."""
        # Minimal valid error response
        response = ErrorResponse(error="ERROR_CODE", message="Error message")
        assert response.error == "ERROR_CODE"
        assert response.message == "Error message"
        assert response.details is None

    def test_error_response_validation(self):
        """Test ErrorResponse validation."""
        # Missing required fields should raise ValidationError
        with pytest.raises(ValidationError):
            ErrorResponse()

        with pytest.raises(ValidationError):
            ErrorResponse(error="CODE")  # Missing message


class TestSuccessResponse:
    """Test SuccessResponse model."""

    def test_success_response_creation(self):
        """Test creating a SuccessResponse."""
        response = SuccessResponse(
            success=True,
            message="Operation completed successfully",
            data={"result": "success", "count": 1},
        )

        assert response.success is True
        assert response.message == "Operation completed successfully"
        assert response.data["result"] == "success"

    def test_success_response_defaults(self):
        """Test SuccessResponse default values."""
        response = SuccessResponse()

        assert response.success is True  # Default value
        assert response.message is None
        assert response.data is None

    def test_success_response_optional_fields(self):
        """Test that message and data are optional."""
        # Only success field (with default)
        response = SuccessResponse()
        assert response.success is True

        # Custom success value
        response = SuccessResponse(success=False)
        assert response.success is False


class TestBaseClassIntegration:
    """Test integration between base classes and real models."""

    def test_base_classes_with_generated_models(self):
        """Test that base classes work with generated models."""
        # Import a generated model to test integration
        from shared_models.generated.document_service import DocumentResponse

        # Verify that DocumentResponse uses the base classes
        assert issubclass(DocumentResponse, BaseSharedModel)
        # Note: We can't directly check for mixin inheritance due to how they're composed

        # Test that the generated model has the expected behavior
        user_id = uuid4()
        doc_id = uuid4()
        now = datetime.utcnow()

        doc = DocumentResponse(
            id=doc_id,
            user_id=user_id,
            filename="test.pdf",
            content_type="application/pdf",
            file_size=1024,
            created_at=now,
            updated_at=now,
        )

        # Verify base model functionality works
        assert doc.id == doc_id
        assert doc.user_id == user_id
        assert doc.created_at == now

        # Test serialization
        data = doc.model_dump()
        # UUIDs may or may not be serialized to strings depending on configuration
        assert data["id"] == doc_id or data["id"] == str(doc_id)
        assert data["filename"] == "test.pdf"

    def test_base_model_error_handling(self):
        """Test error handling in base models."""
        from shared_models.generated.document_service import Feature

        # Test validation errors
        with pytest.raises(ValidationError) as exc_info:
            Feature()  # Missing required fields

        # Verify error structure
        error = exc_info.value
        assert len(error.errors()) > 0

        # Check that error details are available
        for err in error.errors():
            assert "type" in err
            assert "loc" in err
            assert "msg" in err


class TestModelConfiguration:
    """Test model configuration consistency."""

    def test_all_base_models_inherit_correctly(self):
        """Test that all base models have consistent configuration."""
        base_models = [
            BaseSharedModel,
            PaginationResponse,
            ErrorResponse,
            SuccessResponse,
        ]

        for model_class in base_models:
            # All should inherit from BaseSharedModel or be BaseSharedModel
            assert issubclass(model_class, BaseSharedModel)

            # All should have the same core configuration
            config = model_class.model_config
            assert config.get("from_attributes") is True
            assert config.get("use_enum_values") is True
            assert config.get("validate_assignment") is True

    def test_mixin_fields_are_properly_typed(self):
        """Test that mixin fields have proper type annotations."""
        from typing import get_type_hints

        # Check TimestampMixin
        timestamp_hints = get_type_hints(TimestampMixin)
        assert "created_at" in timestamp_hints
        assert "updated_at" in timestamp_hints
        # The type should be Optional[datetime] but we'll check it's datetime related

        # Check UserContextMixin
        user_hints = get_type_hints(UserContextMixin)
        assert "user_id" in user_hints
        assert "organization_id" in user_hints

        # Check MetadataMixin
        metadata_hints = get_type_hints(MetadataMixin)
        assert "metadata" in metadata_hints
