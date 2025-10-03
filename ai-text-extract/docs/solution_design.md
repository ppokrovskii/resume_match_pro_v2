# AI Text Extract Service - Solution Design

## Overview
Serverless microservice processing documents via Azure Functions. Extracts text, classifies types, and extracts metadata using Azure AI services with generated shared models.

## Architecture

### Tech Stack
- **Runtime**: Azure Functions (Python 3.11+)
- **AI**: Azure OpenAI + Document Intelligence
- **Queue**: Azure Storage Queues
- **Models**: Generated from document-service OpenAPI
- **Auth**: Shared-auth middleware
- **Monitoring**: OpenTelemetry + Application Insights

### Processing Flow
```
Queue Event → Download Document → Extract Text → Classify → Extract Features → Update Document
```

## Core Components

### 1. Event Handler
```python
@app.queue_trigger(queue_name="document-created-events")
async def process_document(msg: func.QueueMessage):
    # Main processing entry point
```

### 2. Text Extraction
- **Word**: python-docx → markdown format
- **PDF**: Azure Document Intelligence → markdown format

### 3. AI Services
- **Classification**: Azure OpenAI → CV/JD with confidence
- **Features**: Azure OpenAI → structured features array

### 4. Document Client
- Uses generated shared models for type safety
- Custom HTTPX client with retry logic
- Service-to-service authentication

## Implementation

### Text Extraction
```python
def extract_text_from_docx(file_content: bytes) -> str:
    """Extract as markdown preserving structure"""
    doc = Document(BytesIO(file_content))
    markdown_content = []
    
    for paragraph in doc.paragraphs:
        if paragraph.style.name.startswith('Heading'):
            level = int(paragraph.style.name[-1])
            markdown_content.append(f"{'#' * level} {paragraph.text}")
        else:
            markdown_content.append(paragraph.text)
    
    return "\n\n".join(markdown_content)
```

### AI Classification
```python
async def classify_document(text_content: str) -> dict:
    """Classify as CV or JD using Azure OpenAI"""
    prompt = f"""
    Classify as "CV" or "JD" with confidence 0-1:
    {text_content[:2000]}
    
    JSON: {{"document_type": "CV|JD", "confidence": 0.95}}
    """
    
    response = await openai_client.chat.completions.create(
        model="gpt-4", messages=[{"role": "user", "content": prompt}]
    )
    return json.loads(response.choices[0].message.content)
```

### Complete Processing
```python
async def process_document_complete(document_id: str, file_content: bytes, file_type: str):
    # Extract text (markdown format)
    text_content = await extract_text_from_pdf(file_content) if file_type == 'pdf' else extract_text_from_docx(file_content)
    
    # Classify and extract features
    classification = await classify_document(text_content)
    features = await extract_features(text_content, classification["document_type"])
    
    # Update using generated models
    document_client = DocumentServiceClient()
    await document_client.update_document_features(
        doc_id=document_id,
        features=[Feature(**f) for f in features],
        markdown_content=text_content,
        file_type=classification["document_type"].lower(),
        confidence_score=classification["confidence"]
    )
```

## Configuration
```python
# Environment Variables
DOCUMENT_SERVICE_BASE_URL = "https://api.resumematch.com"
AZURE_OPENAI_ENDPOINT = "https://your-openai.openai.azure.com/"
AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT = "https://your-di.cognitiveservices.azure.com/"
```

## Error Handling
- **Retry Strategy**: 3 attempts with exponential backoff
- **Dead Letter Queue**: Failed messages after retries
- **Timeout**: 30-second processing limit

## Monitoring
- Processing time, success rate, error rate
- Queue depth, AI service usage
- OpenTelemetry tracing with correlation IDs

## Deployment
- Azure Functions Consumption Plan
- Serverless auto-scaling
- Infrastructure as Code (Terraform)