"""
Embedding service using Azure OpenAI
"""

import logging
import os
import time
from typing import List, Dict, Any, Optional, Tuple
from uuid import UUID
import hashlib
import json

import openai
from openai import AzureOpenAI
import redis
import numpy as np

from utils.error_handler import EmbeddingGenerationError, ModelUnavailableError
from utils.database import EmbeddingRepository

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing embeddings using Azure OpenAI"""
    
    def __init__(self):
        # Azure OpenAI configuration
        self.endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        self.api_key = os.getenv('AZURE_OPENAI_API_KEY')
        self.api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-01')
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-ada-002')
        
        if not self.endpoint or not self.api_key:
            logger.warning("Azure OpenAI credentials not configured. Using mock embeddings.")
            self.client = None
        else:
            try:
                self.client = AzureOpenAI(
                    azure_endpoint=self.endpoint,
                    api_key=self.api_key,
                    api_version=self.api_version
                )
                logger.info("Azure OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Azure OpenAI client: {e}")
                self.client = None
        
        # Redis cache for embeddings
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        try:
            self.cache = redis.from_url(redis_url, decode_responses=False)
            self.cache.ping()  # Test connection
            logger.info("Redis cache connected")
        except Exception as e:
            logger.warning(f"Redis cache not available: {e}")
            self.cache = None
        
        # Database repository
        self.repository = EmbeddingRepository()
        
        # Configuration
        self.max_chunk_size = 8000  # Max tokens per chunk for OpenAI
        self.embedding_dimension = 1536  # OpenAI embedding dimension
        self.cache_ttl = 86400  # 24 hours cache TTL
    
    def _generate_cache_key(self, text: str, model: str) -> str:
        """Generate cache key for text embedding"""
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        return f"embedding:{model}:{text_hash}"
    
    def _chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
        """Split text into overlapping chunks"""
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings within the last 200 characters
                last_period = text.rfind('.', max(start, end - 200), end)
                last_newline = text.rfind('\n', max(start, end - 200), end)
                
                break_point = max(last_period, last_newline)
                if break_point > start:
                    end = break_point + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap
            if start >= len(text):
                break
        
        return chunks
    
    def _get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get embedding from cache"""
        if not self.cache:
            return None
        
        try:
            cache_key = self._generate_cache_key(text, self.embedding_model)
            cached_data = self.cache.get(cache_key)
            if cached_data:
                return json.loads(cached_data.decode('utf-8'))
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        
        return None
    
    def _cache_embedding(self, text: str, embedding: List[float]) -> None:
        """Cache embedding"""
        if not self.cache:
            return
        
        try:
            cache_key = self._generate_cache_key(text, self.embedding_model)
            self.cache.setex(
                cache_key,
                self.cache_ttl,
                json.dumps(embedding)
            )
        except Exception as e:
            logger.warning(f"Cache write error: {e}")
    
    def _generate_mock_embedding(self, text: str) -> List[float]:
        """Generate mock embedding for development/testing"""
        # Create a deterministic but pseudo-random embedding based on text
        text_hash = hashlib.md5(text.encode('utf-8')).digest()
        np.random.seed(int.from_bytes(text_hash[:4], byteorder='big'))
        
        # Generate normalized random vector
        embedding = np.random.normal(0, 1, self.embedding_dimension)
        embedding = embedding / np.linalg.norm(embedding)
        
        return embedding.tolist()
    
    async def generate_embedding(self, text: str) -> Tuple[List[float], int]:
        """
        Generate embedding for text
        Returns (embedding, token_count)
        """
        if not text.strip():
            raise EmbeddingGenerationError("Empty text provided")
        
        # Check cache first
        cached_embedding = self._get_cached_embedding(text)
        if cached_embedding:
            logger.debug("Using cached embedding")
            return cached_embedding, len(text.split())  # Approximate token count
        
        try:
            if self.client:
                # Use Azure OpenAI
                response = self.client.embeddings.create(
                    model=self.embedding_model,
                    input=text
                )
                
                embedding = response.data[0].embedding
                token_count = response.usage.total_tokens
                
                # Cache the result
                self._cache_embedding(text, embedding)
                
                logger.debug(f"Generated embedding using Azure OpenAI: {token_count} tokens")
                return embedding, token_count
            
            else:
                # Use mock embedding for development
                embedding = self._generate_mock_embedding(text)
                token_count = len(text.split())  # Approximate
                
                logger.debug("Generated mock embedding")
                return embedding, token_count
                
        except openai.RateLimitError as e:
            logger.error(f"OpenAI rate limit exceeded: {e}")
            raise EmbeddingGenerationError("Rate limit exceeded. Please try again later.")
        
        except openai.APIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise ModelUnavailableError(f"AI model temporarily unavailable: {str(e)}")
        
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            raise EmbeddingGenerationError(f"Failed to generate embedding: {str(e)}")
    
    async def generate_document_embeddings(
        self, 
        text: str, 
        document_id: UUID,
        chunk_size: int = 1000,
        overlap: int = 100
    ) -> Dict[str, Any]:
        """
        Generate embeddings for a document with chunking
        """
        try:
            start_time = time.time()
            
            # Split text into chunks
            text_chunks = self._chunk_text(text, chunk_size, overlap)
            logger.info(f"Split document into {len(text_chunks)} chunks")
            
            embeddings = []
            total_tokens = 0
            
            # Generate embeddings for each chunk
            for i, chunk in enumerate(text_chunks):
                try:
                    embedding, tokens = await self.generate_embedding(chunk)
                    embeddings.append(embedding)
                    total_tokens += tokens
                    
                    logger.debug(f"Generated embedding for chunk {i+1}/{len(text_chunks)}")
                    
                    # Small delay to avoid rate limiting
                    if self.client and i < len(text_chunks) - 1:
                        time.sleep(0.1)
                        
                except Exception as e:
                    logger.error(f"Failed to generate embedding for chunk {i}: {e}")
                    # Use zero vector for failed chunks
                    embeddings.append([0.0] * self.embedding_dimension)
            
            # Average the embeddings (simple approach)
            if embeddings:
                avg_embedding = np.mean(embeddings, axis=0).tolist()
            else:
                raise EmbeddingGenerationError("No embeddings generated")
            
            # Store in database
            embedding_data = {
                'document_id': document_id,
                'embedding': avg_embedding,
                'text_chunks': text_chunks,
                'metadata': {
                    'total_tokens': total_tokens,
                    'chunk_count': len(text_chunks),
                    'model': self.embedding_model,
                    'processing_time': time.time() - start_time
                }
            }
            
            # Check if embedding exists, update or create
            existing = self.repository.get_embedding(document_id)
            if existing:
                self.repository.update_embedding(document_id, embedding_data)
                logger.info(f"Updated embedding for document {document_id}")
            else:
                embedding_id = self.repository.create_embedding(embedding_data)
                logger.info(f"Created embedding {embedding_id} for document {document_id}")
            
            return {
                'success': True,
                'document_id': document_id,
                'embeddings': embeddings,
                'text_chunks': text_chunks,
                'total_tokens': total_tokens,
                'processing_time': time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"Document embedding generation failed: {e}")
            if isinstance(e, EmbeddingGenerationError):
                raise
            raise EmbeddingGenerationError(f"Failed to generate document embeddings: {str(e)}")
    
    def get_document_embedding(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        """Get existing embedding for document"""
        try:
            return self.repository.get_embedding(document_id)
        except Exception as e:
            logger.error(f"Failed to get document embedding: {e}")
            return None
    
    async def batch_generate_embeddings(
        self, 
        documents: List[Dict[str, Any]], 
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """Generate embeddings for multiple documents"""
        results = []
        processed_count = 0
        failed_count = 0
        total_tokens = 0
        start_time = time.time()
        
        for doc in documents:
            try:
                document_id = doc['id']
                text_content = doc.get('text_content')
                
                if not text_content:
                    results.append({
                        'document_id': document_id,
                        'success': False,
                        'error': 'No text content'
                    })
                    failed_count += 1
                    continue
                
                # Check if embedding already exists
                if not force_regenerate and self.repository.get_embedding(document_id):
                    results.append({
                        'document_id': document_id,
                        'success': True,
                        'message': 'Embedding already exists'
                    })
                    processed_count += 1
                    continue
                
                # Generate embedding
                result = await self.generate_document_embeddings(
                    text_content, document_id
                )
                
                results.append({
                    'document_id': document_id,
                    'success': result['success'],
                    'tokens': result['total_tokens']
                })
                
                processed_count += 1
                total_tokens += result['total_tokens']
                
            except Exception as e:
                logger.error(f"Batch embedding failed for document {doc.get('id')}: {e}")
                results.append({
                    'document_id': doc.get('id'),
                    'success': False,
                    'error': str(e)
                })
                failed_count += 1
        
        return {
            'success': processed_count > 0,
            'processed_count': processed_count,
            'failed_count': failed_count,
            'total_tokens': total_tokens,
            'processing_time_ms': int((time.time() - start_time) * 1000),
            'results': results
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Health check for embedding service"""
        try:
            # Check Azure OpenAI connection
            openai_healthy = True
            if self.client:
                try:
                    # Try a simple embedding request
                    test_embedding, _ = self.generate_embedding("test")
                    openai_healthy = len(test_embedding) == self.embedding_dimension
                except Exception:
                    openai_healthy = False
            
            # Check cache connection
            cache_healthy = True
            if self.cache:
                try:
                    self.cache.ping()
                except Exception:
                    cache_healthy = False
            
            # Check database connection
            db_healthy = True
            try:
                self.repository.get_embedding_stats()
            except Exception:
                db_healthy = False
            
            overall_healthy = openai_healthy and cache_healthy and db_healthy
            
            return {
                'status': 'healthy' if overall_healthy else 'unhealthy',
                'openai': 'healthy' if openai_healthy else 'unhealthy',
                'cache': 'healthy' if cache_healthy else 'unhealthy',
                'database': 'healthy' if db_healthy else 'unhealthy',
                'model': self.embedding_model
            }
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }






