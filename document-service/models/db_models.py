"""
SQLAlchemy database models for document service

Following microservice boundaries:
- Document service only owns document and upload_session data
- User and organization data comes from identity provider (Auth0) or user service
- user_id and organization_id are foreign references without FK constraints
"""

from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4
from sqlalchemy import (
    Column, String, DateTime, Integer, Text, Boolean, 
    CheckConstraint, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Document(Base):
    """Document table - core entity owned by document service"""
    __tablename__ = 'documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # Reference to user in identity service
    organization_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to organization in identity service
    filename = Column(String(255), nullable=False)
    file_type = Column(String(20), nullable=True)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    storage_path = Column(Text, nullable=False)
    doc_metadata = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # No relationships to user/organization tables - they're in other services
    # user_id and organization_id are just foreign references
    
    __table_args__ = (
        CheckConstraint("file_type IS NULL OR file_type IN ('cv', 'jd')", name='check_document_file_type'),
        CheckConstraint("file_size > 0", name='check_document_file_size'),
        Index('idx_documents_user_id', 'user_id'),
        Index('idx_documents_organization_id', 'organization_id'),
        Index('idx_documents_file_type', 'file_type'),
        Index('idx_documents_created_at', 'created_at'),
    )


class UploadSession(Base):
    """Upload sessions table for tracking bulk uploads"""
    __tablename__ = 'upload_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False)  # Reference to user in identity service
    organization_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to organization in identity service
    session_type = Column(String(20), nullable=False)
    total_files = Column(Integer, default=0, nullable=False)
    processed_files = Column(Integer, default=0, nullable=False)
    failed_files = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default='pending', nullable=False)
    session_metadata = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)
    
    # No relationships to user/organization tables - they're in other services
    # user_id and organization_id are just foreign references
    
    __table_args__ = (
        CheckConstraint("session_type IN ('single', 'bulk')", name='check_session_type'),
        CheckConstraint("status IN ('pending', 'completed', 'failed')", name='check_upload_status'),
        Index('idx_upload_sessions_user_id', 'user_id'),
        Index('idx_upload_sessions_status', 'status'),
    )


# Utility function to create tables
def create_all_tables(engine):
    """Create all tables"""
    Base.metadata.create_all(engine)


# Utility function to drop tables
def drop_all_tables(engine):
    """Drop all tables"""
    Base.metadata.drop_all(engine)