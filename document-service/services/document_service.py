"""
Core document service business logic
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID, uuid4
from datetime import datetime

from models.document import Document, DocumentMetadata
from utils.database import DocumentRepository
from utils.file_validators import validate_upload_file, sanitize_filename
from utils.fastapi_error_handler import DocumentServiceError, DatabaseError
from utils.event_publisher import publish_document_uploaded, publish_document_updated, publish_document_deleted
from utils.audit_logger import AuditLogger
from services.storage_service import get_storage_service

logger = logging.getLogger(__name__)


class DocumentService:
    """Core document service for managing documents"""
    
    def __init__(self):
        self.repository = DocumentRepository()
        self.storage_service = get_storage_service()
    
    def upload_document(
        self,
        file_data: bytes,
        filename: str,
        content_type: str,
        file_type: Optional[str],
        user_id: UUID,
        organization_id: Optional[UUID] = None
    ) -> Document:
        """
        Upload and process a document
        """
        try:
            logger.info(f"Starting document upload: {filename} for user {user_id}")
            
            # Validate file
            file_size = len(file_data)
            sanitized_filename = sanitize_filename(filename)
            
            # Upload to storage
            storage_path = self.storage_service.upload_file(
                file_data=file_data,
                filename=sanitized_filename,
                content_type=content_type,
                user_id=str(user_id),
                file_type=file_type
            )
            
            # Store document metadata in database
            document_data = {
                'user_id': user_id,
                'organization_id': organization_id,
                'filename': filename,
                'file_type': file_type,
                'content_type': content_type,
                'file_size': file_size,
                'storage_path': storage_path,
                'metadata': {
                    'sanitized_filename': sanitized_filename,
                    'upload_timestamp': datetime.utcnow().isoformat()
                }
            }
            
            document_id = self.repository.create_document(document_data)
            
            # Retrieve and return the created document
            document_dict = self.repository.get_document(document_id, user_id)
            if not document_dict:
                raise DatabaseError("Failed to retrieve created document")
            
            document = Document(**document_dict)
            logger.info(f"Document uploaded successfully: {document_id}")
            
            # Publish document.uploaded event for text extraction service
            try:
                publish_document_uploaded(document.id, content_type)
                logger.debug(f"Published document.uploaded event for {document_id}")
            except Exception as e:
                logger.warning(f"Failed to publish document.uploaded event: {e}")
                # Don't fail the upload if event publishing fails
            
            # Audit log the upload
            AuditLogger.log_document_upload(
                document_id=document.id,
                user_id=user_id,
                filename=filename,
                file_type=file_type,
                file_size=file_size,
                success=True
            )
            
            return document
            
        except Exception as e:
            logger.error(f"Document upload failed: {e}")
            
            # Cleanup: try to remove uploaded file if storage succeeded
            if 'storage_path' in locals():
                try:
                    self.storage_service.delete_file(storage_path)
                except Exception as cleanup_error:
                    logger.error(f"Failed to cleanup uploaded file: {cleanup_error}")
            
            if isinstance(e, DocumentServiceError):
                raise
            raise DocumentServiceError(f"Document upload failed: {str(e)}")
    
    async def upload_multiple_documents(self, files, user_id: UUID):
        """Upload multiple documents - handles all the business logic"""
        from utils.file_validators import validate_upload_file, FileValidationError
        from utils.event_publisher import publish_document_uploaded
        
        results = []
        successful_uploads = 0
        failed_uploads = 0
        
        for file in files:
            try:
                if not file.filename:
                    results.append({
                        "filename": "unknown",
                        "success": False,
                        "error": "No filename provided"
                    })
                    failed_uploads += 1
                    continue
                
                # Read file data
                file_data = await file.read()
                
                # Validate file
                try:
                    class MockFile:
                        def __init__(self, filename, data, content_type):
                            self.filename = filename
                            self.data = data
                            self.content_type = content_type
                            
                        def read(self):
                            return self.data
                            
                        def seek(self, pos):
                            pass
                    
                    mock_file = MockFile(file.filename, file_data, file.content_type)
                    filename, content_type, file_size = validate_upload_file(mock_file)
                    
                except FileValidationError as e:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": str(e)
                    })
                    failed_uploads += 1
                    continue
                
                # Upload document using existing single upload method
                document = self.upload_document(
                    file_data=file_data,
                    filename=filename,
                    content_type=content_type,
                    file_type=None,
                    user_id=user_id
                )
                
                # Publish event
                try:
                    publish_document_uploaded(document.id, document.content_type)
                except Exception as e:
                    logger.warning(f"Failed to publish event for document {document.id}: {e}")
                
                results.append({
                    "filename": filename,
                    "success": True,
                    "document_id": str(document.id),
                    "file_type": document.file_type,
                    "content_type": document.content_type,
                    "file_size": document.file_size,
                    "created_at": document.created_at.isoformat()
                })
                successful_uploads += 1
                
            except Exception as e:
                logger.error(f"Failed to upload file {file.filename}: {e}")
                results.append({
                    "filename": file.filename,
                    "success": False,
                    "error": "Upload failed"
                })
                failed_uploads += 1
        
        from models.document import BulkUploadResponse
        return BulkUploadResponse(
            total_files=len(files),
            successful_uploads=successful_uploads,
            failed_uploads=failed_uploads,
            results=results
        )
    
    def get_document(self, document_id: UUID, user_id: UUID) -> Optional[Document]:
        """Get document by ID"""
        try:
            document_dict = self.repository.get_document(document_id, user_id)
            if not document_dict:
                return None
            
            return Document(**document_dict)
            
        except Exception as e:
            logger.error(f"Failed to get document {document_id}: {e}")
            raise DatabaseError(f"Failed to retrieve document: {str(e)}")
    
    def get_user_documents(
        self,
        user_id: UUID,
        file_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> tuple[List[Document], int]:
        """
        Get documents for a user with pagination
        
        Returns:
            tuple: (documents, total_count) where documents is List[Document] 
                   and total_count is the total number of documents for the user
        """
        try:
            # Get documents for current page
            documents_data = self.repository.get_user_documents(
                user_id, file_type, limit, offset
            )
            
            # Get total count for pagination
            total_count = self.repository.get_document_count(
                user_id, file_type
            )
            
            documents = [Document(**doc_data) for doc_data in documents_data]
            
            return documents, total_count
            
        except Exception as e:
            logger.error(f"Failed to get user documents: {e}")
            raise DatabaseError(f"Failed to retrieve documents: {str(e)}")
    
    def download_document(self, document_id: UUID, user_id: UUID) -> tuple[bytes, str, str]:
        """
        Download document file
        Returns (file_data, content_type, filename)
        """
        try:
            # Get document metadata
            document = self.get_document(document_id, user_id)
            if not document:
                raise FileNotFoundError("Document not found")
            
            if not document.storage_path:
                raise FileNotFoundError("Document file not found in storage")
            
            # Download file from storage
            file_data, storage_content_type = self.storage_service.download_file(
                document.storage_path
            )
            
            logger.info(f"Document downloaded: {document_id}")
            return file_data, document.content_type, document.filename
            
        except DocumentServiceError:
            raise
        except Exception as e:
            logger.error(f"Failed to download document {document_id}: {e}")
            raise DocumentServiceError(f"Document download failed: {str(e)}")
    
    def delete_document(self, document_id: UUID, user_id: UUID) -> bool:
        """Delete document and its file"""
        try:
            # Get document metadata
            document = self.get_document(document_id, user_id)
            if not document:
                raise FileNotFoundError("Document not found")
            
            # Delete file from storage
            if document.storage_path:
                try:
                    self.storage_service.delete_file(document.storage_path)
                    logger.info(f"File deleted from storage: {document.storage_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete file from storage: {e}")
                    # Continue with database deletion even if storage deletion fails
            
            # Delete from database
            success = self.repository.delete_document(document_id, user_id)
            
            if success:
                logger.info(f"Document deleted successfully: {document_id}")
                
                # Publish document.deleted event for cleanup services
                try:
                    publish_document_deleted(document_id, user_id)
                    logger.debug(f"Published document.deleted event for {document_id}")
                except Exception as e:
                    logger.warning(f"Failed to publish document.deleted event: {e}")
                    # Don't fail the deletion if event publishing fails
                
                # Audit log the deletion
                AuditLogger.log_document_delete(
                    document_id=document_id,
                    user_id=user_id,
                    success=True
                )
            
            return success
            
        except DocumentServiceError:
            raise
        except FileNotFoundError:
            raise  # Re-raise FileNotFoundError as-is
        except DatabaseError:
            raise  # Re-raise DatabaseError as-is (will be caught by router as 404)
        except Exception as e:
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise DocumentServiceError(f"Document deletion failed: {str(e)}")
    
    def search_documents(
        self,
        user_id: UUID,
        query: str,
        file_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Document]:
        """Search documents by text content"""
        try:
            documents_data = self.repository.search_documents(
                user_id, query, file_type, limit, offset
            )
            
            return [Document(**doc_data) for doc_data in documents_data]
            
        except Exception as e:
            logger.error(f"Failed to search documents: {e}")
            raise DatabaseError(f"Document search failed: {str(e)}")
    
    def get_document_count(self, user_id: UUID, file_type: Optional[str] = None) -> int:
        """Get total document count for user"""
        try:
            return self.repository.get_document_count(user_id, file_type)
        except Exception as e:
            logger.error(f"Failed to get document count: {e}")
            raise DatabaseError(f"Failed to get document count: {str(e)}")
    
    def update_document_metadata(self, document_id: UUID, user_id: UUID, update_data: Dict[str, Any]) -> bool:
        """Update document metadata (for external services)"""
        try:
            # Get document
            document = self.get_document(document_id, user_id)
            if not document:
                raise FileNotFoundError("Document not found")
            
            # Prepare updates - handle both direct fields and metadata
            updates = {'updated_at': datetime.utcnow()}
            
            # Handle direct document fields
            direct_fields = ['file_type']
            for field in direct_fields:
                if field in update_data:
                    updates[field] = update_data[field]
            
            # Handle features and metadata together (both stored in doc_metadata JSON field)
            existing_metadata = document.metadata or {}
            
            # Handle features field (convert to JSON for database storage)
            if 'features' in update_data:
                features_data = update_data['features']
                if features_data is not None:
                    # Convert Feature objects to dictionaries if needed
                    if isinstance(features_data, list):
                        features_json = []
                        for feature in features_data:
                            if hasattr(feature, 'model_dump'):
                                features_json.append(feature.model_dump())
                            elif isinstance(feature, dict):
                                features_json.append(feature)
                            else:
                                features_json.append(dict(feature))
                        existing_metadata['features'] = features_json
                    else:
                        existing_metadata['features'] = features_data
                else:
                    existing_metadata['features'] = None
            
            # Map role and text_content into metadata for persistence
            if 'role' in update_data:
                existing_metadata['role'] = update_data['role']
            if 'text_content' in update_data:
                existing_metadata['text_content'] = update_data['text_content']

            # Handle additional metadata (merge with existing metadata)
            if 'metadata' in update_data:
                new_metadata = update_data['metadata'] or {}
                existing_metadata.update(new_metadata)
            
            # Only update doc_metadata if we have features or metadata updates
            if 'features' in update_data or 'metadata' in update_data or 'role' in update_data or 'text_content' in update_data:
                updates['doc_metadata'] = existing_metadata
            
            success = self.repository.update_document(document_id, user_id, updates)
            
            if success:
                logger.info(f"Document metadata updated: {document_id} with fields: {list(update_data.keys())}")
                
                # Publish document.updated event for AI matching service
                try:
                    updated_document = self.get_document(document_id, user_id)
                    if updated_document:
                        document_dict = updated_document.model_dump()
                        publish_document_updated(document_dict)
                        logger.debug(f"Published document.updated event for {document_id}")
                except Exception as e:
                    logger.warning(f"Failed to publish document.updated event: {e}")
                    # Don't fail the update if event publishing fails
                
                # Audit log the update
                AuditLogger.log_document_update(
                    document_id=document_id,
                    user_id=user_id,
                    changes=update_data,
                    success=True
                )
            
            return success
            
        except DocumentServiceError:
            raise
        except FileNotFoundError:
            raise  # Re-raise FileNotFoundError as-is
        except Exception as e:
            logger.error(f"Failed to update document metadata {document_id}: {e}")
            raise DocumentServiceError(f"Metadata update failed: {str(e)}")
    
    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for document service and all dependencies"""
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'document-service',
            'version': '1.0.0',
            'checks': {}
        }
        
        # Check database connection
        try:
            # Test database with a simple query
            self.repository.get_document_count(UUID('00000000-0000-0000-0000-000000000000'))
            health_status['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            health_status['checks']['database'] = {
                'status': 'unhealthy',
                'message': f'Database connection failed: {str(e)}'
            }
            health_status['status'] = 'unhealthy'
        
        # Check storage service (Azure Blob Storage)
        try:
            storage_check = self.storage_service.health_check()
            if storage_check:
                health_status['checks']['storage'] = {
                    'status': 'healthy',
                    'message': 'Azure Blob Storage connection successful'
                }
            else:
                health_status['checks']['storage'] = {
                    'status': 'unhealthy',
                    'message': 'Azure Blob Storage connection failed'
                }
                health_status['status'] = 'unhealthy'
        except Exception as e:
            health_status['checks']['storage'] = {
                'status': 'unhealthy',
                'message': f'Storage service error: {str(e)}'
            }
            health_status['status'] = 'unhealthy'
        
        # Check event publisher (Azure Storage Queues)
        try:
            from utils.event_publisher import get_event_publisher
            event_publisher = get_event_publisher()
            event_check = event_publisher.health_check()
            
            if event_check['status'] == 'healthy':
                health_status['checks']['event_publisher'] = {
                    'status': 'healthy',
                    'message': 'Event publishing service operational'
                }
            elif event_check['status'] == 'disabled':
                health_status['checks']['event_publisher'] = {
                    'status': 'disabled',
                    'message': event_check['reason']
                }
            else:
                health_status['checks']['event_publisher'] = {
                    'status': 'unhealthy',
                    'message': f"Event publishing failed: {event_check.get('error', 'Unknown error')}"
                }
                # Don't mark overall service as unhealthy for event publisher issues
                # since the service can operate without it
        except Exception as e:
            health_status['checks']['event_publisher'] = {
                'status': 'error',
                'message': f'Event publisher check failed: {str(e)}'
            }
        
        return health_status





