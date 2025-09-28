# Document Service - Business Requirements

## Overview
Pure document CRUD service that allows users to upload, store, and manage their CVs and job descriptions. File storage and metadata management only - all text extraction and AI processing handled by separate applications.

---

## User Stories & Acceptance Criteria

### 1. Document Upload

**As a** job seeker or recruiter  
**I want to** upload my documents by dragging and dropping them anywhere on the screen  
**So that** I can quickly store multiple CVs or job descriptions for later processing

**Acceptance Criteria:**
- ✅ User can drag and drop 1-10 files anywhere on the browser window
- ✅ System accepts PDF, DOC, and DOCX files up to 16MB each
- ✅ System stores all files securely and shows individual success/failure status
- ✅ User sees upload progress and completion status for each file
- ✅ Failed uploads show clear error messages (file too large, wrong format, etc.)
- ✅ Documents are immediately available for download after upload
- ✅ System publishes `document.uploaded` event for text extraction service
- ✅ No text processing in this service - files stored as-is

**Business Rules:**
- Maximum 10 files per upload session
- Supported formats: PDF, DOC, DOCX only
- File size limit: 16MB per file
- User must be authenticated
- No text extraction or AI processing in this service

### 2. Document Management

**As a** user  
**I want to** view, download, and delete my uploaded documents  
**So that** I can manage my document library effectively

**Acceptance Criteria:**
- ✅ User can see a list of all their uploaded documents
- ✅ List shows document name, file size, upload date, and basic metadata
- ✅ User can download original document files exactly as uploaded
- ✅ User can delete documents they no longer need
- ✅ Deleted documents are permanently removed from storage
- ✅ User cannot see or access other users' documents
- ✅ Document metadata can be updated by external services

**Business Rules:**
- Users only see their own documents (data isolation)
- Enterprise users can see organization documents based on permissions
- Document list is paginated (50 documents per page)
- Soft delete not required - permanent deletion
- No file processing - pure storage service

---

### 3. External Service Integration

**As an** external AI service  
**I want to** update document metadata after processing  
**So that** I can add extracted text, document type, role, and features

**Acceptance Criteria:**
- ✅ External services can update document properties via API
- ✅ Support updating: file_type, text_content, role, features
- ✅ Features support flexible NoSQL structure (name, type, properties)
- ✅ Updates are atomic and validated
- ✅ Only authorized services can update documents
- ✅ Update history is tracked with timestamps
- ✅ System publishes `document.updated` event for AI matching service
- ✅ Document service remains stateless - no processing logic

**Business Rules:**
- Document service only provides CRUD operations
- External services handle all text extraction and AI processing
- Updates must include valid authentication
- No business logic for document analysis in this service

---

### 4. Enterprise Organization Support

**As an** enterprise administrator  
**I want to** manage documents across my organization  
**So that** I can control access and maintain data governance

**Acceptance Criteria:**
- ✅ Organization members can access shared documents based on roles
- ✅ Documents are organized by organization and user hierarchy
- ✅ Individual users have private document spaces
- ✅ Enterprise users have both private and shared spaces
- ✅ Data is completely isolated between different organizations
- ✅ Storage paths reflect organization structure

**Business Rules:**
- Individual users: `/user_id/documents`
- Enterprise users: `/organization_id/user_id/documents`
- Role-based access control for shared documents
- Complete data isolation between organizations

---

## Acceptance Test Scenarios

### Scenario 1: Job Seeker Uploads Resume
**Given** I am a job seeker with a PDF resume  
**When** I drag and drop my resume file onto the upload area  
**Then** the system should store the file successfully  
**And** show me the upload was successful with a document ID  
**And** the file should be immediately available for download  
**And** a `document.uploaded` event should be published for text extraction service  
**And** no text processing should occur in this service

### Scenario 2: Recruiter Bulk Uploads Job Descriptions  
**Given** I am a recruiter with 5 job description files  
**When** I select all files and drag them to the browser window  
**Then** the system should process all 5 files  
**And** show individual success/failure status for each file  
**And** any failed uploads should show clear error messages  
**And** successful uploads should be immediately available in my document list

### Scenario 3: Enterprise User Access Control
**Given** I am an enterprise user in Organization A  
**When** I view my document list  
**Then** I should see my personal documents  
**And** I should see organization documents I have access to  
**And** I should NOT see documents from Organization B  
**And** I should NOT see other users' personal documents

### Scenario 4: External Service Updates Document
**Given** I uploaded a PDF resume and an external text extraction service processed it  
**When** the text extraction service calls the update API with extracted data  
**Then** the document should be updated with the new metadata  
**And** a `document.updated` event should be published for AI matching service  
**And** I should see the extracted text content when viewing the document  
**And** I should see the identified job role (e.g., "Python Developer")  
**And** I should see structured skills with experience levels  
**And** all data should be stored and retrievable via API

### Scenario 5: Document Management
**Given** I have uploaded several documents  
**When** I view my document library  
**Then** I can filter by document type (CV or JD)  
**And** I can download any of my original files  
**And** I can delete documents I no longer need  
**And** deleted documents are permanently removed

## Performance Requirements

### Upload Performance
- Single file upload: Complete within 5 seconds for files up to 16MB
- Multiple file upload: Store 10 files within 15 seconds
- File storage: Immediate availability for download after upload
- No processing delays - pure storage operations

### System Performance  
- Document list loading: Under 2 seconds for 50 documents
- Document download: Start within 1 second
- Search/filter: Results within 3 seconds
- 99.9% uptime during business hours

### Scalability
- Support 1000+ concurrent users
- Handle 10,000+ documents per organization
- Process 100+ file uploads per minute
- Auto-scale based on demand

---

## Security & Compliance

### Data Protection
- All documents encrypted at rest and in transit
- User data completely isolated (cannot access other users' documents)
- Organization data boundaries strictly enforced
- Secure file deletion (data cannot be recovered)

### Authentication & Authorization
- JWT token-based authentication required for all operations
- Role-based access control for enterprise organizations
- Session management and token expiration
- API rate limiting to prevent abuse

### File Security
- Virus scanning for uploaded files (optional)
- File type validation (only PDF, DOC, DOCX allowed)
- File size limits enforced (16MB maximum)
- Malicious file detection and blocking

---

## Business Rules Summary

1. **File Limits**: 16MB per file, 10 files per upload, PDF/DOC/DOCX only
2. **User Isolation**: Users can only access their own documents
3. **Organization Access**: Enterprise users can access shared org documents based on roles
4. **No Processing**: Files stored as-is, no text extraction or AI processing
5. **External Updates**: External services can update document metadata via API
6. **Data Retention**: Documents stored until user deletes them (no automatic expiration)
7. **Audit Trail**: Track document creation, updates, and deletion timestamps

