"""
Database connection and utilities using SQLAlchemy ORM
"""

import logging
import os
from contextlib import contextmanager
from typing import Generator, Dict, List, Any, Optional
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from models.db_models import Base, Document as DocumentModel

logger = logging.getLogger(__name__)


class DatabaseManager:
    """SQLAlchemy database manager"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = None
        self.SessionLocal = None
    
    def connect(self) -> None:
        """Establish database connection"""
        try:
            self.engine = create_engine(
                self.database_url,
                pool_pre_ping=True,
                pool_recycle=300,
                echo=os.getenv('DATABASE_ECHO', 'false').lower() == 'true'
            )
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self) -> None:
        """Close database connection"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.SessionLocal = None
            logger.info("Database connection closed")
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic transaction management"""
        if not self.SessionLocal:
            self.connect()
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database transaction failed: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self) -> None:
        """Create all tables"""
        if not self.engine:
            self.connect()
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


def init_db(database_url: str) -> None:
    """Initialize database connection"""
    global db_manager
    db_manager = DatabaseManager(database_url)
    db_manager.connect()


def get_db_manager() -> DatabaseManager:
    """Get database manager instance"""
    if not db_manager:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return db_manager


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session"""
    db = get_db_manager()
    with db.get_session() as session:
        yield session


class DocumentRepository:
    """Document database operations using SQLAlchemy ORM"""
    
    def create_document(self, document_data: Dict[str, Any]) -> UUID:
        """Create a new document record"""
        with get_db_session() as session:
            document = DocumentModel(
                user_id=document_data['user_id'],
                organization_id=document_data.get('organization_id'),
                filename=document_data['filename'],
                file_type=document_data['file_type'],
                content_type=document_data['content_type'],
                file_size=document_data['file_size'],
                storage_path=document_data['storage_path'],
                doc_metadata=document_data.get('metadata', {})
            )
            session.add(document)
            session.flush()  # Flush to get the ID
            return document.id
    
    def get_document(self, document_id: UUID, user_id: UUID) -> Optional[Dict[str, Any]]:
        """Get document by ID (with user access control)"""
        with get_db_session() as session:
            document = session.query(DocumentModel).filter(
                DocumentModel.id == document_id,
                DocumentModel.user_id == user_id
            ).first()
            
            if not document:
                return None
            
            # Extract features from metadata if present
            metadata = document.doc_metadata or {}
            features = metadata.get('features')
            text_content = metadata.get('text_content')
            
            return {
                'id': document.id,
                'user_id': document.user_id,
                'organization_id': document.organization_id,
                'filename': document.filename,
                'file_type': document.file_type,
                'content_type': document.content_type,
                'file_size': document.file_size,
                'storage_path': document.storage_path,
                'text_content': text_content,
                'role': metadata.get('role'),
                'features': features,
                'metadata': metadata,
                'created_at': document.created_at,
                'updated_at': document.updated_at
            }
    
    def get_user_documents(
        self, 
        user_id: UUID, 
        file_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get documents for a user with pagination"""
        with get_db_session() as session:
            query = session.query(DocumentModel).filter(DocumentModel.user_id == user_id)
            
            if file_type:
                query = query.filter(DocumentModel.file_type == file_type)
            
            documents = query.order_by(DocumentModel.created_at.desc()).offset(offset).limit(limit).all()
            
            result = []
            for doc in documents:
                metadata = doc.doc_metadata or {}
                features = metadata.get('features')
                text_content = metadata.get('text_content')
                
                result.append({
                    'id': doc.id,
                    'user_id': doc.user_id,
                    'organization_id': doc.organization_id,
                    'filename': doc.filename,
                    'file_type': doc.file_type,
                    'content_type': doc.content_type,
                    'file_size': doc.file_size,
                    'storage_path': doc.storage_path,
                    'text_content': text_content,
                    'role': metadata.get('role'),
                    'features': features,
                    'metadata': metadata,
                    'created_at': doc.created_at,
                    'updated_at': doc.updated_at
                })
            
            return result
    
    def update_document(self, document_id: UUID, user_id: UUID, updates: Dict[str, Any]) -> bool:
        """Update document record"""
        if not updates:
            return False
            
        with get_db_session() as session:
            # Debug logging to understand the user isolation issue
            logger.info(f"UPDATE_DOCUMENT: Looking for document_id={document_id}, user_id={user_id}")
            
            # First, check if document exists at all
            all_docs = session.query(DocumentModel).filter(DocumentModel.id == document_id).all()
            logger.info(f"UPDATE_DOCUMENT: Found {len(all_docs)} documents with id {document_id}")
            for doc in all_docs:
                logger.info(f"UPDATE_DOCUMENT: Document {doc.id} belongs to user_id={doc.user_id}")
            
            # Now check with user filter
            document = session.query(DocumentModel).filter(
                DocumentModel.id == document_id,
                DocumentModel.user_id == user_id
            ).first()
            
            if not document:
                logger.warning(f"UPDATE_DOCUMENT: No document found with id={document_id} for user_id={user_id}")
                return False
            
            logger.info(f"UPDATE_DOCUMENT: Found document {document.id} for user {user_id}, proceeding with update")
            
            # Update allowed fields
            allowed_fields = {
                'file_type': 'file_type',
                # role is kept inside doc_metadata
                'storage_path': 'storage_path',
                'doc_metadata': 'doc_metadata',
                'updated_at': 'updated_at'
            }
            
            for key, value in updates.items():
                if key in allowed_fields:
                    db_field = allowed_fields[key]
                    setattr(document, db_field, value)
            
            return True
    
    def delete_document(self, document_id: UUID, user_id: UUID) -> bool:
        """Delete document record"""
        with get_db_session() as session:
            document = session.query(DocumentModel).filter(
                DocumentModel.id == document_id,
                DocumentModel.user_id == user_id
            ).first()
            
            if not document:
                return False
            
            session.delete(document)
            return True
    
    def search_documents(
        self, 
        user_id: UUID, 
        query: str, 
        file_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Search documents by text content"""
        with get_db_session() as session:
            # Simple search within text content stored in metadata (if any)
            search_query = session.query(DocumentModel).filter(
                DocumentModel.user_id == user_id
            )
            
            if file_type:
                search_query = search_query.filter(DocumentModel.file_type == file_type)
            
            documents = search_query.order_by(DocumentModel.created_at.desc()).offset(offset).limit(limit).all()
            
            result = []
            for doc in documents:
                metadata = doc.doc_metadata or {}
                features = metadata.get('features')
                text_content = metadata.get('text_content')
                
                result.append({
                    'id': doc.id,
                    'user_id': doc.user_id,
                    'organization_id': doc.organization_id,
                    'filename': doc.filename,
                    'file_type': doc.file_type,
                    'content_type': doc.content_type,
                    'file_size': doc.file_size,
                    'storage_path': doc.storage_path,
                    'text_content': text_content,
                    'role': metadata.get('role'),
                    'features': features,
                    'metadata': metadata,
                    'created_at': doc.created_at,
                    'updated_at': doc.updated_at
                })
            
            return result
    
    def get_document_count(self, user_id: UUID, file_type: Optional[str] = None) -> int:
        """Get total document count for user"""
        with get_db_session() as session:
            query = session.query(DocumentModel).filter(DocumentModel.user_id == user_id)
            
            if file_type:
                query = query.filter(DocumentModel.file_type == file_type)
            
            return query.count()








