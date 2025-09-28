"""
Pytest configuration and shared fixtures for document service tests
"""

import os
import pytest
import tempfile
import uuid
from typing import Generator, Dict, Any
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

from main import create_app
from models.db_models import Base
from utils.database import get_db_manager, init_db


@pytest.fixture(scope="session")
def postgres_container():
    """PostgreSQL test container for pure document storage"""
    with PostgresContainer(
        image="postgres:16",
        username="test",
        password="test",
        dbname="testdb",
        port=5432
    ) as postgres:
        # Wait for container to be ready
        postgres.get_connection_url()
        yield postgres


@pytest.fixture(scope="session")
def test_database_url(postgres_container):
    """Get test database URL"""
    return postgres_container.get_connection_url()


@pytest.fixture(scope="session")
def test_azure_config():
    """Get test Azure Storage configuration (Azurite - includes both blob and queue endpoints)"""
    return {
        "connection_string": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;",
        "container_name": "test-documents"
    }


@pytest.fixture(scope="session")
def test_storage_queue_config():
    """Get test Azure Storage Queue configuration (using Azurite)"""
    return {
        "connection_string": "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;QueueEndpoint=http://127.0.0.1:10001/devstoreaccount1;",
        "queue_name": "document-events"
    }


@pytest.fixture(scope="function")
def test_db_session(test_database_url):
    """Create a test database session"""
    # Create engine for test database
    engine = create_engine(test_database_url, echo=False)
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create session
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_app(test_database_url, test_azure_config, test_storage_queue_config):
    """Create test FastAPI application"""
    # Set test environment variables
    test_env = {
        "DATABASE_URL": test_database_url,
        "AZURE_STORAGE_CONNECTION_STRING": test_azure_config["connection_string"],
        "AZURE_STORAGE_CONTAINER_NAME": test_azure_config["container_name"],
        "AZURE_STORAGE_QUEUE_NAME": test_storage_queue_config["queue_name"],
        "AUTH0_DOMAIN": "test.auth0.com",
        "AUTH0_API_IDENTIFIER": "https://api.test.com/document-service",
        "AUTH0_ALGORITHMS": "RS256",
        "FASTAPI_ENV": "testing"
    }
    
    # Mock document service before any imports
    with patch('routers.documents.get_document_service') as mock_doc_service:
        # Create mock document service
        mock_service = Mock()
        
        # Mock upload_document method
        from models.document import Document
        from datetime import datetime
        from uuid import uuid4
        
        def create_mock_document(*args, **kwargs):
            # Extract filename from kwargs or use default
            filename = kwargs.get('filename', 'test_document.pdf')
            content_type = kwargs.get('content_type', 'application/pdf')
            file_size = len(kwargs.get('file_data', b'')) if kwargs.get('file_data') else 1024
            
            return Document(
                id=uuid4(),
                user_id=kwargs.get('user_id', uuid4()),
                filename=filename,
                file_type=kwargs.get('file_type'),  # Can be None for pure storage
                content_type=content_type,
                file_size=file_size,
                storage_path=f"test/path/{filename}",
                metadata={"test": "data"},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                text_content=None
            )
        
        mock_service.upload_document.side_effect = create_mock_document
        
        # Mock the new async upload_multiple_documents method
        async def mock_upload_multiple_documents(files, user_id):
            from models.document import BulkUploadResponse
            results = []
            successful_uploads = 0
            failed_uploads = 0
            
            for file in files:
                try:
                    # Simple validation - reject non-PDF/DOC/DOCX files
                    if not file.content_type.startswith(('application/pdf', 'application/msword', 'application/vnd.openxmlformats')):
                        results.append({
                            "filename": file.filename,
                            "success": False,
                            "error": f"File type not allowed: {file.content_type}"
                        })
                        failed_uploads += 1
                        continue
                    
                    # Create a mock result for valid files
                    document = create_mock_document(
                        filename=file.filename,
                        content_type=file.content_type,
                        file_data=await file.read(),
                        user_id=user_id
                    )
                    results.append({
                        "filename": file.filename,
                        "success": True,
                        "document_id": str(document.id),
                        "file_type": document.file_type,
                        "content_type": document.content_type,
                        "file_size": document.file_size,
                        "created_at": document.created_at.isoformat()
                    })
                    successful_uploads += 1
                except Exception as e:
                    results.append({
                        "filename": file.filename,
                        "success": False,
                        "error": str(e)
                    })
                    failed_uploads += 1
            
            return BulkUploadResponse(
                total_files=len(files),
                successful_uploads=successful_uploads,
                failed_uploads=failed_uploads,
                results=results
            )
        
        mock_service.upload_multiple_documents = mock_upload_multiple_documents
        
        # Create a default document for other methods
        default_document = create_mock_document()
        mock_service.get_document.return_value = default_document
        mock_service.get_user_documents.return_value = ([default_document], 1)
        mock_service.delete_document.return_value = True
        mock_service.search_documents.return_value = ([default_document], 1)
        mock_service.health_check.return_value = True
        
        mock_doc_service.return_value = mock_service
        
        with patch.dict(os.environ, test_env):
            # Initialize database
            init_db(test_database_url)
            
            # Create tables
            db_manager = get_db_manager()
            db_manager.create_tables()
            
            # Create app without Auth0 middleware for testing
            from main import create_app
            from fastapi import FastAPI
            from fastapi.middleware.cors import CORSMiddleware
            from routers.documents import router as documents_router
            from routers.health import router as health_router
            from routers.auth import router as auth_router
            from utils.fastapi_error_handler import register_exception_handlers
            
            # Create test app without Auth0 middleware
            app = FastAPI(
                title="Document Service API (Test)",
                description="Pure document storage and management microservice",
                version="1.0.0",
            )
            
            # CORS configuration
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )
            
            # Register exception handlers
            register_exception_handlers(app)
            
            # Include routers
            app.include_router(documents_router, prefix="/api/v1/documents", tags=["Documents"])
            app.include_router(health_router, prefix="/health", tags=["Health"])
            app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
            
            yield app


@pytest.fixture(scope="function")
def test_client(test_app):
    """Create test client"""
    return TestClient(test_app)


@pytest.fixture(scope="function")
def integration_app(test_database_url, test_azure_config, test_storage_queue_config):
    """Create integration test FastAPI application with REAL services (no mocking)"""
    # Set test environment variables
    test_env = {
        "DATABASE_URL": test_database_url,
        "AZURE_STORAGE_CONNECTION_STRING": test_azure_config["connection_string"],
        "AZURE_STORAGE_CONTAINER_NAME": test_azure_config["container_name"],
        "AZURE_STORAGE_QUEUE_NAME": test_storage_queue_config["queue_name"],
        "AUTH0_DOMAIN": "test.auth0.com",
        "AUTH0_API_IDENTIFIER": "https://api.test.com/document-service",
        "AUTH0_ALGORITHMS": "RS256",
        "FASTAPI_ENV": "testing"
    }
    
    with patch.dict(os.environ, test_env):
        # Initialize database with real connection
        init_db(test_database_url)
        
        # Create tables
        db_manager = get_db_manager()
        db_manager.create_tables()
        
        # Create app with REAL services (no mocking)
        from main import create_app
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
        from routers.documents import router as documents_router
        from routers.health import router as health_router
        from routers.auth import router as auth_router
        from utils.fastapi_error_handler import register_exception_handlers
        
        # Create integration test app with real services
        app = FastAPI(
            title="Document Service API (Integration Test)",
            description="Pure document storage and management microservice - Integration Testing",
            version="1.0.0",
        )
        
        # CORS configuration
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Register exception handlers
        register_exception_handlers(app)
        
        # Include routers with REAL services
        app.include_router(documents_router, prefix="/api/v1/documents", tags=["Documents"])
        app.include_router(health_router, prefix="/health", tags=["Health"])
        app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
        
        yield app


@pytest.fixture(scope="function")
def integration_client(integration_app):
    """Create integration test client with REAL services"""
    return TestClient(integration_app)


@pytest.fixture(scope="function")
def mock_auth_user():
    """Mock authenticated user"""
    user_id = str(uuid.uuid4())
    return {
        "user_id": user_id,
        "sub": f"auth0|{user_id}",
        "email": "test@example.com"
    }


@pytest.fixture(scope="function")
def auth_headers(mock_auth_user):
    """Mock authentication headers"""
    # Use middleware's mock-test token format to inject user identity without patching
    yield {
        "Authorization": f"Bearer mock-test-{mock_auth_user['user_id']}"
        # Note: No Content-Type header - let FastAPI/TestClient handle multipart/form-data
    }


@pytest.fixture(scope="function")
def sample_pdf_file():
    """Create a sample PDF file for testing"""
    # Create a minimal PDF content
    pdf_content = b"""%PDF-1.4
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
(Sample CV Content) Tj
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
    
    return {
        "filename": "sample_cv.pdf",
        "content": pdf_content,
        "content_type": "application/pdf"
    }


@pytest.fixture(scope="function")
def sample_docx_file():
    """Create a sample DOCX file for testing"""
    # Create a minimal but valid DOCX file structure (must be > 102 bytes)
    docx_content = b"PK\x03\x04\x14\x00\x00\x00\x08\x00\x00\x00!\x00" + b"x" * 100  # Pad to meet minimum size
    
    return {
        "filename": "sample_jd.docx",
        "content": docx_content,
        "content_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    }


@pytest.fixture(scope="function")
def invalid_file():
    """Create an invalid file for testing error scenarios"""
    return {
        "filename": "invalid.txt",
        "content": b"This is not a valid document format",
        "content_type": "text/plain"
    }


@pytest.fixture(scope="function")
def large_file():
    """Create a large file for testing size limits"""
    # Create a file larger than 16MB
    large_content = b"x" * (17 * 1024 * 1024)  # 17MB
    
    return {
        "filename": "large_document.pdf",
        "content": large_content,
        "content_type": "application/pdf"
    }


@pytest.fixture(scope="function")
def mock_storage_service():
    """Mock storage service for unit tests"""
    mock_service = Mock()
    mock_service.upload_file.return_value = "test/path/document.pdf"
    mock_service.download_file.return_value = (b"file content", "application/pdf")
    mock_service.delete_file.return_value = True
    mock_service.health_check.return_value = True
    
    return mock_service


@pytest.fixture(scope="function")
def mock_document_classifier():
    """Mock document classifier for unit tests"""
    mock_classifier = Mock()
    mock_classifier.classify_document.return_value = Mock(
        document_type=Mock(value="cv"),
        confidence=0.95,
        reasoning="Document contains resume-like content"
    )
    
    return mock_classifier


# Test data fixtures
@pytest.fixture(scope="function")
def test_document_data():
    """Sample document data for testing"""
    return {
        "user_id": uuid.uuid4(),
        "filename": "test_document.pdf",
        "file_type": "cv",
        "content_type": "application/pdf",
        "file_size": 1024,
        "storage_path": "test/path/document.pdf",
        "text_content": "Sample CV content with skills and experience",
        "metadata": {
            "skills": ["Python", "FastAPI", "PostgreSQL"],
            "experience_years": 5
        }
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "e2e: marks tests as end-to-end tests"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow running"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers"""
    for item in items:
        # Add integration marker to integration tests
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Add unit marker to unit tests
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        
        # Add e2e marker to e2e tests
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)