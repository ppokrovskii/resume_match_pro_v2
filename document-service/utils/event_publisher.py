"""
Event publishing utilities for Azure Storage Queues
Publishes document lifecycle events for external microservices
"""

import logging
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from uuid import UUID

try:
    from azure.storage.queue import QueueServiceClient
except ImportError:
    QueueServiceClient = None

logger = logging.getLogger(__name__)


class EventPublisher:
    """Azure Storage Queue event publisher for document lifecycle events"""
    
    def __init__(self):
        self.connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.queue_name = os.getenv('AZURE_STORAGE_QUEUE_NAME', 'document-events')
        self.enabled = bool(self.connection_string and QueueServiceClient)
        
        if not self.enabled:
            logger.warning("Event publishing disabled: Azure Storage not configured or azure-storage-queue not installed")
        else:
            logger.info(f"Event publisher initialized for queue: {self.queue_name}")
            self._ensure_queue_exists()
    
    def publish_document_uploaded(self, document_id: UUID, content_type: Optional[str] = None) -> bool:
        """
        Publish document.uploaded event for text extraction service
        
        Args:
            document_id: UUID of the uploaded document
            content_type: MIME type of the document (optional)
            
        Returns:
            bool: True if event was published successfully
        """
        event_data = {
            "event_type": "document.uploaded",
            "document_id": str(document_id),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Add optional content_type if provided
        if content_type:
            event_data["content_type"] = content_type
        
        return self._publish_event(event_data, "document.uploaded")
    
    def publish_document_updated(self, document: Dict[str, Any]) -> bool:
        """
        Publish document.updated event for AI matching service
        
        Args:
            document: Complete document object with updated metadata
            
        Returns:
            bool: True if event was published successfully
        """
        # Convert UUIDs to strings for JSON serialization
        serializable_document = self._make_json_serializable(document)
        
        event_data = {
            "event_type": "document.updated",
            "document": serializable_document,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return self._publish_event(event_data, "document.updated")
    
    def publish_document_deleted(self, document_id: UUID, user_id: UUID) -> bool:
        """
        Publish document.deleted event for cleanup services
        
        Args:
            document_id: UUID of the deleted document
            user_id: UUID of the user who deleted the document
            
        Returns:
            bool: True if event was published successfully
        """
        event_data = {
            "event_type": "document.deleted",
            "document_id": str(document_id),
            "user_id": str(user_id),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return self._publish_event(event_data, "document.deleted")
    
    def _ensure_queue_exists(self):
        """Ensure the queue exists (create if it doesn't)"""
        try:
            queue_service = QueueServiceClient.from_connection_string(self.connection_string)
            queue_service.create_queue(self.queue_name)
            logger.debug(f"Queue '{self.queue_name}' ensured to exist")
        except Exception as e:
            # Queue might already exist, which is fine
            logger.debug(f"Queue creation result: {e}")
    
    def _make_json_serializable(self, obj: Any) -> Any:
        """Convert objects to JSON serializable format"""
        if isinstance(obj, UUID):
            return str(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        else:
            return obj
    
    def _publish_event(self, event_data: Dict[str, Any], event_type: str) -> bool:
        """
        Internal method to publish event to Azure Storage Queue
        
        Args:
            event_data: Event payload
            event_type: Type of event for message properties
            
        Returns:
            bool: True if published successfully
        """
        if not self.enabled:
            logger.debug(f"Event publishing disabled, would publish: {event_type}")
            return True  # Return True for testing/development
        
        try:
            queue_service = QueueServiceClient.from_connection_string(self.connection_string)
            queue_client = queue_service.get_queue_client(self.queue_name)
            
            # Create message with event data and metadata
            message_data = {
                "event_type": event_type,
                "service": "document-service",
                "version": "1.0",
                "timestamp": event_data.get("timestamp", datetime.utcnow().isoformat()),
                "data": event_data
            }
            
            message_body = json.dumps(message_data)
            
            # Send the message to queue
            queue_client.send_message(message_body)
            logger.info(f"Published event: {event_type} for document {event_data.get('document_id')}")
            return True
                    
        except Exception as e:
            logger.error(f"Failed to publish event {event_type}: {e}")
            return False
    
    def health_check(self) -> Dict[str, Any]:
        """
        Check if event publishing is healthy
        
        Returns:
            dict: Health status information
        """
        if not self.enabled:
            return {
                "status": "disabled",
                "reason": "Azure Storage not configured or library not installed"
            }
        
        try:
            # Try to create a client to test connectivity
            queue_service = QueueServiceClient.from_connection_string(self.connection_string)
            # Test by getting queue properties
            queue_client = queue_service.get_queue_client(self.queue_name)
            queue_client.get_queue_properties()
            
            return {
                "status": "healthy",
                "queue": self.queue_name,
                "connection": "ok"
            }
                
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "queue": self.queue_name
            }


# Global event publisher instance
_event_publisher: Optional[EventPublisher] = None


def get_event_publisher() -> EventPublisher:
    """Get global event publisher instance"""
    global _event_publisher
    if not _event_publisher:
        _event_publisher = EventPublisher()
    return _event_publisher


def publish_document_uploaded(document_id: UUID, content_type: Optional[str] = None) -> bool:
    """Convenience function to publish document uploaded event"""
    return get_event_publisher().publish_document_uploaded(document_id, content_type)


def publish_document_updated(document: Dict[str, Any]) -> bool:
    """Convenience function to publish document updated event"""
    return get_event_publisher().publish_document_updated(document)


def publish_document_deleted(document_id: UUID, user_id: UUID) -> bool:
    """Convenience function to publish document deleted event"""
    return get_event_publisher().publish_document_deleted(document_id, user_id)
