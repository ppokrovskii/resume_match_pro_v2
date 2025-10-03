"""
Base classes and utilities for shared models.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class BaseSharedModel(BaseModel):
    """Base class for all shared models with common configuration."""

    model_config = {
        "from_attributes": True,
        "use_enum_values": True,
        "validate_assignment": True,
        "arbitrary_types_allowed": False,
        "extra": "forbid",
    }


class TimestampMixin(BaseModel):
    """Mixin for models with timestamp fields."""

    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")


class UserContextMixin(BaseModel):
    """Mixin for models with user context."""

    user_id: UUID = Field(..., description="User ID who owns this resource")
    organization_id: Optional[UUID] = Field(
        None, description="Organization ID (for enterprise users)"
    )


class MetadataMixin(BaseModel):
    """Mixin for models with flexible metadata."""

    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class PaginationResponse(BaseSharedModel):
    """Base pagination response model."""

    total_count: int = Field(..., description="Total number of items")
    limit: int = Field(..., description="Items per page")
    offset: int = Field(..., description="Items skipped")
    has_more: bool = Field(..., description="Whether there are more items")


class ErrorResponse(BaseSharedModel):
    """Standard error response model."""

    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None, description="Additional error details"
    )


class SuccessResponse(BaseSharedModel):
    """Standard success response model."""

    success: bool = Field(True, description="Operation success status")
    message: Optional[str] = Field(None, description="Success message")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


# Version information
__version__ = "0.1.0"
__all__ = [
    "BaseSharedModel",
    "TimestampMixin",
    "UserContextMixin",
    "MetadataMixin",
    "PaginationResponse",
    "ErrorResponse",
    "SuccessResponse",
]
