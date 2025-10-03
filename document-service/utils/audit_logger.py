"""
Audit logging utilities for external service interactions
Tracks all external updates and service-to-service communications
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID
from fastapi import Request

# Create dedicated audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Ensure audit logger doesn't propagate to root logger to avoid duplication
audit_logger.propagate = False

# Create console handler for audit logs if not already configured
if not audit_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s - AUDIT - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    audit_logger.addHandler(handler)


class AuditLogger:
    """Audit logging utility for external service interactions"""
    
    @staticmethod
    def log_external_update(
        action: str,
        resource_type: str,
        resource_id: str,
        user_id: Optional[str] = None,
        service_id: Optional[str] = None,
        changes: Optional[Dict[str, Any]] = None,
        request: Optional[Request] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """
        Log external service updates for audit trail
        
        Args:
            action: Action performed (create, update, delete, etc.)
            resource_type: Type of resource (document, metadata, etc.)
            resource_id: ID of the resource
            user_id: ID of the user making the request
            service_id: ID of the external service making the request
            changes: Dictionary of changes made
            request: FastAPI request object
            success: Whether the operation was successful
            error_message: Error message if operation failed
        """
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "success": success,
            "service": "document-service"
        }
        
        # Add user/service identification
        if user_id:
            audit_entry["user_id"] = user_id
        if service_id:
            audit_entry["service_id"] = service_id
        
        # Add request information
        if request:
            audit_entry["request"] = {
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
                "user_agent": request.headers.get("User-Agent"),
                "x_forwarded_for": request.headers.get("X-Forwarded-For")
            }
        
        # Add changes if provided
        if changes:
            audit_entry["changes"] = changes
        
        # Add error information if failed
        if not success and error_message:
            audit_entry["error"] = error_message
        
        # Log the audit entry
        audit_logger.info(json.dumps(audit_entry, default=str))
    
    @staticmethod
    def log_document_upload(
        document_id: UUID,
        user_id: UUID,
        filename: str,
        file_type: str,
        file_size: int,
        request: Optional[Request] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log document upload events"""
        changes = {
            "filename": filename,
            "file_type": file_type,
            "file_size": file_size
        }
        
        AuditLogger.log_external_update(
            action="upload",
            resource_type="document",
            resource_id=str(document_id),
            user_id=str(user_id),
            changes=changes,
            request=request,
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    def log_document_update(
        document_id: UUID,
        user_id: UUID,
        changes: Dict[str, Any],
        request: Optional[Request] = None,
        service_id: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log document metadata updates (typically from external services)"""
        AuditLogger.log_external_update(
            action="update",
            resource_type="document",
            resource_id=str(document_id),
            user_id=str(user_id),
            service_id=service_id,
            changes=changes,
            request=request,
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    def log_document_delete(
        document_id: UUID,
        user_id: UUID,
        request: Optional[Request] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log document deletion events"""
        AuditLogger.log_external_update(
            action="delete",
            resource_type="document",
            resource_id=str(document_id),
            user_id=str(user_id),
            request=request,
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    def log_bulk_upload(
        session_id: UUID,
        user_id: UUID,
        file_count: int,
        successful_uploads: int,
        failed_uploads: int,
        request: Optional[Request] = None
    ):
        """Log bulk upload operations"""
        changes = {
            "total_files": file_count,
            "successful": successful_uploads,
            "failed": failed_uploads
        }
        
        success = failed_uploads == 0
        error_message = f"{failed_uploads} files failed to upload" if failed_uploads > 0 else None
        
        AuditLogger.log_external_update(
            action="bulk_upload",
            resource_type="upload_session",
            resource_id=str(session_id),
            user_id=str(user_id),
            changes=changes,
            request=request,
            success=success,
            error_message=error_message
        )
    
    @staticmethod
    def log_external_service_call(
        service_name: str,
        action: str,
        resource_id: str,
        user_id: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Log calls to external services (AI, text extraction, etc.)"""
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": f"external_service_call",
            "external_service": service_name,
            "service_action": action,
            "resource_id": resource_id,
            "success": success,
            "service": "document-service"
        }
        
        if user_id:
            audit_entry["user_id"] = user_id
        
        if request_data:
            audit_entry["request_data"] = request_data
        
        if response_data:
            audit_entry["response_data"] = response_data
        
        if not success and error_message:
            audit_entry["error"] = error_message
        
        audit_logger.info(json.dumps(audit_entry, default=str))


# Convenience functions for common audit logging scenarios
def audit_document_upload(document_id: UUID, user_id: UUID, filename: str, file_type: str, file_size: int, request: Request = None, success: bool = True, error: str = None):
    """Convenience function for document upload audit logging"""
    AuditLogger.log_document_upload(document_id, user_id, filename, file_type, file_size, request, success, error)

def audit_document_update(document_id: UUID, user_id: UUID, changes: Dict[str, Any], request: Request = None, service_id: str = None, success: bool = True, error: str = None):
    """Convenience function for document update audit logging"""
    AuditLogger.log_document_update(document_id, user_id, changes, request, service_id, success, error)

def audit_document_delete(document_id: UUID, user_id: UUID, request: Request = None, success: bool = True, error: str = None):
    """Convenience function for document delete audit logging"""
    AuditLogger.log_document_delete(document_id, user_id, request, success, error)

