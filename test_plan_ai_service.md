# AI Service - Test Plan

## Service Overview
**Service**: AI Service  
**Responsibilities**: Embedding generation, similarity calculations, match score computation, semantic search  
**Tech Stack**: Python 3.11+, Flask, Azure OpenAI, PostgreSQL pgvector  

---

## Test Categories

### 1. Unit Tests (AI-UNIT)
| Test ID | Component | Test Case | Priority |
|---------|-----------|-----------|----------|
| AI-U-001 | embedding_service.py | Generate embeddings for text content | High |
| AI-U-002 | embedding_service.py | Handle Azure OpenAI API failures | High |
| AI-U-003 | embedding_service.py | Batch embedding generation | Medium |
| AI-U-004 | matching_service.py | Calculate cosine similarity | High |
| AI-U-005 | matching_service.py | Compute match scores (0-100 scale) | High |
| AI-U-006 | matching_service.py | Handle invalid embedding vectors | High |
| AI-U-007 | search_service.py | Perform vector similarity search | High |
| AI-U-008 | search_service.py | Rank search results by similarity | High |
| AI-U-009 | vector_utils.py | Normalize embedding vectors | Medium |
| AI-U-010 | similarity_metrics.py | Calculate distance metrics | Medium |

### 2. Integration Tests (AI-INT)
| Test ID | Component | Test Case | Priority |
|---------|-----------|-----------|----------|
| AI-I-001 | embedding.py | Store embeddings in PostgreSQL pgvector | High |
| AI-I-002 | embedding.py | Query similar embeddings | High |
| AI-I-003 | embedding.py | Update existing embeddings | Medium |
| AI-I-004 | match_result.py | Store match results in database | High |
| AI-I-005 | match_result.py | Query match history | Medium |
| AI-I-006 | Azure OpenAI | Real API integration test | High |
| AI-I-007 | PostgreSQL | Vector index performance | Medium |

### 3. API Tests (AI-API)
| Test ID | Endpoint | Test Case | Priority |
|---------|----------|-----------|----------|
| AI-A-001 | POST /ai/embeddings | Generate embeddings for document | High |
| AI-A-002 | POST /ai/embeddings | Handle empty text input | High |
| AI-A-003 | POST /ai/embeddings | Handle oversized text input | Medium |
| AI-A-004 | POST /ai/match | Calculate CV-JD match score | High |
| AI-A-005 | POST /ai/match | Match non-existent documents | High |
| AI-A-006 | POST /ai/search | Semantic search by skills | High |
| AI-A-007 | POST /ai/search | Semantic search by roles | High |
| AI-A-008 | POST /ai/search | Semantic search by technologies | High |
| AI-A-009 | GET /ai/matches/{cv_id}/{jd_id} | Get specific match result | High |
| AI-A-010 | POST /ai/search | Search with empty query | Medium |

### 4. Performance Tests (AI-PERF)
| Test ID | Scenario | Test Case | Target |
|---------|----------|-----------|--------|
| AI-P-001 | Embedding Generation | Single document embedding time | <5s |
| AI-P-002 | Match Calculation | CV-JD match score calculation | <5s |
| AI-P-003 | Vector Search | Semantic search response time | <2s |
| AI-P-004 | Batch Processing | 100 embeddings generation time | <60s |
| AI-P-005 | Database Query | Vector similarity query performance | <1s |

### 5. AI Quality Tests (AI-QUAL)
| Test ID | Quality Aspect | Test Case | Priority |
|---------|---------------|-----------|----------|
| AI-Q-001 | Match Accuracy | High-match CV-JD pairs score >80 | High |
| AI-Q-002 | Match Accuracy | Low-match CV-JD pairs score <30 | High |
| AI-Q-003 | Search Relevance | Skill search returns relevant CVs | High |
| AI-Q-004 | Search Relevance | Role search returns relevant JDs | High |
| AI-Q-005 | Embedding Consistency | Same text generates same embedding | High |
| AI-Q-006 | Similarity Logic | Similar documents have high scores | High |

### 6. Security Tests (AI-SEC)
| Test ID | Security Aspect | Test Case | Priority |
|---------|----------------|-----------|----------|
| AI-S-001 | Data Privacy | User embeddings are isolated | High |
| AI-S-002 | API Security | Unauthorized embedding requests blocked | High |
| AI-S-003 | Input Validation | Malicious text input handling | High |
| AI-S-004 | Rate Limiting | Azure OpenAI rate limit compliance | Medium |

---

## Test Data Requirements
- Sample CV and JD text content with known similarity levels
- Test embeddings with known vector values
- Azure OpenAI API test account with quota limits
- Performance benchmark datasets

## Mock Strategy
- **DO NOT MOCK**: Azure OpenAI API (use test account)
- **DO NOT MOCK**: PostgreSQL (use local instance with pgvector)
- **Mock**: External service failures for error handling tests

## Coverage Target
**Minimum**: 80% code coverage  
**Critical paths**: 100% coverage (embedding generation, match calculation, search)

## Test Environment
- Local PostgreSQL with pgvector extension
- Azure OpenAI test endpoint with quota monitoring
- Test data with ground truth similarity scores






