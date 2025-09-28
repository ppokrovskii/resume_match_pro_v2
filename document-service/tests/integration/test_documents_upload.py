"""
Integration tests for POST /documents/upload endpoint

Tests the single upload endpoint that accepts arrays of 1-100 files.
Uses real testcontainers (no mocking) as per .cursorrules.

Requirements coverage:
- Single endpoint handles both single and multiple files
- Frontend sends single file as array: [file]  
- Maximum 100 files per upload
- File validation (PDF, DOC, DOCX, 16MB limit)
- Pure storage service (no text processing)
- Event publishing for external services
- Authentication required
- Proper error handling
"""

import pytest
import io
from fastapi import status


class TestDocumentsUpload:
    """Integration tests for document upload endpoint"""
    
    def test_upload_single_file_as_array(self, test_client, auth_headers, sample_pdf_file, mock_auth_user):
        """
        Test single file upload using array format
        Requirement: Frontend sends single file as array with one element
        """
        # Arrange - Single file as array
        files = [
            ("files", (sample_pdf_file["filename"], io.BytesIO(sample_pdf_file["content"]), sample_pdf_file["content_type"]))
        ]
        
        # Act
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["total_files"] == 1
        assert data["data"]["successful_uploads"] == 1
        assert data["data"]["failed_uploads"] == 0
        assert len(data["data"]["results"]) == 1
        
        result = data["data"]["results"][0]
        assert result["filename"] == sample_pdf_file["filename"]
        assert result["success"] is True
        assert "document_id" in result
        assert result["file_type"] is None  # Pure storage - no classification
        
    def test_upload_multiple_files(self, test_client, auth_headers, sample_pdf_file, mock_auth_user):
        """
        Test multiple files upload
        Requirement: Upload 1-100 files per session
        """
        # Arrange - Multiple files
        files = [
            ("files", ("resume1.pdf", io.BytesIO(sample_pdf_file["content"]), sample_pdf_file["content_type"])),
            ("files", ("resume2.pdf", io.BytesIO(sample_pdf_file["content"]), sample_pdf_file["content_type"])),
            ("files", ("resume3.pdf", io.BytesIO(sample_pdf_file["content"]), sample_pdf_file["content_type"]))
        ]
        
        # Act
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["total_files"] == 3
        assert data["data"]["successful_uploads"] == 3
        assert data["data"]["failed_uploads"] == 0
        assert len(data["data"]["results"]) == 3
        
        # All files should be successful
        for result in data["data"]["results"]:
            assert result["success"] is True
            assert "document_id" in result
            assert result["file_type"] is None
            
    def test_upload_file_limit_validation(self, test_client, auth_headers, sample_pdf_file):
        """
        Test file count limit validation
        Requirement: Maximum 100 files per upload
        """
        # Arrange - 101 files (exceeds limit)
        files = []
        for i in range(101):
            files.append(("files", (f"file_{i}.pdf", io.BytesIO(sample_pdf_file["content"]), sample_pdf_file["content_type"])))
        
        # Act
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        
        assert data["success"] is False
        assert data["error"]["code"] == "FILE_VALIDATION_ERROR"
        assert "maximum 100 files" in data["error"]["message"].lower()
        
    def test_upload_no_files_validation(self, test_client, auth_headers):
        """
        Test validation when no files provided
        Requirement: Clear error messages
        """
        # Act - No files
        response = test_client.post(
            "/api/v1/documents/upload",
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        
    def test_upload_file_type_validation(self, test_client, auth_headers, mock_auth_user):
        """
        Test file type validation
        Requirement: Only PDF, DOC, DOCX files accepted
        """
        # Arrange - Unsupported file type
        text_content = b"This is a text file content. " * 10  # Large enough
        files = [
            ("files", ("document.txt", io.BytesIO(text_content), "text/plain"))
        ]
        
        # Act
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        # Should succeed but with validation failure in results
        assert data["success"] is True
        assert data["data"]["total_files"] == 1
        assert data["data"]["failed_uploads"] == 1
        assert data["data"]["successful_uploads"] == 0
        
        result = data["data"]["results"][0]
        assert result["success"] is False
        assert "error" in result
        
    def test_upload_mixed_valid_invalid_files(self, test_client, auth_headers, sample_pdf_file, mock_auth_user):
        """
        Test upload with mix of valid and invalid files
        Requirement: Individual success/failure status
        """
        # Arrange - Mix of valid and invalid files
        text_content = b"This is a text file content. " * 10
        files = [
            ("files", ("valid.pdf", io.BytesIO(sample_pdf_file["content"]), sample_pdf_file["content_type"])),
            ("files", ("invalid.txt", io.BytesIO(text_content), "text/plain"))
        ]
        
        # Act
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        assert data["success"] is True
        assert data["data"]["total_files"] == 2
        assert data["data"]["successful_uploads"] == 1
        assert data["data"]["failed_uploads"] == 1
        
    def test_upload_authentication_required(self, test_client, sample_pdf_file):
        """
        Test authentication requirement
        Requirement: User must be authenticated
        """
        # Arrange
        files = [
            ("files", (sample_pdf_file["filename"], io.BytesIO(sample_pdf_file["content"]), sample_pdf_file["content_type"]))
        ]
        
        # Act - No authentication
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files
        )
        
        # Assert
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
    def test_upload_special_characters_filename(self, test_client, auth_headers, sample_pdf_file, mock_auth_user):
        """
        Test upload with special characters in filename
        Requirement: Secure filename handling
        """
        # Arrange - Filename with special characters
        special_filename = "résumé_测试_файл.pdf"
        files = [
            ("files", (special_filename, io.BytesIO(sample_pdf_file["content"]), sample_pdf_file["content_type"]))
        ]
        
        # Act
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        result = data["data"]["results"][0]
        assert result["filename"] == special_filename
        assert result["success"] is True
        
    def test_upload_pure_storage_no_processing(self, test_client, auth_headers, sample_pdf_file, mock_auth_user):
        """
        Test that files are stored as-is without processing
        Requirement: Pure storage service - no text processing
        """
        # Arrange
        files = [
            ("files", (sample_pdf_file["filename"], io.BytesIO(sample_pdf_file["content"]), sample_pdf_file["content_type"]))
        ]
        
        # Act
        response = test_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers
        )
        
        # Assert
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        
        result = data["data"]["results"][0]
        
        # Verify no processing occurred
        assert result["file_type"] is None  # No automatic classification
        assert result["file_size"] == len(sample_pdf_file["content"])  # Original size preserved
        assert result["content_type"] == sample_pdf_file["content_type"]  # Original content type
        assert result["filename"] == sample_pdf_file["filename"]  # Original filename
        
    def test_upload_concurrent_requests(self, test_client, auth_headers, sample_pdf_file, mock_auth_user):
        """
        Test handling of concurrent upload requests
        Requirement: System should handle multiple simultaneous uploads
        """
        import threading
        
        results = []
        
        def upload_file(file_suffix):
            files = [
                ("files", (f"concurrent_{file_suffix}.pdf", io.BytesIO(sample_pdf_file["content"]), sample_pdf_file["content_type"]))
            ]
            
            response = test_client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers
            )
            results.append(response.status_code)
        
        # Act - Start multiple concurrent uploads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=upload_file, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all uploads to complete
        for thread in threads:
            thread.join()
        
        # Assert - All uploads should succeed
        assert len(results) == 3
        assert all(status_code == 201 for status_code in results)
