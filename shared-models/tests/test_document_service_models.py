"""Tests for document service models."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from shared_models.generated.document_service import (
    BulkUploadResponse,
    DocumentListResponse,
    DocumentResponse,
    DocumentUpdateRequest,
    DocumentUpdateResponse,
    Feature,
    FeatureProperties,
    HealthResponse,
)


class TestFeatureProperties:
    """Test FeatureProperties model."""

    def test_create_empty_properties(self):
        """Test creating empty feature properties."""
        props = FeatureProperties()
        assert props.years is None
        assert props.level is None
        assert props.grade is None

    def test_create_skill_properties(self):
        """Test creating skill properties."""
        props = FeatureProperties(
            years=5, level="expert", description="Advanced Python programming"
        )
        assert props.years == 5
        assert props.level == "expert"
        assert props.description == "Advanced Python programming"

    def test_create_certification_properties(self):
        """Test creating certification properties."""
        props = FeatureProperties(
            grade="A", percentage=92, year_obtained=2023, expires=2026
        )
        assert props.grade == "A"
        assert props.percentage == 92
        assert props.year_obtained == 2023
        assert props.expires == 2026

    def test_extra_properties_allowed(self):
        """Test that extra properties are allowed."""
        props = FeatureProperties(
            years=3, custom_field="custom_value", another_field=123
        )
        assert props.years == 3
        # Extra properties should be accessible
        assert hasattr(props, "custom_field")
        assert hasattr(props, "another_field")


class TestFeature:
    """Test Feature model."""

    def test_create_basic_feature(self):
        """Test creating a basic feature."""
        feature = Feature(name="Python", type="skill")
        assert feature.name == "Python"
        assert feature.type == "skill"
        assert isinstance(feature.properties, FeatureProperties)

    def test_create_feature_with_properties(self):
        """Test creating feature with properties."""
        props = FeatureProperties(years=5, level="expert")
        feature = Feature(name="Python", type="skill", properties=props)
        assert feature.name == "Python"
        assert feature.type == "skill"
        assert feature.properties.years == 5
        assert feature.properties.level == "expert"

    def test_feature_validation(self):
        """Test feature validation."""
        # Missing required fields should raise ValidationError
        with pytest.raises(ValidationError):
            Feature()

        with pytest.raises(ValidationError):
            Feature(name="Python")  # Missing type

        with pytest.raises(ValidationError):
            Feature(type="skill")  # Missing name


class TestDocumentResponse:
    """Test DocumentResponse model."""

    def test_create_document_response(self, sample_document_response):
        """Test creating a document response."""
        doc = sample_document_response
        assert isinstance(doc.id, type(uuid4()))
        assert isinstance(doc.user_id, type(uuid4()))
        assert doc.filename == "test_resume.pdf"
        assert doc.file_type == "cv"
        assert doc.content_type == "application/pdf"
        assert doc.file_size == 1024000
        assert doc.role == "Senior Python Developer"
        assert len(doc.features) == 1
        assert doc.features[0].name == "Python"
        assert doc.processing_status == "completed"
        assert doc.metadata["confidence_score"] == 0.95

    def test_document_response_validation(self):
        """Test document response validation."""
        # Missing required fields should raise ValidationError
        with pytest.raises(ValidationError):
            DocumentResponse()

        # Invalid file_type should raise ValidationError
        with pytest.raises(ValidationError):
            DocumentResponse(
                id=uuid4(),
                user_id=uuid4(),
                filename="test.pdf",
                file_type="invalid",  # Should be 'cv' or 'jd'
                content_type="application/pdf",
                file_size=1024,
            )


class TestDocumentUpdateRequest:
    """Test DocumentUpdateRequest model."""

    def test_create_update_request(self, sample_feature):
        """Test creating a document update request."""
        request = DocumentUpdateRequest(
            file_type="cv",
            text_content="# John Doe\n\nSoftware Engineer...",
            role="Senior Python Developer",
            features=[sample_feature],
            metadata={"confidence_score": 0.95},
        )
        assert request.file_type == "cv"
        assert request.text_content.startswith("# John Doe")
        assert request.role == "Senior Python Developer"
        assert len(request.features) == 1
        assert request.features[0].name == "Python"
        assert request.metadata["confidence_score"] == 0.95

    def test_update_request_optional_fields(self):
        """Test that all fields are optional."""
        request = DocumentUpdateRequest()
        assert request.file_type is None
        assert request.text_content is None
        assert request.role is None
        assert request.features is None
        assert request.metadata is None

    def test_update_request_validation(self):
        """Test update request validation."""
        # Invalid file_type should raise ValidationError
        with pytest.raises(ValidationError):
            DocumentUpdateRequest(file_type="invalid")


class TestDocumentListResponse:
    """Test DocumentListResponse model."""

    def test_create_list_response(self, sample_document_response):
        """Test creating a document list response."""
        response = DocumentListResponse(
            documents=[sample_document_response],
            total_count=1,
            limit=50,
            offset=0,
            has_more=False,
        )
        assert len(response.documents) == 1
        assert response.total_count == 1
        assert response.limit == 50
        assert response.offset == 0
        assert response.has_more is False

    def test_empty_list_response(self):
        """Test creating an empty list response."""
        response = DocumentListResponse(
            documents=[], total_count=0, limit=50, offset=0, has_more=False
        )
        assert len(response.documents) == 0
        assert response.total_count == 0


class TestBulkUploadResponse:
    """Test BulkUploadResponse model."""

    def test_create_bulk_upload_response(self):
        """Test creating a bulk upload response."""
        response = BulkUploadResponse(
            total_files=5,
            successful_uploads=4,
            failed_uploads=1,
            results=[
                {
                    "filename": "resume1.pdf",
                    "status": "success",
                    "document_id": str(uuid4()),
                },
                {
                    "filename": "resume2.pdf",
                    "status": "success",
                    "document_id": str(uuid4()),
                },
                {
                    "filename": "resume3.pdf",
                    "status": "success",
                    "document_id": str(uuid4()),
                },
                {
                    "filename": "resume4.pdf",
                    "status": "success",
                    "document_id": str(uuid4()),
                },
                {
                    "filename": "resume5.pdf",
                    "status": "failed",
                    "error": "File too large",
                },
            ],
        )
        assert response.total_files == 5
        assert response.successful_uploads == 4
        assert response.failed_uploads == 1
        assert len(response.results) == 5


class TestDocumentUpdateResponse:
    """Test DocumentUpdateResponse model."""

    def test_create_update_response(self):
        """Test creating a document update response."""
        response = DocumentUpdateResponse(
            success=True,
            data={
                "document_id": str(uuid4()),
                "updated_fields": ["text_content", "role"],
            },
            meta={"processing_time": 1.23},
        )
        assert response.success is True
        assert "document_id" in response.data
        assert "updated_fields" in response.data
        assert response.meta["processing_time"] == 1.23


class TestHealthResponse:
    """Test HealthResponse model."""

    def test_create_health_response(self):
        """Test creating a health response."""
        response = HealthResponse(
            status="healthy",
            timestamp=datetime.utcnow(),
            version="1.0.0",
            dependencies={"database": "healthy", "storage": "healthy"},
        )
        assert response.status == "healthy"
        assert isinstance(response.timestamp, datetime)
        assert response.version == "1.0.0"
        assert response.dependencies["database"] == "healthy"


class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_document_response_serialization(self, sample_document_response):
        """Test document response serialization."""
        doc = sample_document_response

        # Test model_dump
        data = doc.model_dump()
        assert isinstance(data, dict)
        assert data["filename"] == "test_resume.pdf"
        assert data["file_type"] == "cv"

        # Test JSON serialization
        json_str = doc.model_dump_json()
        assert isinstance(json_str, str)
        assert "test_resume.pdf" in json_str

    def test_document_response_deserialization(self, sample_document_response):
        """Test document response deserialization."""
        doc = sample_document_response
        data = doc.model_dump()

        # Test model reconstruction
        new_doc = DocumentResponse(**data)
        assert new_doc.id == doc.id
        assert new_doc.filename == doc.filename
        assert new_doc.file_type == doc.file_type
        assert len(new_doc.features) == len(doc.features)
        assert new_doc.features[0].name == doc.features[0].name
