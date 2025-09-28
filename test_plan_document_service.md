# Document Service - Test Plan

## Service Overview
**Service**: Document Service  
**Responsibilities**: File upload/download, document parsing (PDF/Word), text extraction, metadata storage  
**Tech Stack**: Python 3.11+, Flask, Azure Functions, Supabase Storage  

---

## Test Categories

### 1. Unit Tests (DOC-UNIT)
| Test ID | Component | Test Case | Priority |
|---------|-----------|-----------|----------|
| DOC-U-001 | parser_service.py | Extract text from PDF documents | High |
| DOC-U-002 | parser_service.py | Extract text from Word (.docx) documents | High |
| DOC-U-003 | parser_service.py | Extract text from Word (.doc) documents | High |
| DOC-U-004 | parser_service.py | Handle corrupted PDF files | High |
| DOC-U-005 | parser_service.py | Handle corrupted Word files | High |
| DOC-U-006 | file_validators.py | Validate supported file formats | High |
| DOC-U-007 | file_validators.py | Reject unsupported file formats | High |
| DOC-U-008 | file_validators.py | Validate file size limits (5MB) | High |
| DOC-U-009 | text_extractors.py | Clean extracted text content | Medium |
| DOC-U-010 | document_service.py | Create document metadata | High |

### 2. Integration Tests (DOC-INT)
| Test ID | Component | Test Case | Priority |
|---------|-----------|-----------|----------|
| DOC-I-001 | storage_service.py | Upload file to Supabase Storage | High |
| DOC-I-002 | storage_service.py | Download file from Supabase Storage | High |
| DOC-I-003 | storage_service.py | Delete file from Supabase Storage | High |
| DOC-I-004 | document.py | Save document metadata to PostgreSQL | High |
| DOC-I-005 | document.py | Query documents by user_id | High |
| DOC-I-006 | document.py | Query documents by organization_id | Medium |
| DOC-I-007 | upload_session.py | Track bulk upload progress | Medium |

### 3. API Tests (DOC-API)
| Test ID | Endpoint | Test Case | Priority |
|---------|----------|-----------|----------|
| DOC-A-001 | POST /documents/upload | Single file upload success | High |
| DOC-A-002 | POST /documents/upload | Bulk file upload success | High |
| DOC-A-003 | POST /documents/upload | Upload with invalid file format | High |
| DOC-A-004 | POST /documents/upload | Upload exceeding size limit | High |
| DOC-A-005 | POST /documents/upload | Unauthorized upload attempt | High |
| DOC-A-006 | GET /documents | List user documents | High |
| DOC-A-007 | GET /documents | Organization documents access | Medium |
| DOC-A-008 | GET /documents/{id} | Get document details | High |
| DOC-A-009 | GET /documents/{id}/download | Download document | High |
| DOC-A-010 | DELETE /documents/{id} | Delete document | High |
| DOC-A-011 | DELETE /documents/{id} | Delete non-existent document | Medium |

### 4. Performance Tests (DOC-PERF)
| Test ID | Scenario | Test Case | Target |
|---------|----------|-----------|--------|
| DOC-P-001 | File Upload | 5MB PDF upload time | <10s |
| DOC-P-002 | File Upload | 5MB Word upload time | <10s |
| DOC-P-003 | Text Extraction | PDF text extraction time | <5s |
| DOC-P-004 | Text Extraction | Word text extraction time | <5s |
| DOC-P-005 | Bulk Upload | 10 documents upload time | <30s |

### 5. Security Tests (DOC-SEC)
| Test ID | Security Aspect | Test Case | Priority |
|---------|----------------|-----------|----------|
| DOC-S-001 | Authorization | User can only access own documents | High |
| DOC-S-002 | Authorization | Organization member access control | High |
| DOC-S-003 | File Security | Malicious file upload prevention | High |
| DOC-S-004 | Data Isolation | Cross-tenant data isolation | High |
| DOC-S-005 | Input Validation | SQL injection prevention | High |

---

## Test Data Requirements
- Sample PDF files (valid, corrupted, large)
- Sample Word files (.doc, .docx, corrupted)
- Test user accounts with different organization memberships
- Malicious file samples for security testing

## Coverage Target
**Minimum**: 80% code coverage  
**Critical paths**: 100% coverage (file upload, text extraction, authorization)

## Test Environment
- Local emulators: Supabase local stack, Azure Storage emulator
- Test database with sample data
- Mock Azure Functions runtime for unit tests






