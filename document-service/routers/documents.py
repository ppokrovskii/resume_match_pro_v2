"""
Document management routes for FastAPI
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from uuid import UUID
from typing import List, Optional, Union
from pydantic import BaseModel, Field
from io import BytesIO

from models.document import Document, DocumentListResponse, DocumentSearchRequest, DocumentSearchResponse, DocumentUploadResponse, BulkUploadResponse, DocumentUpdateRequest, DocumentUpdateResponse
from services.document_service import DocumentService
from utils.file_validators import validate_upload_file, FileValidationError
from utils.fastapi_error_handler import DatabaseError, FileNotFoundError as ServiceFileNotFoundError, DocumentServiceError
from middleware.auth0_middleware import get_current_user_id, get_current_org_id, require_scope

logger = logging.getLogger(__name__)
router = APIRouter()

# Pydantic response models
class DocumentResponse(BaseModel):
    success: bool
    data: Document
    meta: dict

class DocumentListResponseModel(BaseModel):
    success: bool = Field(..., description="Indicates if the request was successful", example=True)
    data: DocumentListResponse = Field(..., description="Document list data")
    meta: dict = Field(
        ..., 
        description="Metadata about the request",
        example={
            "service": "document-service",
            "endpoint": "documents.get_documents",
            "method": "GET"
        }
    )

class DocumentSearchResponseModel(BaseModel):
    success: bool
    data: DocumentSearchResponse
    meta: dict

class DeleteResponse(BaseModel):
    success: bool
    data: dict
    meta: dict

class UploadResponse(BaseModel):
    success: bool
    data: DocumentUploadResponse
    meta: dict

class BulkUploadResponseModel(BaseModel):
    success: bool
    data: BulkUploadResponse
    meta: dict


def get_document_service():
    """Lazy initialization of document service"""
    if not hasattr(get_document_service, '_service'):
        get_document_service._service = DocumentService()
    return get_document_service._service


@router.get("/", response_model=DocumentListResponseModel, summary="List User Documents")
async def get_documents(
    file_type: Optional[str] = Query(
        None, 
        description="Filter by document type. Omit to return all document types.",
        examples={
            "cv": {
                "summary": "CV/Resume documents only",
                "value": "cv"
            },
            "jd": {
                "summary": "Job description documents only", 
                "value": "jd"
            },
            "all": {
                "summary": "All document types (default)",
                "description": "Omit this parameter to get all document types"
            }
        },
        pattern="^(cv|jd)$"
    ),
    limit: int = Query(
        50, 
        ge=1, 
        le=100, 
        description="Maximum number of documents to return per page",
        example=10
    ),
    offset: int = Query(
        0, 
        ge=0, 
        description="Number of documents to skip for pagination",
        example=0
    ),
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Retrieve a paginated list of documents for the authenticated user.
    
    This endpoint returns documents owned by the current user with support for:
    - **Filtering** by document type (CV or Job Description)
    - **Pagination** with customizable limit and offset
    - **Ordering** by creation date (newest first)
    
    ## Parameters
    
    - **file_type** (optional): Filter documents by type
        - `cv` - Return only Resume/CV documents
        - `jd` - Return only Job description documents
        - *omitted* - Return all document types (default behavior)
    
    - **limit**: Number of documents per page (1-100, default: 50)
    
    - **offset**: Skip this many documents for pagination (default: 0)
    
    ## Response
    
    Returns a structured response with:
    - **documents**: Array of document objects with metadata
    - **total_count**: Total number of documents matching the filter
    - **pagination info**: limit, offset, has_more flags
    
    ## Examples
    
    - Get all documents: `GET /documents`
    - Get only CV documents: `GET /documents?file_type=cv`
    - Get only job descriptions: `GET /documents?file_type=jd`
    - Get first 10 CV documents: `GET /documents?file_type=cv&limit=10`
    - Get next page of all documents: `GET /documents?limit=10&offset=10`
    
    ## Security
    
    - Requires authentication (JWT token)
    - Users can only access their own documents
    - Results are automatically filtered by user ownership
    """
    try:
        # Note: file_type validation is now handled by Pydantic pattern validation
        
        document_service = get_document_service()
        documents, total_count = document_service.get_user_documents(
            user_id=user_id,
            file_type=file_type.lower() if file_type else None,
            limit=limit,
            offset=offset
        )
        
        return DocumentListResponseModel(
            success=True,
            data=DocumentListResponse(
                documents=documents,
                total_count=total_count,
                limit=limit,
                offset=offset,
                has_more=offset + len(documents) < total_count
            ),
            meta={
                "service": "document-service",
                "endpoint": "documents.get_documents",
                "method": "GET"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get documents: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "DOCUMENTS_FETCH_FAILED",
                    "message": "Failed to retrieve documents"
                },
                "meta": {
                    "service": "document-service",
                    "endpoint": "documents.get_documents",
                    "method": "GET"
                }
            }
        )


@router.get("/{document_id}", response_model=DocumentResponse, summary="Get Document")
async def get_document(
    document_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Get a specific document by ID
    
    - **document_id**: UUID of the document to retrieve
    
    Returns complete document information including extracted text.
    """
    try:
        document_service = get_document_service()
        document = document_service.get_document(document_id, user_id)
        
        if not document:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": {
                        "code": "DOCUMENT_NOT_FOUND",
                        "message": f"Document {document_id} not found"
                    }
                }
            )
        
        return DocumentResponse(
            success=True,
            data=document,
            meta={
                "service": "document-service",
                "endpoint": "documents.get_document",
                "method": "GET"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "DOCUMENT_FETCH_FAILED",
                    "message": "Failed to retrieve document"
                },
                "meta": {
                    "service": "document-service",
                    "endpoint": "documents.get_document",
                    "method": "GET"
                }
            }
        )


@router.get(
    "/{document_id}/download", 
    summary="Download Document File",
    description="Download the original document file as uploaded by the user",
    responses={
        200: {
            "description": "Document file downloaded successfully",
            "content": {
                "application/pdf": {
                    "example": "Binary PDF content"
                },
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
                    "example": "Binary DOCX content"
                },
                "application/msword": {
                    "example": "Binary DOC content"
                }
            },
            "headers": {
                "Content-Disposition": {
                    "description": "Attachment with original filename",
                    "schema": {"type": "string"},
                    "example": "attachment; filename=resume.pdf"
                }
            }
        },
        401: {
            "description": "Authentication required",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Not authenticated"
                    }
                }
            }
        },
        404: {
            "description": "Document not found or access denied",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "DOCUMENT_NOT_FOUND",
                            "message": "Document not found"
                        }
                    }
                }
            }
        },
        500: {
            "description": "Internal server error during download",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": {
                            "code": "DOWNLOAD_FAILED",
                            "message": "Failed to download document"
                        }
                    }
                }
            }
        }
    },
    tags=["Documents"]
)
async def download_document(
    document_id: UUID,
    user_id: UUID = Depends(get_current_user_id)
):
    """
    Download the original document file exactly as uploaded
    
    This endpoint allows users to download their uploaded documents in their original format.
    The file is returned as a streaming response with appropriate content-type headers.
    
    **Security:**
    - Requires valid JWT authentication
    - Users can only download their own documents
    - Document access is isolated by user_id
    
    **Supported File Types:**
    - PDF (.pdf) - application/pdf
    - Microsoft Word (.docx) - application/vnd.openxmlformats-officedocument.wordprocessingml.document  
    - Microsoft Word Legacy (.doc) - application/msword
    
    **Performance:**
    - Files up to 16MB are supported
    - Download starts within 1 second (performance requirement)
    - Files are immediately available after upload
    
    **Parameters:**
    - **document_id**: UUID of the document to download (path parameter)
    
    **Returns:**
    - Binary file content with appropriate Content-Type header
    - Content-Disposition header with original filename
    - Streaming response for efficient large file handling
    
    **Error Handling:**
    - 404: Document not found or user doesn't have access
    - 401: Authentication required or invalid token
    - 500: Storage service error or internal server error
    """
    try:
        document_service = get_document_service()
        file_data, content_type, filename = document_service.download_document(document_id, user_id)
        
        # Create streaming response
        file_stream = BytesIO(file_data)
        
        return StreamingResponse(
            file_stream,
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to download document {document_id}: {e}", exc_info=True)
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": {
                        "code": "DOCUMENT_NOT_FOUND",
                        "message": "Document not found"
                    }
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail={
                    "success": False,
                    "error": {
                        "code": "DOWNLOAD_FAILED",
                        "message": "Failed to download document"
                    }
                }
            )


@router.delete("/{document_id}", status_code=204, summary="Delete Document")
async def delete_document(
    document_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    org_id: Optional[str] = Depends(get_current_org_id),
    _scope: None = Depends(require_scope("delete:documents"))
):
    """
    Delete a document and its associated file
    
    - **document_id**: UUID of the document to delete
    
    Permanently removes the document record and file from storage.
    Returns 204 No Content on successful deletion.
    """
    try:
        document_service = get_document_service()
        success = document_service.delete_document(document_id, user_id)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": {
                        "code": "DOCUMENT_NOT_FOUND",
                        "message": f"Document {document_id} not found"
                    },
                    "meta": {
                        "service": "document-service",
                        "endpoint": "documents.delete_document",
                        "method": "DELETE"
                    }
                }
            )
        
        # Return 204 No Content for successful deletion (REST standard)
        return None
        
    except HTTPException:
        raise
    except (FileNotFoundError, DatabaseError):
        # Handle document not found specifically
        # DatabaseError from get_document() typically means document doesn't exist
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {
                    "code": "DOCUMENT_NOT_FOUND",
                    "message": f"Document {document_id} not found"
                },
                "meta": {
                "service": "document-service",
                "endpoint": "documents.delete_document",
                "method": "DELETE"
                }
            }
        )
    except Exception as e:
        logger.error(f"Failed to delete document {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "DELETE_FAILED",
                    "message": "Failed to delete document"
                },
                "meta": {
                    "service": "document-service",
                    "endpoint": "documents.delete_document",
                    "method": "DELETE"
                }
            }
        )


@router.put("/{document_id}", response_model=DocumentUpdateResponse, summary="Update Document Metadata")
async def update_document_metadata(
    document_id: UUID,
    update_request: DocumentUpdateRequest,
    user_id: UUID = Depends(get_current_user_id),
    org_id: Optional[str] = Depends(get_current_org_id),
    _scope: None = Depends(require_scope("write:documents"))
):
    """
    Update document metadata (for external services)
    
    This endpoint allows external AI services to update document metadata after processing.
    It supports updating the following fields:
    
    - **file_type**: Document classification (cv or jd)
    - **text_content**: Extracted text content from the document
    - **role**: Identified job role or position (e.g., "Python Developer")
    - **features**: List of extracted features (skills, certifications, etc.)
    - **metadata**: Additional metadata fields
    
    ## Request Body
    
    All fields are optional - only provide the fields you want to update:
    
    ```json
    {
        "file_type": "cv",
        "text_content": "John Doe\\nSoftware Engineer\\n...",
        "role": "Python Developer",
        "features": [
            {
                "name": "Python",
                "type": "skill",
                "properties": {"years": 5, "level": "expert"}
            },
            {
                "name": "AWS Solutions Architect",
                "type": "certification",
                "properties": {"grade": "A", "year_obtained": 2023}
            }
        ],
        "metadata": {
            "processing_version": "1.2.0",
            "confidence_score": 0.95
        }
    }
    ```
    
    ## Features Structure
    
    Features support flexible NoSQL structure with:
    - **name**: Feature/skill name
    - **type**: Feature type (skill, certification, language, tool, etc.)
    - **properties**: Flexible key-value properties specific to the feature type
    
    ## Authentication
    
    - Requires valid JWT token
    - Only authorized external services can update documents
    - Users can only update their own documents
    
    ## Events
    
    - Publishes `document.updated` event to Azure Service Bus after successful update
    - Event contains complete updated document data for AI matching service
    
    ## Response
    
    Returns success status and updated document ID on successful update.
    """
    try:
        document_service = get_document_service()
        
        # Convert request to dictionary, excluding None values
        update_data = update_request.model_dump(exclude_none=True)
        
        if not update_data:
            raise HTTPException(
                status_code=400,
                detail={
                    "success": False,
                    "error": {
                        "code": "EMPTY_UPDATE_REQUEST",
                        "message": "At least one field must be provided for update"
                    },
                    "meta": {
                        "service": "document-service",
                        "endpoint": "documents.update_document_metadata",
                        "method": "PUT"
                    }
                }
            )
        
        success = document_service.update_document_metadata(document_id, user_id, update_data)
        
        if not success:
            raise HTTPException(
                status_code=404,
                detail={
                    "success": False,
                    "error": {
                        "code": "DOCUMENT_NOT_FOUND",
                        "message": f"Document {document_id} not found"
                    },
                    "meta": {
                        "service": "document-service",
                        "endpoint": "documents.update_document_metadata",
                        "method": "PUT"
                    }
                }
            )
        
        return DocumentUpdateResponse(
            success=True,
            data={
                "updated": True,
                "document_id": str(document_id),
                "updated_fields": list(update_data.keys())
            },
            meta={
                "service": "document-service",
                "endpoint": "documents.update_document_metadata",
                "method": "PUT"
            }
        )
        
    except HTTPException:
        raise
    except FileNotFoundError:
        # Handle document not found specifically
        raise HTTPException(
            status_code=404,
            detail={
                "success": False,
                "error": {
                    "code": "DOCUMENT_NOT_FOUND",
                    "message": f"Document {document_id} not found"
                },
                "meta": {
                    "service": "document-service",
                    "endpoint": "documents.update_document_metadata",
                    "method": "PUT"
                }
            }
        )
    except Exception as e:
        logger.error(f"Failed to update document metadata {document_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "UPDATE_FAILED",
                    "message": "Failed to update document metadata"
                },
                "meta": {
                    "service": "document-service",
                    "endpoint": "documents.update_document_metadata",
                    "method": "PUT"
                }
            }
        )


@router.post("/upload", response_model=BulkUploadResponseModel, status_code=201, summary="Upload Documents")
async def upload_documents(
    files: List[UploadFile] = File(..., description="Document files to upload (1-100 files)"),
    user_id: UUID = Depends(get_current_user_id),
    org_id: Optional[str] = Depends(get_current_org_id),
    _scope: None = Depends(require_scope("write:documents"))
):
    """
    Upload documents (single or multiple files)
    
    - **files**: Array of document files (PDF, DOC, DOCX) - 1 to 100 files, up to 16MB each
    
    Pure storage service - files are stored as-is without processing.
    Publishes document.uploaded event for external text extraction service.
    
    Frontend can send single file as array with one element: [file]
    """
    try:
        # Basic validation - keep router thin
        if len(files) > 100:
            raise HTTPException(status_code=400, detail={
                "success": False,
                "error": {"code": "FILE_VALIDATION_ERROR", "message": "Maximum 100 files allowed per upload"}
            })
        
        if len(files) == 0:
            raise HTTPException(status_code=400, detail={
                    "success": False,
                "error": {"code": "FILE_VALIDATION_ERROR", "message": "No files provided"}
            })
        
        # Delegate to service layer
        document_service = get_document_service()
        result = await document_service.upload_multiple_documents(files, user_id)
        
        return BulkUploadResponseModel(
            success=True,
            data=result,
            meta={
                "service": "document-service",
                "endpoint": "documents.upload_documents", 
                "method": "POST"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "success": False,
                "error": {
                    "code": "UPLOAD_FAILED",
                    "message": "Failed to upload documents"
                }
            }
        )
