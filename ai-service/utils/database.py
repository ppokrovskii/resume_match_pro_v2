"""
Database utilities for AI service
"""

import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Generator, Dict, List, Any, Optional, Tuple
from uuid import UUID
import json

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Database connection manager for AI service"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self._connection = None
    
    def connect(self) -> None:
        """Establish database connection"""
        try:
            self._connection = psycopg2.connect(
                self.database_url,
                cursor_factory=RealDictCursor
            )
            logger.info("AI service database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("AI service database connection closed")
    
    @contextmanager
    def get_cursor(self) -> Generator[RealDictCursor, None, None]:
        """Get database cursor with automatic transaction management"""
        if not self._connection:
            self.connect()
        
        cursor = self._connection.cursor()
        try:
            yield cursor
            self._connection.commit()
        except Exception as e:
            self._connection.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            cursor.close()


# Global database connection instance
db_connection: Optional[DatabaseConnection] = None


def init_db(database_url: str) -> None:
    """Initialize database connection"""
    global db_connection
    db_connection = DatabaseConnection(database_url)
    db_connection.connect()


def get_db() -> DatabaseConnection:
    """Get database connection instance"""
    if not db_connection:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return db_connection


class EmbeddingRepository:
    """Embedding database operations"""
    
    def __init__(self):
        self.db = get_db()
    
    def create_embedding(self, embedding_data: Dict[str, Any]) -> UUID:
        """Create a new embedding record"""
        with self.db.get_cursor() as cursor:
            query = """
                INSERT INTO document_embeddings (
                    document_id, embedding, text_chunks, metadata
                ) VALUES (
                    %(document_id)s, %(embedding)s, %(text_chunks)s, %(metadata)s
                ) RETURNING id
            """
            cursor.execute(query, embedding_data)
            result = cursor.fetchone()
            return result['id']
    
    def get_embedding(self, document_id: UUID) -> Optional[Dict[str, Any]]:
        """Get embedding by document ID"""
        with self.db.get_cursor() as cursor:
            query = "SELECT * FROM document_embeddings WHERE document_id = %s"
            cursor.execute(query, (document_id,))
            return cursor.fetchone()
    
    def get_embeddings_by_user(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get all embeddings for documents owned by user"""
        with self.db.get_cursor() as cursor:
            query = """
                SELECT de.*, d.user_id, d.file_type, d.filename
                FROM document_embeddings de
                JOIN documents d ON de.document_id = d.id
                WHERE d.user_id = %s
            """
            cursor.execute(query, (user_id,))
            return cursor.fetchall()
    
    def update_embedding(self, document_id: UUID, embedding_data: Dict[str, Any]) -> bool:
        """Update existing embedding"""
        with self.db.get_cursor() as cursor:
            query = """
                UPDATE document_embeddings 
                SET embedding = %(embedding)s, text_chunks = %(text_chunks)s, metadata = %(metadata)s
                WHERE document_id = %(document_id)s
            """
            params = {**embedding_data, 'document_id': document_id}
            cursor.execute(query, params)
            return cursor.rowcount > 0
    
    def delete_embedding(self, document_id: UUID) -> bool:
        """Delete embedding by document ID"""
        with self.db.get_cursor() as cursor:
            query = "DELETE FROM document_embeddings WHERE document_id = %s"
            cursor.execute(query, (document_id,))
            return cursor.rowcount > 0
    
    def similarity_search(
        self, 
        query_embedding: List[float], 
        user_id: UUID,
        document_type: Optional[str] = None,
        limit: int = 10,
        similarity_threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """Perform vector similarity search"""
        with self.db.get_cursor() as cursor:
            # Build conditions
            conditions = ["d.user_id = %s"]
            params = [user_id]
            
            if document_type:
                conditions.append("d.file_type = %s")
                params.append(document_type)
            
            # Add similarity threshold
            conditions.append("(de.embedding <=> %s::vector) <= %s")
            params.extend([query_embedding, 1.0 - similarity_threshold])
            
            query = f"""
                SELECT 
                    d.id as document_id,
                    d.filename,
                    d.file_type,
                    d.text_content,
                    de.text_chunks,
                    (1 - (de.embedding <=> %s::vector)) as similarity_score
                FROM document_embeddings de
                JOIN documents d ON de.document_id = d.id
                WHERE {' AND '.join(conditions)}
                ORDER BY de.embedding <=> %s::vector
                LIMIT %s
            """
            
            # Add query embedding twice (for SELECT and ORDER BY)
            all_params = [query_embedding] + params + [query_embedding, limit]
            cursor.execute(query, all_params)
            return cursor.fetchall()
    
    def get_match_results(self, cv_id: UUID, jd_ids: List[UUID]) -> List[Dict[str, Any]]:
        """Get existing match results"""
        with self.db.get_cursor() as cursor:
            query = """
                SELECT * FROM match_results 
                WHERE cv_id = %s AND jd_id = ANY(%s)
            """
            cursor.execute(query, (cv_id, jd_ids))
            return cursor.fetchall()
    
    def save_match_results(self, match_results: List[Dict[str, Any]]) -> None:
        """Save match results to database"""
        with self.db.get_cursor() as cursor:
            for match in match_results:
                query = """
                    INSERT INTO match_results (
                        cv_id, jd_id, user_id, match_score, similarity_breakdown,
                        matching_skills, skill_gaps, confidence_level
                    ) VALUES (
                        %(cv_id)s, %(jd_id)s, %(user_id)s, %(match_score)s, %(similarity_breakdown)s,
                        %(matching_skills)s, %(skill_gaps)s, %(confidence_level)s
                    ) ON CONFLICT (cv_id, jd_id) DO UPDATE SET
                        match_score = EXCLUDED.match_score,
                        similarity_breakdown = EXCLUDED.similarity_breakdown,
                        matching_skills = EXCLUDED.matching_skills,
                        skill_gaps = EXCLUDED.skill_gaps,
                        confidence_level = EXCLUDED.confidence_level,
                        created_at = NOW()
                """
                cursor.execute(query, match)
    
    def get_embedding_stats(self, user_id: Optional[UUID] = None) -> Dict[str, Any]:
        """Get embedding statistics"""
        with self.db.get_cursor() as cursor:
            base_query = """
                SELECT 
                    COUNT(de.id) as total_embeddings,
                    COUNT(DISTINCT de.document_id) as total_documents,
                    AVG(array_length(de.text_chunks, 1)) as avg_chunks_per_document
                FROM document_embeddings de
            """
            
            if user_id:
                query = f"""
                    {base_query}
                    JOIN documents d ON de.document_id = d.id
                    WHERE d.user_id = %s
                """
                cursor.execute(query, (user_id,))
            else:
                cursor.execute(base_query)
            
            result = cursor.fetchone()
            return {
                'total_embeddings': result['total_embeddings'] or 0,
                'total_documents': result['total_documents'] or 0,
                'average_chunks_per_document': float(result['avg_chunks_per_document'] or 0),
                'total_tokens_processed': 0,  # Would need to be tracked separately
                'cache_hit_rate': 0.0  # Would need to be calculated from cache metrics
            }
    
    def batch_create_embeddings(self, embeddings_data: List[Dict[str, Any]]) -> List[UUID]:
        """Create multiple embeddings in a single transaction"""
        with self.db.get_cursor() as cursor:
            created_ids = []
            for embedding_data in embeddings_data:
                query = """
                    INSERT INTO document_embeddings (
                        document_id, embedding, text_chunks, metadata
                    ) VALUES (
                        %(document_id)s, %(embedding)s, %(text_chunks)s, %(metadata)s
                    ) RETURNING id
                """
                cursor.execute(query, embedding_data)
                result = cursor.fetchone()
                created_ids.append(result['id'])
            
            return created_ids
    
    def get_documents_without_embeddings(self, user_id: UUID) -> List[Dict[str, Any]]:
        """Get documents that don't have embeddings yet"""
        with self.db.get_cursor() as cursor:
            query = """
                SELECT d.* FROM documents d
                LEFT JOIN document_embeddings de ON d.id = de.document_id
                WHERE d.user_id = %s AND de.id IS NULL AND d.text_content IS NOT NULL
            """
            cursor.execute(query, (user_id,))
            return cursor.fetchall()






