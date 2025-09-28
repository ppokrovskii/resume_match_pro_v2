"""
Storage service for file operations using Azure Blob Storage
"""

import logging
import os
from typing import Optional, Tuple
from uuid import uuid4
from datetime import datetime, timedelta
from io import BytesIO

from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from azure.core.exceptions import ResourceNotFoundError, AzureError
from azure.storage.blob import generate_blob_sas, BlobSasPermissions

from utils.fastapi_error_handler import StorageError

logger = logging.getLogger(__name__)


class StorageService:
    """Azure Blob Storage service for document files"""
    
    def __init__(
        self,
        connection_string: str = None,
        container_name: str = None
    ):
        self.connection_string = connection_string or os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.container_name = container_name or os.getenv('AZURE_STORAGE_CONTAINER', 'documents')
        
        if not self.connection_string:
            # Try account name and key approach
            account_name = os.getenv('AZURE_STORAGE_ACCOUNT_NAME')
            account_key = os.getenv('AZURE_STORAGE_ACCOUNT_KEY')
            
            if account_name and account_key:
                self.connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
            else:
                raise StorageError("Azure Storage credentials not configured. Set AZURE_STORAGE_CONNECTION_STRING or AZURE_STORAGE_ACCOUNT_NAME/AZURE_STORAGE_ACCOUNT_KEY")
        
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string)
            self._ensure_container_exists()
            logger.info(f"Storage service initialized: {self.container_name}")
        except Exception as e:
            logger.error(f"Failed to initialize storage service: {e}")
            raise StorageError(f"Storage service initialization failed: {str(e)}")
    
    def _ensure_container_exists(self) -> None:
        """Ensure the container exists, create if it doesn't"""
        try:
            container_client = self.blob_service_client.get_container_client(self.container_name)
            if not container_client.exists():
                container_client.create_container()
                logger.info(f"Created container: {self.container_name}")
        except Exception as e:
            logger.error(f"Failed to ensure container exists: {e}")
            raise StorageError(f"Container creation failed: {str(e)}")
    
    def _generate_blob_path(self, user_id: str, filename: str, file_type: str) -> str:
        """Generate unique blob path for file storage"""
        # Create path: user_id/file_type/year/month/uuid_filename
        now = datetime.utcnow()
        unique_id = str(uuid4())
        safe_filename = filename.replace(' ', '_').replace('/', '_')
        
        return f"{user_id}/{file_type}/{now.year}/{now.month:02d}/{unique_id}_{safe_filename}"
    
    def upload_file(
        self, 
        file_data: bytes, 
        filename: str, 
        content_type: str,
        user_id: str,
        file_type: str
    ) -> str:
        """
        Upload file to storage and return storage path
        """
        try:
            blob_path = self._generate_blob_path(user_id, filename, file_type)
            
            # Get blob client
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )
            
            # Upload file with metadata
            metadata = {
                'original_filename': filename,
                'user_id': user_id,
                'file_type': file_type,
                'upload_timestamp': datetime.utcnow().isoformat()
            }
            
            blob_client.upload_blob(
                data=file_data,
                content_type=content_type,
                metadata=metadata,
                overwrite=True
            )
            
            logger.info(f"File uploaded successfully: {blob_path}")
            return blob_path
            
        except AzureError as e:
            logger.error(f"Azure error during upload: {e}")
            raise StorageError(f"File upload failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during upload: {e}")
            raise StorageError(f"File upload failed: {str(e)}")
    
    def download_file(self, storage_path: str) -> Tuple[bytes, str]:
        """
        Download file from storage and return (file_data, content_type)
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=storage_path
            )
            
            # Download blob
            blob_data = blob_client.download_blob()
            file_data = blob_data.readall()
            
            # Get properties for content type
            properties = blob_client.get_blob_properties()
            content_type = properties.content_settings.content_type or 'application/octet-stream'
            
            logger.info(f"File downloaded successfully: {storage_path}")
            return file_data, content_type
            
        except ResourceNotFoundError:
            logger.warning(f"File not found: {storage_path}")
            raise StorageError("File not found", "FILE_NOT_FOUND", 404)
        except AzureError as e:
            logger.error(f"Azure error during download: {e}")
            raise StorageError(f"File download failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            raise StorageError(f"File download failed: {str(e)}")
    
    def delete_file(self, storage_path: str) -> bool:
        """Delete file from storage"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=storage_path
            )
            
            blob_client.delete_blob()
            logger.info(f"File deleted successfully: {storage_path}")
            return True
            
        except ResourceNotFoundError:
            logger.warning(f"File not found for deletion: {storage_path}")
            return False
        except AzureError as e:
            logger.error(f"Azure error during deletion: {e}")
            raise StorageError(f"File deletion failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during deletion: {e}")
            raise StorageError(f"File deletion failed: {str(e)}")
    
    def get_download_url(self, storage_path: str, expires_in_hours: int = 1) -> str:
        """Generate pre-signed download URL"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=storage_path
            )
            
            # Generate SAS token
            sas_token = generate_blob_sas(
                account_name=blob_client.account_name,
                container_name=self.container_name,
                blob_name=storage_path,
                account_key=self._get_account_key(),
                permission=BlobSasPermissions(read=True),
                expiry=datetime.utcnow() + timedelta(hours=expires_in_hours)
            )
            
            # Construct URL with SAS token
            url = f"{blob_client.url}?{sas_token}"
            
            logger.info(f"Generated download URL for: {storage_path}")
            return url
            
        except AzureError as e:
            logger.error(f"Azure error generating download URL: {e}")
            raise StorageError(f"Failed to generate download URL: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error generating download URL: {e}")
            raise StorageError(f"Failed to generate download URL: {str(e)}")
    
    def get_upload_url(
        self, 
        blob_path: str, 
        content_type: str,
        expires_in_hours: int = 1
    ) -> str:
        """Generate pre-signed upload URL"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_path
            )
            
            # Generate SAS token for upload
            sas_token = generate_blob_sas(
                account_name=blob_client.account_name,
                container_name=self.container_name,
                blob_name=blob_path,
                account_key=self._get_account_key(),
                permission=BlobSasPermissions(write=True, create=True),
                expiry=datetime.utcnow() + timedelta(hours=expires_in_hours)
            )
            
            # Construct URL with SAS token
            url = f"{blob_client.url}?{sas_token}"
            
            logger.info(f"Generated upload URL for: {blob_path}")
            return url
            
        except AzureError as e:
            logger.error(f"Azure error generating upload URL: {e}")
            raise StorageError(f"Failed to generate upload URL: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error generating upload URL: {e}")
            raise StorageError(f"Failed to generate upload URL: {str(e)}")
    
    def get_file_info(self, storage_path: str) -> Optional[dict]:
        """Get file metadata"""
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=storage_path
            )
            
            properties = blob_client.get_blob_properties()
            return {
                'size': properties.size,
                'content_type': properties.content_settings.content_type,
                'last_modified': properties.last_modified,
                'etag': properties.etag,
                'metadata': properties.metadata
            }
        except ResourceNotFoundError:
            return None
        except AzureError as e:
            logger.error(f"Azure error getting file info: {e}")
            raise StorageError(f"Failed to get file info: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error getting file info: {e}")
            raise StorageError(f"Failed to get file info: {str(e)}")
    
    def health_check(self) -> bool:
        """Check if storage service is healthy"""
        try:
            # Try to get container properties as a health check
            container_client = self.blob_service_client.get_container_client(self.container_name)
            container_client.get_container_properties()
            return True
        except Exception as e:
            logger.error(f"Storage health check failed: {e}")
            return False
    
    def _get_account_key(self) -> str:
        """Extract account key from connection string"""
        try:
            # Parse connection string to get account key
            parts = self.connection_string.split(';')
            for part in parts:
                if part.startswith('AccountKey='):
                    return part.split('=', 1)[1]
            raise ValueError("AccountKey not found in connection string")
        except Exception as e:
            logger.error(f"Failed to extract account key: {e}")
            raise StorageError("Failed to extract account key for SAS generation")


# Global storage service instance
storage_service: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get storage service instance"""
    global storage_service
    if not storage_service:
        storage_service = StorageService()
    return storage_service

