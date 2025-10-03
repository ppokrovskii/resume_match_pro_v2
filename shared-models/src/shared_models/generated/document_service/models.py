"""
Auto-generated Pydantic models from Document Service API OpenAPI specification.

Service: Document Service API
Version: 1.0.0
Description: Pure document storage and management microservice
Generated: 2025-10-03T10:34:00Z

DO NOT EDIT MANUALLY - Use scripts/generate_models.py to regenerate.
"""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

from ...base import BaseSharedModel, TimestampMixin, UserContextMixin, MetadataMixin


class FeatureProperties(BaseSharedModel):
    """Properties for a document feature with flexible key-value structure."""
    
    # Common properties for skills
    years: Optional[int] = Field(None, description="Years of experience")
    level: Optional[str] = Field(None, description="Skill level: expert|advanced|intermediate|beginner")
    
    # Common properties for certifications
    grade: Optional[str] = Field(None, description="Certification grade")
    percentage: Optional[int] = Field(None, description="Certification percentage")
    year_obtained: Optional[int] = Field(None, description="Year certification was obtained")
    expires: Optional[int] = Field(None, description="Year certification expires")
    
    # Common properties for requirements (JD)
    required: Optional[bool] = Field(None, description="Whether feature is required (for JD)")
    preferred: Optional[bool] = Field(None, description="Whether feature is preferred (for JD)")
    min_years: Optional[int] = Field(None, description="Minimum years required (for JD)")
    
    # Common properties for education
    degree: Optional[str] = Field(None, description="Degree level")
    field: Optional[str] = Field(None, description="Field of study")
    institution: Optional[str] = Field(None, description="Educational institution")
    
    # Common properties for languages
    fluency: Optional[str] = Field(None, description="Language fluency level")
    certification: Optional[str] = Field(None, description="Language certification")
    
    # General properties
    industry: Optional[str] = Field(None, description="Industry context")
    description: Optional[str] = Field(None, description="Feature description")
    
    # Allow additional properties for flexibility
    model_config = {"extra": "allow"}


class Feature(BaseSharedModel):
    """Document feature model (e.g., skill, certification, experience, etc.)."""
    
    name: str = Field(..., description="Feature name")
    type: str = Field(..., description="Feature type: skill|certification|experience|education|language|soft_skill|tool")
    properties: Optional[FeatureProperties] = Field(
        default_factory=FeatureProperties, 
        description="Feature-specific properties"
    )


class DocumentUpdateRequest(BaseSharedModel):
    """Request model for updating documents (used by AI services)."""
    
    file_type: Optional[str] = Field(
        None, 
        pattern="^(cv|jd)$", 
        description="Document type classification",
        examples=["cv", "jd"]
    )
    text_content: Optional[str] = Field(
        None, 
        description="Extracted text content from the document in markdown format"
    )
    role: Optional[str] = Field(
        None, 
        description="Identified job role or position"
    )
    features: Optional[List[Feature]] = Field(
        None, 
        description="List of extracted features (skills, certifications, etc.)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata fields"
    )


class DocumentResponse(BaseSharedModel, TimestampMixin, UserContextMixin):
    """Document response model with full document information."""
    
    id: UUID = Field(..., description="Document UUID")
    filename: str = Field(..., description="Original filename")
    file_type: Optional[str] = Field(None, pattern="^(cv|jd)$", description="Document type: cv or jd")
    content_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., description="File size in bytes")
    storage_path: Optional[str] = Field(None, description="Internal storage path")
    text_content: Optional[str] = Field(None, description="Extracted text content")
    role: Optional[str] = Field(None, description="Primary role or job title")
    features: Optional[List[Feature]] = Field(None, description="Extracted features")
    processing_status: Optional[str] = Field(None, description="Processing status: pending|processing|completed|failed")
    processing_error: Optional[str] = Field(None, description="Processing error message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class DocumentListResponse(BaseSharedModel):
    """Response model for document listing with pagination."""
    
    documents: List[DocumentResponse] = Field(..., description="List of documents")
    total_count: int = Field(..., description="Total number of documents")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Items skipped")
    has_more: bool = Field(..., description="Whether there are more documents")


class BulkUploadResponse(BaseSharedModel):
    """Response model for bulk document upload operations."""
    
    total_files: int = Field(..., description="Total number of files processed")
    successful_uploads: int = Field(..., description="Number of successful uploads")
    failed_uploads: int = Field(..., description="Number of failed uploads")
    results: List[Dict[str, Any]] = Field(..., description="Individual file results")


class DocumentUpdateResponse(BaseSharedModel):
    """Response model for document update operations."""
    
    success: bool = Field(..., description="Update success status")
    data: Dict[str, Any] = Field(..., description="Update result data")
    meta: Dict[str, Any] = Field(..., description="Response metadata")


class HealthResponse(BaseSharedModel):
    """Health check response model."""
    
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(..., description="Health check timestamp")
    version: str = Field(..., description="Service version")
    dependencies: Optional[Dict[str, Any]] = Field(None, description="Dependency status")


class ValidationError(BaseSharedModel):
    """Validation error details."""
    
    loc: List[Union[str, int]] = Field(..., description="Error location")
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class HTTPValidationError(BaseSharedModel):
    """HTTP validation error response."""
    
    detail: List[ValidationError] = Field(..., description="Validation error details")
