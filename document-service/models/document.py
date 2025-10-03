"""
Document data models using Pydantic
"""

from datetime import datetime
from typing import Dict, Optional, Any, List
from uuid import UUID
from pydantic import BaseModel, Field


class FeatureProperties(BaseModel):
    """Properties for a document feature"""
    # Allow arbitrary fields for flexibility
    model_config = {"extra": "allow"}
    
    def __getitem__(self, key):
        """Allow dict-like access for backward compatibility with tests"""
        return getattr(self, key)
        
    def __setitem__(self, key, value):
        """Allow dict-like assignment for backward compatibility with tests"""
        setattr(self, key, value)
        
    def __eq__(self, other):
        """Allow comparison with dict for backward compatibility with tests"""
        if isinstance(other, dict):
            # Convert self to dict for comparison
            self_dict = {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
            return self_dict == other
        return super().__eq__(other)


class Feature(BaseModel):
    """Document feature model (e.g., skill, certification)"""
    name: str = Field(..., description="Name of the feature (e.g., 'Python', 'AWS Certified')")
    type: str = Field(..., description="Type of the feature (e.g., 'skill', 'certification')")
    properties: Optional[FeatureProperties] = Field(default_factory=lambda: FeatureProperties(), description="Additional properties for the feature")


class DocumentMetadata(BaseModel):
    """Document metadata model"""
    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., pattern="^(cv|jd)$", description="Document type")
    content_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    storage_path: Optional[str] = Field(None, description="Storage path")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Document(BaseModel):
    """Document model"""
    id: Optional[UUID] = Field(None, description="Document ID")
    user_id: UUID = Field(..., description="User ID who uploaded the document")
    organization_id: Optional[UUID] = Field(None, description="Organization ID")
    filename: str = Field(..., description="Original filename")
    file_type: Optional[str] = Field(None, description="Document type (determined by external services)")
    content_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    storage_path: Optional[str] = Field(None, description="Storage path")
    # Values persisted inside doc_metadata for flexibility
    text_content: Optional[str] = Field(None, description="Extracted text content (markdown format)")
    role: Optional[str] = Field(None, description="Identified role/position")
    features: Optional[List[Feature]] = Field(None, description="Extracted features")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    model_config = {"from_attributes": True}


class DocumentUploadRequest(BaseModel):
    """Document upload request model"""
    filename: str = Field(..., description="Filename")
    content_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., gt=0, le=16*1024*1024, description="File size (max 16MB)")
    file_type: str = Field(..., pattern="^(cv|jd)$", description="Document type")


class DocumentUploadResponse(BaseModel):
    """Document upload response model"""
    id: UUID = Field(..., description="Document ID")
    filename: str = Field(..., description="Original filename")
    file_type: Optional[str] = Field(None, description="Document type (determined by external services)")
    content_type: str = Field(..., description="MIME type")
    file_size: int = Field(..., description="File size in bytes")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    created_at: datetime = Field(..., description="Creation timestamp")


class BulkUploadResponse(BaseModel):
    """Bulk upload response model"""
    total_files: int = Field(..., description="Total number of files processed")
    successful_uploads: int = Field(..., description="Number of successful uploads")
    failed_uploads: int = Field(..., description="Number of failed uploads")
    results: List[Dict[str, Any]] = Field(..., description="Individual file results")


class DocumentListResponse(BaseModel):
    """Document list response model"""
    documents: List[Document] = Field(
        ..., 
        description="List of documents",
        example=[
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "987fcdeb-51a2-43d1-9f12-345678901234",
                "filename": "john_doe_resume.pdf",
                "file_type": "cv",
                "content_type": "application/pdf",
                "file_size": 1024000,
                "storage_path": "documents/user123/cvs/john_doe_resume.pdf",
                "metadata": {"original_filename": "john_doe_resume.pdf"},
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        ]
    )
    total_count: int = Field(..., description="Total number of documents", example=25)
    limit: int = Field(..., description="Limit per page", example=10)
    offset: int = Field(..., description="Offset for pagination", example=0)
    has_more: bool = Field(..., description="Whether there are more documents", example=True)


class DocumentSearchRequest(BaseModel):
    """Document search request model"""
    query: str = Field(..., min_length=1, description="Search query")
    file_type: Optional[str] = Field(None, pattern="^(cv|jd)$", description="Filter by document type")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")
    offset: int = Field(0, ge=0, description="Results offset for pagination")


class DocumentSearchResponse(BaseModel):
    """Document search response model"""
    documents: List[Document] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total matching documents")
    query: str = Field(..., description="Search query used")
    limit: int = Field(..., description="Limit per page")
    offset: int = Field(..., description="Offset for pagination")
    has_more: bool = Field(..., description="Whether there are more results")


class DocumentUpdateRequest(BaseModel):
    """Document update request model for external services"""
    file_type: Optional[str] = Field(
        None, 
        pattern="^(cv|jd)$", 
        description="Document type classification",
        example="cv"
    )
    text_content: Optional[str] = Field(
        None, 
        description="Extracted text content from the document (markdown format)",
        example="# John Doe\n\n## Experience\n\n**Software Engineer** at TechCorp\n- Python development\n- AWS cloud services"
    )
    role: Optional[str] = Field(
        None, 
        description="Identified job role or position",
        example="Python Developer"
    )
    features: Optional[List[Feature]] = Field(
        None, 
        description="List of extracted features (skills, certifications, etc.)",
        example=[
            {"name": "Python", "type": "skill", "properties": {"years": 5, "level": "expert"}},
            {"name": "AWS Solutions Architect", "type": "certification", "properties": {"grade": "A", "year_obtained": 2023}}
        ]
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, 
        description="Additional metadata fields",
        example={"processing_version": "1.2.0", "confidence_score": 0.95}
    )

    model_config = {"extra": "forbid"}  # Prevent additional fields


class DocumentUpdateResponse(BaseModel):
    """Document update response model"""
    success: bool = Field(..., description="Update success status")
    data: Dict[str, Any] = Field(..., description="Update result data")
    meta: Dict[str, Any] = Field(..., description="Response metadata")

