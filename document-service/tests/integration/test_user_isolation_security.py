"""
Integration tests for user isolation security
Tests that users cannot access each other's documents
"""

import pytest
import uuid
import io
from fastapi import status
from starlette.testclient import TestClient
from unittest.mock import patch


class TestUserIsolationSecurity:
    """Test user isolation and security"""

    @pytest.mark.integration
    def test_user_cannot_update_other_users_document(self, integration_client: TestClient, sample_pdf_file):
        """
        Test Case: Critical Security Issue - Cross-user document access
        
        Requirement: Users must NOT be able to access/modify other users' documents
        Expected: 404 NOT_FOUND when trying to access another user's document
        Actual Bug: 200 OK (security vulnerability!)
        """
        # Arrange - User1 uploads a document
        user1_id = str(uuid.uuid4())
        user1_headers = {"Authorization": f"Bearer mock-test-{user1_id}"}
        
        files = {
            "files": (
                sample_pdf_file["filename"],
                io.BytesIO(sample_pdf_file["content"]),
                sample_pdf_file["content_type"]
            )
        }
        
        upload_response = integration_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=user1_headers
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        document_id = upload_response.json()["data"]["results"][0]["document_id"]
        
        # Act - User2 tries to update User1's document (SECURITY TEST)
        user2_id = str(uuid.uuid4())
        user2_headers = {"Authorization": f"Bearer mock-test-{user2_id}"}
        update_data = {"file_type": "cv"}
        
        response = integration_client.put(
            f"/api/v1/documents/{document_id}",
            json=update_data,
            headers=user2_headers
        )
        
        # Assert - CRITICAL SECURITY CHECK
        # User2 should NOT be able to update User1's document
        assert response.status_code == status.HTTP_404_NOT_FOUND, f"SECURITY BUG: User2 got {response.status_code} instead of 404 when trying to update User1's document"
        
        response_data = response.json()
        assert response_data["success"] is False
        assert response_data["error"]["code"] == "DOCUMENT_NOT_FOUND"
    
    @pytest.mark.integration
    def test_user_cannot_get_other_users_document(self, integration_client: TestClient, sample_pdf_file):
        """
        Test Case: User cannot retrieve other users' documents
        """
        # Arrange - User1 uploads a document
        user1_id = str(uuid.uuid4())
        user1_headers = {"Authorization": f"Bearer mock-test-{user1_id}"}
        
        files = {
            "files": (
                sample_pdf_file["filename"],
                io.BytesIO(sample_pdf_file["content"]),
                sample_pdf_file["content_type"]
            )
        }
        
        upload_response = integration_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=user1_headers
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        document_id = upload_response.json()["data"]["results"][0]["document_id"]
        
        # Act - User2 tries to get User1's document (SECURITY TEST)
        user2_id = str(uuid.uuid4())
        user2_headers = {"Authorization": f"Bearer mock-test-{user2_id}"}
        
        response = integration_client.get(
            f"/api/v1/documents/{document_id}",
            headers=user2_headers
        )
        
        # Assert - CRITICAL SECURITY CHECK
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert response_data["success"] is False
        assert response_data["error"]["code"] == "DOCUMENT_NOT_FOUND"
    
    @pytest.mark.integration
    def test_user_cannot_delete_other_users_document(self, integration_client: TestClient, sample_pdf_file):
        """
        Test Case: User cannot delete other users' documents
        """
        # Arrange - User1 uploads a document
        user1_id = str(uuid.uuid4())
        user1_headers = {"Authorization": f"Bearer mock-test-{user1_id}"}
        
        files = {
            "files": (
                sample_pdf_file["filename"],
                io.BytesIO(sample_pdf_file["content"]),
                sample_pdf_file["content_type"]
            )
        }
        
        upload_response = integration_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=user1_headers
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        document_id = upload_response.json()["data"]["results"][0]["document_id"]
        
        # Act - User2 tries to delete User1's document (SECURITY TEST)
        user2_id = str(uuid.uuid4())
        user2_headers = {"Authorization": f"Bearer mock-test-{user2_id}"}
        
        response = integration_client.delete(
            f"/api/v1/documents/{document_id}",
            headers=user2_headers
        )
        
        # Assert - CRITICAL SECURITY CHECK
        assert response.status_code == status.HTTP_404_NOT_FOUND
        response_data = response.json()
        assert response_data["success"] is False
        assert response_data["error"]["code"] == "DOCUMENT_NOT_FOUND"
    
    @pytest.mark.integration
    def test_user_can_only_see_own_documents_in_list(self, integration_client: TestClient, sample_pdf_file):
        """
        Test Case: User document list should only show their own documents
        """
        # Arrange - User1 uploads a document
        user1_id = str(uuid.uuid4())
        user1_headers = {"Authorization": f"Bearer mock-test-{user1_id}"}
        
        files = {
            "files": (
                sample_pdf_file["filename"],
                io.BytesIO(sample_pdf_file["content"]),
                sample_pdf_file["content_type"]
            )
        }
        
        upload_response = integration_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=user1_headers
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        user1_document_id = upload_response.json()["data"]["results"][0]["document_id"]
        
        # User2 uploads a different document
        user2_id = str(uuid.uuid4())
        user2_headers = {"Authorization": f"Bearer mock-test-{user2_id}"}
        
        files = {
            "files": (
                "user2_document.pdf",
                io.BytesIO(sample_pdf_file["content"]),
                sample_pdf_file["content_type"]
            )
        }
        
        upload_response = integration_client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=user2_headers
        )
        
        assert upload_response.status_code == status.HTTP_201_CREATED
        user2_document_id = upload_response.json()["data"]["results"][0]["document_id"]
        
        # Act - User1 gets their document list
        user1_list_response = integration_client.get(
            "/api/v1/documents/",
            headers=user1_headers
        )
        
        # Assert - User1 should only see their own document
        assert user1_list_response.status_code == status.HTTP_200_OK
        user1_data = user1_list_response.json()
        assert user1_data["success"] is True
        
        # User1 should see exactly 1 document (their own)
        assert len(user1_data["data"]["documents"]) == 1
        assert user1_data["data"]["documents"][0]["id"] == user1_document_id
        
        # User2 should also only see their own document
        user2_list_response = integration_client.get(
            "/api/v1/documents/",
            headers=user2_headers
        )
        
        assert user2_list_response.status_code == status.HTTP_200_OK
        user2_data = user2_list_response.json()
        assert user2_data["success"] is True
        
        # User2 should see exactly 1 document (their own)
        assert len(user2_data["data"]["documents"]) == 1
        assert user2_data["data"]["documents"][0]["id"] == user2_document_id
        
        # Verify that users cannot see each other's documents
        assert user1_document_id != user2_document_id