"""
End-to-end tests for document upload workflow

These tests run against a real running application instance
and test complete user journeys as specified in test_plan.md
"""

import pytest
import requests
import io
import time
from typing import Dict, Any


@pytest.mark.e2e
@pytest.mark.smoke
class TestDocumentUploadWorkflow:
    """E2E tests for document upload workflow"""
    
    def test_complete_document_upload_flow(self, e2e_config, test_auth_token):
        """
        Test Case: E2E-JOURNEY-001 - Complete Document Upload Flow
        
        1. Authenticate user → GET /health (verify service)
        2. Upload CV document → POST /api/v1/upload
        3. Verify document in list → GET /api/v1/documents
        4. Download document → GET /api/v1/documents/{id}/download
        5. Delete document → DELETE /api/v1/documents/{id}
        """
        base_url = e2e_config.base_url
        headers = {
            "Authorization": f"Bearer {test_auth_token}",
            "Content-Type": "application/json"
        }
        
        # Step 1: Verify service health
        health_response = requests.get(f"{base_url}/health", timeout=30)
        assert health_response.status_code == 200
        
        # Step 2: Upload CV document
        sample_pdf = self._create_sample_pdf()
        files = {
            "files": ("test_cv.pdf", io.BytesIO(sample_pdf), "application/pdf")
        }
        
        upload_response = requests.post(
            f"{base_url}/api/v1/documents/upload",
            files=files,
            headers={"Authorization": f"Bearer {test_auth_token}"},
            timeout=30
        )
        
        assert upload_response.status_code == 201
        upload_data = upload_response.json()
        assert upload_data["success"] is True
        
        document_id = upload_data["data"]["id"]
        assert document_id is not None
        
        # Step 3: Verify document in list
        list_response = requests.get(
            f"{base_url}/api/v1/documents",
            headers=headers,
            timeout=30
        )
        
        assert list_response.status_code == 200
        list_data = list_response.json()
        
        # Find our uploaded document
        uploaded_doc = None
        for doc in list_data["data"]["documents"]:
            if doc["id"] == document_id:
                uploaded_doc = doc
                break
        
        assert uploaded_doc is not None
        assert uploaded_doc["filename"] == "test_cv.pdf"
        
        # Step 4: Download document
        download_response = requests.get(
            f"{base_url}/api/v1/documents/{document_id}/download",
            headers={"Authorization": f"Bearer {test_auth_token}"},
            timeout=30
        )
        
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "application/pdf"
        
        # Step 5: Delete document
        delete_response = requests.delete(
            f"{base_url}/api/v1/documents/{document_id}",
            headers={"Authorization": f"Bearer {test_auth_token}"},
            timeout=30
        )
        
        assert delete_response.status_code == 204
        
        # Verify document is deleted
        get_response = requests.get(
            f"{base_url}/api/v1/documents/{document_id}",
            headers={"Authorization": f"Bearer {test_auth_token}"},
            timeout=30
        )
        
        assert get_response.status_code == 404
    
    @pytest.mark.e2e
    def test_upload_performance_benchmark(self, e2e_config, test_auth_token):
        """
        Test Case: E2E-PERF-001 - Single User Performance
        
        Upload 1MB document → Measure response time (<5s)
        """
        base_url = e2e_config.base_url
        
        # Create 1MB test file
        file_size = 1024 * 1024  # 1MB
        large_content = b"x" * file_size
        
        files = {
            "file": ("performance_test.pdf", io.BytesIO(large_content), "application/pdf")
        }
        
        # Measure upload time
        start_time = time.time()
        
        upload_response = requests.post(
            f"{base_url}/api/v1/documents/upload",
            files=files,
            headers={"Authorization": f"Bearer {test_auth_token}"},
            timeout=30
        )
        
        end_time = time.time()
        upload_time = end_time - start_time
        
        # Assert performance requirement
        assert upload_time < 5.0, f"Upload took {upload_time:.2f}s, should be < 5s"
        assert upload_response.status_code == 201
        
        # Cleanup
        if upload_response.status_code == 201:
            document_id = upload_response.json()["data"]["id"]
            requests.delete(
                f"{base_url}/api/v1/documents/{document_id}",
                headers={"Authorization": f"Bearer {test_auth_token}"},
                timeout=30
            )
    
    @pytest.mark.e2e
    def test_error_recovery_flow(self, e2e_config, test_auth_token):
        """
        Test Case: E2E-JOURNEY-003 - Error Recovery Flow
        
        1. Upload invalid file → POST /api/v1/upload (expect 400)
        2. Try to access non-existent document → GET /api/v1/documents/{fake-id} (expect 404)
        3. Upload with invalid auth → POST /api/v1/upload (expect 401)
        4. Verify error responses are well-formed
        """
        base_url = e2e_config.base_url
        
        # Step 1: Upload invalid file
        invalid_file = b"This is not a valid PDF or DOCX file"
        files = {
            "file": ("invalid.txt", io.BytesIO(invalid_file), "text/plain")
        }
        
        invalid_response = requests.post(
            f"{base_url}/api/v1/documents/upload",
            files=files,
            headers={"Authorization": f"Bearer {test_auth_token}"},
            timeout=30
        )
        
        assert invalid_response.status_code == 400
        error_data = invalid_response.json()
        assert error_data["success"] is False
        assert "error" in error_data
        assert error_data["error"]["code"] == "FILE_VALIDATION_ERROR"
        
        # Step 2: Access non-existent document
        fake_id = "00000000-0000-0000-0000-000000000000"
        not_found_response = requests.get(
            f"{base_url}/api/v1/documents/{fake_id}",
            headers={"Authorization": f"Bearer {test_auth_token}"},
            timeout=30
        )
        
        assert not_found_response.status_code == 404
        
        # Step 3: Upload with invalid auth
        valid_file = self._create_sample_pdf()
        files = {
            "file": ("test.pdf", io.BytesIO(valid_file), "application/pdf")
        }
        
        unauthorized_response = requests.post(
            f"{base_url}/api/v1/documents/upload",
            files=files,
            headers={"Authorization": "Bearer invalid-token"},
            timeout=30
        )
        
        assert unauthorized_response.status_code == 401
    
    def _create_sample_pdf(self) -> bytes:
        """Create a minimal valid PDF for testing"""
        return b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test CV Content) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000125 00000 n 
0000000185 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
279
%%EOF"""


# E2E test configuration fixtures
@pytest.fixture(scope="session")
def e2e_config():
    """E2E test configuration"""
    import os
    from dataclasses import dataclass
    
    @dataclass
    class E2EConfig:
        base_url: str
        timeout: int
        
    return E2EConfig(
        base_url=os.getenv("E2E_BASE_URL", "http://localhost:5001"),
        timeout=30
    )


@pytest.fixture(scope="session")
def test_auth_token():
    """Get test authentication token"""
    import os
    
    # In a real scenario, this would get a token from Auth0
    # For now, return a mock token that the test environment accepts
    return os.getenv("E2E_AUTH_TOKEN", "mock-test-token")

