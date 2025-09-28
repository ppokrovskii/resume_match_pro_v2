# Resume Match Pro AI - MVP Requirements

## 1. Product Overview

**Product Name**: Resume Match Pro AI  
**Target Users**: HR Professionals and Hiring Managers  
**Purpose**: AI-powered tool to match CVs with Job Descriptions and identify best candidates  
**MVP Scope**: Core matching functionality with intuitive drag-and-drop interface  

---

## 2. Functional Requirements

### 2.1 Document Management

**REQ-2.1.1** The system SHALL support drag-and-drop upload of CV documents anywhere on the screen  
**REQ-2.1.2** The system SHALL support drag-and-drop upload of Job Description documents anywhere on the screen  
**REQ-2.1.3** The system SHALL support bulk upload of multiple documents simultaneously  
**REQ-2.1.4** The system SHALL accept Word (.doc, .docx) document formats  
**REQ-2.1.5** The system SHALL accept PDF document formats  
**REQ-2.1.6** The system SHALL extract and parse text content from uploaded documents  
**REQ-2.1.7** The system SHALL generate embeddings for all uploaded documents  
**REQ-2.1.8** The system SHALL display uploaded CVs in the left panel  
**REQ-2.1.9** The system SHALL display uploaded Job Descriptions in the right panel  
**REQ-2.1.10** Users SHALL be able to download any uploaded document  
**REQ-2.1.11** Users SHALL be able to delete uploaded documents  

### 2.2 User Interface Layout

**REQ-2.2.1** The system SHALL provide a dual-pane interface layout  
**REQ-2.2.2** The left pane SHALL display CV documents list  
**REQ-2.2.3** The right pane SHALL display Job Description documents list  
**REQ-2.2.4** Each document item SHALL be clickable  
**REQ-2.2.5** The system SHALL provide visual feedback when hovering over document items  

### 2.3 AI Matching Engine

**REQ-2.3.1** The system SHALL calculate match scores between CVs and Job Descriptions using embeddings  
**REQ-2.3.2** Match scores SHALL be expressed as numerical values (0-100 scale)  
**REQ-2.3.3** The system SHALL use embedding similarity to determine compatibility objectively  
**REQ-2.3.4** Match scores SHALL be calculated in real-time when documents are uploaded  

### 2.4 Filtering and Sorting

**REQ-2.4.1** When a CV is clicked, the system SHALL filter Job Descriptions to show relevant matches  
**REQ-2.4.2** When a Job Description is clicked, the system SHALL filter CVs to show relevant matches  
**REQ-2.4.3** Filtered results SHALL be sorted by match score in descending order (highest match first)  
**REQ-2.4.4** The system SHALL display match scores alongside filtered results  
**REQ-2.4.5** Users SHALL be able to clear filters and return to full document lists

### 2.5 Advanced Search

**REQ-2.5.1** Users SHALL be able to search documents using semantic queries  
**REQ-2.5.2** The system SHALL support skill-based searches (e.g., "python", "excel", "accounting")  
**REQ-2.5.3** The system SHALL support role-based searches (e.g., "accountant", "developer", "manager")  
**REQ-2.5.4** The system SHALL support technology searches (e.g., "hr systems", "CRM", "databases")  
**REQ-2.5.5** Search results SHALL be ranked by embedding similarity  
**REQ-2.5.6** The system SHALL provide real-time search suggestions  

---

## 3. Non-Functional Requirements

### 3.1 Performance

**REQ-3.1.1** Document upload SHALL complete within 10 seconds for files up to 5MB  
**REQ-3.1.2** Match score calculation SHALL complete within 5 seconds per document pair  
**REQ-3.1.3** Filtering and sorting SHALL respond within 2 seconds  

### 3.2 Usability

**REQ-3.2.1** The interface SHALL be intuitive for non-technical HR users  
**REQ-3.2.2** Drag-and-drop functionality SHALL work across the entire application area  
**REQ-3.2.3** Visual indicators SHALL clearly show document upload progress  

### 3.3 Compatibility

**REQ-3.3.1** The system SHALL support modern web browsers (Chrome, Firefox, Safari, Edge)  
**REQ-3.3.2** The system SHALL be responsive for desktop and tablet devices  

---

## 4. Data Requirements

### 4.1 Document Storage

**REQ-4.1.1** The system SHALL store uploaded documents securely  
**REQ-4.1.2** Document metadata SHALL include filename, upload timestamp, and file type  
**REQ-4.1.3** Extracted text content SHALL be stored for matching purposes  

### 4.2 Match Data

**REQ-4.2.1** Match scores SHALL be stored and associated with CV-JD pairs  
**REQ-4.2.2** Match results SHALL be persistent across user sessions  

---

## 5. Authentication and Authorization

**REQ-5.1.1** Users SHALL be able to register and login with email and password  
**REQ-5.1.2** Users SHALL be able to login using Google OAuth  
**REQ-5.1.3** Users SHALL only see and access their own uploaded documents  
**REQ-5.1.4** The system SHALL support organization accounts for enterprise users  
**REQ-5.1.5** Organization members SHALL be able to access shared documents within their organization  
**REQ-5.1.6** Organization administrators SHALL be able to manage member access

## 6. Security Requirements

**REQ-6.1.1** Uploaded documents SHALL be processed securely  
**REQ-6.1.2** Document content SHALL be protected from unauthorized access  
**REQ-6.1.3** User sessions SHALL be managed securely  
**REQ-6.1.4** Organization data SHALL be isolated between different organizations  

---

## 7. Error Handling

**REQ-7.1.1** The system SHALL display clear error messages for unsupported file formats  
**REQ-7.1.2** The system SHALL handle corrupted or unreadable documents gracefully  
**REQ-7.1.3** The system SHALL provide feedback when matching fails or is incomplete  
**REQ-7.1.4** Users SHALL be able to retry failed operations  
**REQ-7.1.5** The system SHALL handle bulk upload failures gracefully with per-file status  

---

## 8. MVP Limitations

**LIMIT-8.1** Document editing capabilities are out of scope  
**LIMIT-8.2** Detailed match explanations are out of scope  
**LIMIT-8.3** Advanced organization management features are out of scope  
**LIMIT-8.4** Document version control is out of scope  

---

## 9. Acceptance Criteria Summary

For MVP completion, the system must:
1. Support user authentication with email/password and Google OAuth
2. Successfully upload CV and JD documents via drag-and-drop (single and bulk)
3. Generate embeddings for semantic search and matching
4. Display documents in dual-pane layout with download and delete options
5. Calculate and display embedding-based match scores
6. Filter and sort results when documents are clicked
7. Provide semantic search functionality for skills, roles, and technologies
8. Support organization accounts for enterprise users
9. Provide responsive user experience within performance thresholds
