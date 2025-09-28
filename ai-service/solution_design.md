# AI Service - Solution Design

## Service Overview

**Purpose**: AI-powered matching and search capabilities  
**Technology**: Python 3.11+ with Flask  
**Deployment**: Azure Functions (Consumption Plan)  
**AI Platform**: Azure OpenAI, Supabase PostgreSQL with pgvector  

## Responsibilities

- Text embedding generation
- Semantic similarity calculations
- CV-JD matching algorithms
- Vector search operations
- Match score computation
- Real-time search suggestions

## Architecture

### Core Components

```
ai-service/
├── app.py                      # Flask app entry point
├── routes/
│   ├── embeddings.py          # Embedding operations
│   ├── matching.py            # Match calculations
│   └── search.py              # Semantic search
├── models/
│   ├── embedding.py           # Embedding data model
│   ├── match_result.py        # Match results
│   └── search_result.py       # Search results
├── services/
│   ├── embedding_service.py   # Azure OpenAI integration
│   ├── matching_service.py    # Similarity calculations
│   └── search_service.py      # Vector search operations
├── utils/
│   ├── vector_utils.py        # Vector operations
│   └── similarity_metrics.py  # Distance calculations
└── tests/                     # Unit tests
```

## API Endpoints

### Embedding Operations (`/embeddings`)
- `POST /embeddings/generate` - Generate embeddings for text
- `POST /embeddings/batch` - Batch embedding generation
- `GET /embeddings/{document_id}` - Get document embeddings
- `DELETE /embeddings/{document_id}` - Delete embeddings

### Matching Operations (`/matching`)
- `POST /matching/calculate` - Calculate match scores
- `POST /matching/batch` - Batch match calculations
- `GET /matching/results/{cv_id}` - Get CV match results
- `GET /matching/results/{cv_id}/{jd_id}` - Get specific match

### Search Operations (`/search`)
- `POST /search/semantic` - Semantic text search
- `POST /search/skills` - Skill-based search
- `POST /search/roles` - Role-based search
- `GET /search/suggestions` - Real-time search suggestions

## Data Models

### Embedding Model
```python
@dataclass
class DocumentEmbedding:
    id: str
    document_id: str
    user_id: str
    embedding_vector: List[float]
    text_chunks: List[str]
    chunk_embeddings: List[List[float]]
    model_version: str
    created_at: datetime
    metadata: dict
```

### Match Result Model
```python
@dataclass
class MatchResult:
    id: str
    cv_id: str
    jd_id: str
    user_id: str
    match_score: float
    similarity_breakdown: dict
    matching_skills: List[str]
    skill_gaps: List[str]
    confidence_level: float
    created_at: datetime
```

### Search Result Model
```python
@dataclass
class SearchResult:
    document_id: str
    document_type: str
    relevance_score: float
    matched_content: str
    highlighted_text: str
    metadata: dict
```

## AI/ML Pipeline

### 1. Text Preprocessing
- Text cleaning and normalization
- Skill extraction using NER
- Section identification (experience, education, etc.)
- Keyword extraction and weighting

### 2. Embedding Generation
- Azure OpenAI text-embedding-ada-002
- Chunked text processing (512 token limit)
- Batch processing for efficiency
- Vector normalization

### 3. Similarity Calculation
- Cosine similarity for semantic matching
- Weighted similarity for different sections
- Skill-specific matching algorithms
- Experience level compatibility

### 4. Match Scoring
- Multi-factor scoring algorithm
- Skill match percentage
- Experience relevance
- Education alignment
- Industry fit assessment

## Matching Algorithm

### Core Matching Logic
```python
def calculate_match_score(cv_embedding, jd_embedding, metadata):
    # Base semantic similarity
    semantic_score = cosine_similarity(cv_embedding, jd_embedding)
    
    # Skill-specific matching
    skill_score = calculate_skill_match(cv_metadata, jd_metadata)
    
    # Experience level matching
    experience_score = calculate_experience_match(cv_metadata, jd_metadata)
    
    # Final weighted score
    final_score = (
        semantic_score * 0.4 +
        skill_score * 0.4 +
        experience_score * 0.2
    ) * 100
    
    return min(final_score, 100)
```

### Skill Extraction & Matching
- NLP-based skill identification
- Skill taxonomy mapping
- Synonym and related skill matching
- Skill importance weighting

## Vector Search Implementation

### Azure Cognitive Search Configuration
```python
SEARCH_CONFIG = {
    "index_name": "resume_embeddings",
    "vector_fields": ["content_vector"],
    "searchable_fields": ["content", "skills", "title"],
    "filterable_fields": ["document_type", "user_id", "created_date"],
    "facetable_fields": ["skills", "experience_level", "industry"]
}
```

### Search Query Structure
- Hybrid search (vector + keyword)
- Semantic ranking
- Result filtering and faceting
- Real-time query suggestions

## Dependencies

### Core Dependencies
```
flask==3.0.0
openai==1.3.0
supabase==2.0.0
numpy==1.24.3
scikit-learn==1.3.2
psycopg2-binary==2.9.7
pgvector==0.2.3
opentelemetry-api==1.21.0
```

### NLP Dependencies
```
spacy==3.7.2
nltk==3.8.1
transformers==4.35.0
sentence-transformers==2.2.2
```

## Configuration

### Environment Variables
- `OPENAI_API_KEY` - Azure OpenAI API key
- `OPENAI_ENDPOINT` - Azure OpenAI endpoint
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `EMBEDDING_MODEL` - Model name (text-embedding-ada-002)
- `MAX_TOKENS` - Maximum tokens per request (8000)

### Model Configuration
```python
EMBEDDING_CONFIG = {
    "model": "text-embedding-ada-002",
    "chunk_size": 512,
    "chunk_overlap": 50,
    "batch_size": 16,
    "max_retries": 3,
    "timeout": 30
}

MATCHING_CONFIG = {
    "similarity_threshold": 0.7,
    "skill_weight": 0.4,
    "experience_weight": 0.3,
    "education_weight": 0.2,
    "industry_weight": 0.1
}
```

## Performance Optimization

### Caching Strategy
- Embedding result caching (Redis)
- Match result caching
- Search suggestion caching
- Model response caching

### Batch Processing
- Bulk embedding generation
- Parallel similarity calculations
- Async processing for large datasets
- Queue management for high loads

### Cost Optimization
- Token usage monitoring
- Request batching
- Result caching to reduce API calls
- Efficient prompt engineering

## Error Handling

### API Errors
- OpenAI rate limiting
- Token limit exceeded
- Model unavailability
- Network timeout handling

### Data Errors
- Invalid text input
- Malformed embeddings
- Missing metadata
- Corrupted vector data

## Testing Strategy

### Unit Tests
- Embedding generation accuracy
- Similarity calculation correctness
- Match scoring algorithms
- Vector operations

### Integration Tests
- Azure OpenAI integration
- Cognitive Search operations
- End-to-end matching pipeline
- Performance benchmarks

### AI Model Testing
- Embedding quality validation
- Match score accuracy testing
- Search relevance evaluation
- A/B testing for algorithm improvements

## Monitoring & Analytics

### Key Metrics
- Embedding generation latency
- Match calculation accuracy
- Search result relevance
- API usage and costs

### AI Model Monitoring
- Embedding drift detection
- Match score distribution
- Search click-through rates
- User satisfaction feedback

### Performance Monitoring
- Response times by operation
- Token usage per request
- Cache hit rates
- Error rates by endpoint

## Security & Privacy

### Data Protection
- No PII in embeddings
- Encrypted vector storage
- User data isolation
- Audit logging for AI operations

### Model Security
- API key rotation
- Request rate limiting
- Input validation
- Output sanitization
