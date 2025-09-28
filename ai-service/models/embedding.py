"""
Embedding data models
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class EmbeddingRequest(BaseModel):
    """Request model for generating embeddings"""
    text: str = Field(..., min_length=1, max_length=50000, description="Text to generate embeddings for")
    document_id: Optional[UUID] = Field(None, description="Associated document ID")
    chunk_size: int = Field(1000, ge=100, le=5000, description="Text chunk size for processing")
    overlap: int = Field(100, ge=0, le=500, description="Overlap between chunks")


class EmbeddingResponse(BaseModel):
    """Response model for embedding generation"""
    success: bool = Field(..., description="Operation success status")
    embeddings: List[List[float]] = Field(..., description="Generated embeddings")
    text_chunks: List[str] = Field(..., description="Text chunks that were processed")
    total_tokens: int = Field(..., description="Total tokens processed")
    model: str = Field(..., description="Model used for embedding generation")


class DocumentEmbedding(BaseModel):
    """Document embedding model"""
    id: Optional[UUID] = Field(None, description="Embedding ID")
    document_id: UUID = Field(..., description="Associated document ID")
    embedding: List[float] = Field(..., description="Embedding vector")
    text_chunks: List[str] = Field(..., description="Text chunks")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")

    class Config:
        from_attributes = True


class SimilaritySearchRequest(BaseModel):
    """Request model for similarity search"""
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    user_id: UUID = Field(..., description="User ID for filtering results")
    document_type: Optional[str] = Field(None, pattern="^(cv|job_description)$", description="Filter by document type")
    limit: int = Field(10, ge=1, le=100, description="Maximum results to return")
    similarity_threshold: float = Field(0.7, ge=0.0, le=1.0, description="Minimum similarity threshold")


class SimilaritySearchResponse(BaseModel):
    """Response model for similarity search"""
    results: List[Dict[str, Any]] = Field(..., description="Search results with similarity scores")
    query: str = Field(..., description="Original search query")
    total_results: int = Field(..., description="Total number of results")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")


class MatchRequest(BaseModel):
    """Request model for document matching"""
    cv_id: UUID = Field(..., description="CV document ID")
    jd_ids: List[UUID] = Field(..., min_items=1, max_items=50, description="Job description document IDs")
    user_id: UUID = Field(..., description="User ID for access control")


class MatchResult(BaseModel):
    """Match result between CV and JD"""
    cv_id: UUID = Field(..., description="CV document ID")
    jd_id: UUID = Field(..., description="Job description document ID")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0-1)")
    match_score: int = Field(..., ge=0, le=100, description="Match score (0-100)")
    matching_keywords: List[str] = Field(default_factory=list, description="Matching keywords found")
    skill_gaps: List[str] = Field(default_factory=list, description="Identified skill gaps")
    confidence_level: float = Field(..., ge=0.0, le=1.0, description="Confidence in the match")


class MatchResponse(BaseModel):
    """Response model for document matching"""
    matches: List[MatchResult] = Field(..., description="Match results")
    cv_id: UUID = Field(..., description="CV document ID")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    total_matches: int = Field(..., description="Total number of matches processed")


class EmbeddingStats(BaseModel):
    """Embedding statistics"""
    total_embeddings: int = Field(..., description="Total number of embeddings stored")
    total_documents: int = Field(..., description="Total number of documents with embeddings")
    average_chunks_per_document: float = Field(..., description="Average chunks per document")
    total_tokens_processed: int = Field(..., description="Total tokens processed")
    cache_hit_rate: float = Field(..., description="Cache hit rate percentage")


class BatchEmbeddingRequest(BaseModel):
    """Request model for batch embedding generation"""
    documents: List[Dict[str, Any]] = Field(..., min_items=1, max_items=100, description="Documents to process")
    user_id: UUID = Field(..., description="User ID")
    force_regenerate: bool = Field(False, description="Force regeneration of existing embeddings")


class BatchEmbeddingResponse(BaseModel):
    """Response model for batch embedding generation"""
    success: bool = Field(..., description="Overall operation success")
    processed_count: int = Field(..., description="Number of documents processed")
    failed_count: int = Field(..., description="Number of documents that failed")
    total_tokens: int = Field(..., description="Total tokens processed")
    processing_time_ms: int = Field(..., description="Total processing time")
    results: List[Dict[str, Any]] = Field(..., description="Individual processing results")

