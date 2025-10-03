# AI Text Extract Service - Requirements

## Overview
Serverless microservice that extracts text from documents, classifies types (CV/JD), and extracts structured metadata using Azure AI.

## Functional Requirements

### FR-001: Document Text Extraction
- Extract text from Word (.docx) and PDF files in **markdown format**
- Tools: python-docx for Word, Azure AI Document Intelligence for PDF
- Quality: Preserve headers, lists, and structure as markdown

### FR-002: Document Classification
- Classify as CV/Resume or Job Description using Azure OpenAI
- Output: Document type with confidence score (>95% accuracy)

### FR-003: Event-Driven Processing  
- Subscribe to `document.created` events from Azure Storage Queue
- Flow: Download → Extract → Classify → Update via document-service API

### FR-004: Metadata Extraction
- Extract structured features using Azure OpenAI
- CV: Skills, experience, education, role
- JD: Required skills, experience level, job requirements
- Output: Structured features array for matching

## Non-Functional Requirements

### Performance
- <30 seconds per document (95th percentile)
- Unlimited serverless auto-scaling
- Handle hundreds of concurrent documents

### Reliability
- 99.9% uptime (serverless platform)
- Retry failed extractions up to 3 times
- Fully stateless - no persistent storage

### Security
- Trust API Gateway headers for authentication
- No local document storage
- Process in-memory only (30-second max)

## Integration

### Document Service API
- Download: `GET /documents/{id}/download`
- Update: `PUT /documents/{id}` with extracted data
- Auth: Shared-auth middleware headers

### Azure Services
- **Storage Queue**: `document-created-events`
- **AI Services**: Document Intelligence + OpenAI
- **Models**: GPT-4/GPT-3.5-turbo for classification and extraction

## Data Schema

### Input Event
```json
{
  "eventType": "document.created",
  "documentId": "uuid",
  "fileName": "string",
  "userId": "uuid",
  "organizationId": "uuid"
}
```

### Output Update
```json
{
  "file_type": "cv|jd",
  "markdown_content": "# John Doe\n\n## Experience\n...",
  "role": "Python Developer",
  "features": [
    {
      "name": "Python",
      "type": "skill", 
      "properties": {"years": 5, "level": "expert"}
    }
  ],
  "metadata": {
    "processing_version": "1.2.0",
    "confidence_score": 0.95
  }
}
```

## Success Criteria
- ✅ 98% successful text extraction
- ✅ >95% classification accuracy  
- ✅ <30 second processing SLA
- ✅ Unlimited concurrent processing
- ✅ 99.9% service availability