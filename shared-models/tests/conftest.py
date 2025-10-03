"""Test configuration for shared models package."""

import pytest
from datetime import datetime
from uuid import uuid4


@pytest.fixture
def sample_user_id():
    """Sample user UUID for testing."""
    return uuid4()


@pytest.fixture
def sample_organization_id():
    """Sample organization UUID for testing."""
    return uuid4()


@pytest.fixture
def sample_document_id():
    """Sample document UUID for testing."""
    return uuid4()


@pytest.fixture
def sample_feature_properties():
    """Sample feature properties for testing."""
    return {
        "years": 5,
        "level": "expert",
        "description": "Advanced Python programming skills"
    }


@pytest.fixture
def sample_feature(sample_feature_properties):
    """Sample feature for testing."""
    from shared_models.generated.document_service import Feature, FeatureProperties
    
    return Feature(
        name="Python",
        type="skill",
        properties=FeatureProperties(**sample_feature_properties)
    )


@pytest.fixture
def sample_document_response(sample_document_id, sample_user_id, sample_organization_id, sample_feature):
    """Sample document response for testing."""
    from shared_models.generated.document_service import DocumentResponse
    
    return DocumentResponse(
        id=sample_document_id,
        user_id=sample_user_id,
        organization_id=sample_organization_id,
        filename="test_resume.pdf",
        file_type="cv",
        content_type="application/pdf",
        file_size=1024000,
        storage_path="documents/test/test_resume.pdf",
        text_content="# John Doe\n\nSoftware Engineer with 5 years experience...",
        role="Senior Python Developer",
        features=[sample_feature],
        processing_status="completed",
        metadata={"confidence_score": 0.95},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
