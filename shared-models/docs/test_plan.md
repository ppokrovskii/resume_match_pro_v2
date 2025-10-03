# Shared Models Package - Test Plan

## Package Overview
**Package**: Shared Models  
**Purpose**: Auto-generated Pydantic models from microservice OpenAPI specs  
**Responsibilities**: Type safety, API compatibility, model generation, distribution  
**Tech Stack**: Pydantic v2, datamodel-code-generator, Azure Artifacts  

---

## Test Categories

### 1. Model Generation Tests (GEN) - **MISSING - CRITICAL**
| Test ID | Component | Test Case | Type | Priority |
|---------|-----------|-----------|------|----------|
| GEN-001 | generate_models.py | Fetch OpenAPI spec from Document Service | Integration | High |
| GEN-002 | generate_models.py | Generate models from valid OpenAPI spec | Unit | High |
| GEN-003 | generate_models.py | Handle service unavailable gracefully | Unit | High |
| GEN-004 | generate_models.py | Handle invalid OpenAPI spec format | Unit | High |
| GEN-005 | generate_models.py | Create correct file structure | Unit | High |
| GEN-006 | generate_models.py | Validate generated Python syntax | Unit | High |

### 2. Base Classes Tests (BASE) - **MISSING - IMPORTANT**
| Test ID | Component | Test Case | Type | Priority |
|---------|-----------|-----------|------|----------|
| BASE-001 | base.py | BaseSharedModel initialization | Unit | High |
| BASE-002 | base.py | TimestampMixin functionality | Unit | High |
| BASE-003 | base.py | UserContextMixin functionality | Unit | High |
| BASE-004 | base.py | MetadataMixin functionality | Unit | High |
| BASE-005 | base.py | Base model serialization | Unit | High |
| BASE-006 | base.py | Base model validation | Unit | High |

### 3. Generated Model Tests (MODEL) - **DONE - EXCELLENT**
| Test ID | Component | Test Case | Status | Priority |
|---------|-----------|-----------|--------|----------|
| MODEL-001 | Feature models | Feature creation and validation | ✅ PASSING | High |
| MODEL-002 | Document models | DocumentResponse validation | ❌ 1 FAILING | High |
| MODEL-003 | Document models | DocumentUpdateRequest validation | ✅ PASSING | High |
| MODEL-004 | Document models | List and bulk response models | ✅ PASSING | High |
| MODEL-005 | All models | Serialization/deserialization | ✅ PASSING | High |
| MODEL-006 | All models | Required field validation | ✅ PASSING | High |
| MODEL-007 | All models | Optional field handling | ✅ PASSING | Medium |

---

## Current Test Status

### ✅ **WORKING WELL (Keep as-is)**
- **Model Tests**: 18/19 passing, 100% code coverage
- **Test Structure**: Well-organized with good fixtures
- **Validation Logic**: Comprehensive positive/negative testing
- **Serialization**: JSON conversion working correctly

### ❌ **NEEDS TO BE ADDED (Missing Critical Tests)**

#### **1. Model Generation Tests** (`tests/test_generation.py` - **MISSING**)
```python
# Need to create this file to test scripts/generate_models.py
def test_fetch_openapi_spec_success()
def test_fetch_openapi_spec_failure() 
def test_generate_models_from_valid_spec()
def test_handle_invalid_openapi_spec()
def test_create_correct_directory_structure()
```

#### **2. Base Classes Tests** (`tests/test_base_classes.py` - **MISSING**)
```python
# Need to create this file to test src/shared_models/base.py
def test_base_shared_model()
def test_timestamp_mixin()
def test_user_context_mixin()  
def test_metadata_mixin()
```

### 🐛 **NEEDS TO BE FIXED (Existing Issues)**

#### **1. Failing Validation Test** 
```python
# In tests/test_document_service_models.py line 131
def test_document_response_validation(self):
    # This test expects ValidationError but doesn't get one
    with pytest.raises(ValidationError):
        DocumentResponse(file_type="invalid")  # Should fail but doesn't
```

#### **2. Broken Test Runner**
- `test_runner.py` has Unicode encoding issues on Windows
- Redundant with pytest - should be removed

---

## Implementation Priority

### 🔥 **CRITICAL (Do First)**
1. **Fix failing validation test** - Debug `DocumentResponse(file_type="invalid")` 
2. **Create `tests/test_generation.py`** - Test the core model generation logic
3. **Create `tests/test_base_classes.py`** - Test base model functionality

### 📋 **NICE TO HAVE (Later)**
4. Remove broken `test_runner.py` file
5. Add more edge case testing for generation script

---

## Test Environment Setup

### Local Development
```bash
# Install in development mode
cd shared-models
uv pip install -e . --system

# Run tests with coverage
uv run pytest tests/ --cov=src/shared_models --cov-report=html
```

### Test Data Requirements
- **Valid OpenAPI specs** - For generation testing
- **Invalid OpenAPI specs** - For error handling testing  
- **Sample model data** - Already covered in fixtures

---

## Success Criteria (Realistic MVP)

### Must Have
- ✅ **Models work correctly** (18/19 tests passing - almost there)
- ❌ **Generation script tested** (missing completely)  
- ❌ **Base classes tested** (missing explicitly)

### Coverage Target
- **Current**: 100% code coverage ✅
- **Goal**: Keep 80%+ with new test files ✅
- **Focus**: Test critical business logic, not infrastructure

**Realistic Total**: ~15 focused test cases (not 35!)  
**Current Status**: 19 tests, need ~8 more for generation + base classes  
**Effort**: 1-2 hours to complete vs. 8+ hours for overkill approach
