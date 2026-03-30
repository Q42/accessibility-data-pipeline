---
name: "Phase 1: Foundation Refactor"
about: Critical improvements for error handling, logging, and testing
title: "[REFACTOR] Phase 1: Foundation - Error Handling, Logging, Testing"
labels: enhancement, technical-debt, priority-high
assignees: ''
---

## Context

Following the PR #8 code review, this issue tracks Phase 1 of the architectural refactor roadmap. The codebase is 3+ years old and lacks fundamental software engineering practices.

**Related Documents:**
- [PR_REVIEW.md](../PR_REVIEW.md)
- [REVIEW_SUMMARY.md](../REVIEW_SUMMARY.md)

---

## Phase 1 Goals: Foundation

Establish fundamental practices for reliability and maintainability.

**Target:** Complete within 1 sprint (3-5 days focused work)

---

## Tasks

### 1. Error Handling & Retry Logic

**Current State:** No try/except blocks, failures cause complete job failures

**Required Changes:**

- [ ] Add retry logic with exponential backoff for all GCP API calls
  - BigQuery queries
  - Firestore operations
  - Cloud Storage operations
- [ ] Implement proper exception handling in all components
- [ ] Add circuit breakers for external service calls
- [ ] Define error handling strategy (fail fast vs. graceful degradation)
- [ ] Add error recovery mechanisms where appropriate

**Files to Update:**
- `pipelines/components/transform.py`
- `pipelines/components/merge.py`
- `pipelines/components/aggregate_*.py`
- `pipelines/components/firestore_export.py`
- `pipelines/components/cleanup_*.py`
- `api/main.py`

**Example Implementation:**
```python
from google.api_core import retry
from google.api_core.exceptions import GoogleAPIError

@retry.Retry(predicate=retry.if_exception_type(GoogleAPIError))
def query_with_retry(client, query):
    try:
        query_job = client.query(query)
        return query_job.result()
    except GoogleAPIError as e:
        print(f"Query failed: {e}")
        raise
```

---

### 2. Structured Logging

**Current State:** Only `print()` statements, no structured logging

**Required Changes:**

- [ ] Replace all `print()` statements with proper logging
- [ ] Implement structured logging (JSON format) with:
  - Correlation IDs for request tracing
  - Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Contextual information (component, operation, duration)
- [ ] Integrate with Cloud Logging
- [ ] Add log aggregation for pipeline runs
- [ ] Document logging standards

**Files to Update:**
- All `pipelines/components/*.py`
- `pipelines/main.py`
- `api/main.py`
- `cloud-function/main.py`

**Example Implementation:**
```python
import logging
import json
from datetime import datetime

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)

logger = logging.getLogger(__name__)

def log_structured(level, message, **kwargs):
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'level': level,
        'message': message,
        **kwargs
    }
    logger.log(getattr(logging, level), json.dumps(log_entry))

# Usage
log_structured('INFO', 'Query started', 
               component='transform', 
               table=table_name, 
               row_count=1000)
```

---

### 3. Unit Testing Infrastructure

**Current State:** Zero unit tests

**Required Changes:**

- [ ] Set up pytest framework
  - Add `pytest`, `pytest-cov`, `pytest-mock` to requirements
  - Create `tests/` directory structure
  - Add `conftest.py` with common fixtures
- [ ] Add unit tests for critical components (target: 50% coverage)
  - `utils/schema.py` (100% coverage - it's pure logic)
  - `utils/generate_schemas.py` (100% coverage)
  - `utils/recompute_hashes.py` (mock BigQuery client)
  - Transform logic (mock GCP clients)
  - API validation logic
- [ ] Add test fixtures for BigQuery/Firestore mocks
- [ ] Add coverage reporting
- [ ] Document testing standards

**Directory Structure:**
```
pipelines/
  tests/
    __init__.py
    conftest.py
    test_schema.py
    test_generate_schemas.py
    test_recompute_hashes.py
    components/
      test_transform.py
      test_merge.py
      test_aggregate.py
```

**Example Test:**
```python
import pytest
from unittest.mock import Mock, patch
from utils.schema import load_schema, SchemaField

def test_load_schema_android(tmp_path):
    # Arrange
    schema_file = tmp_path / "schema-android.json"
    schema_file.write_text('[{"name": "test_field", "type": "STRING"}]')
    
    # Act
    result = load_schema("android", tmp_path)
    
    # Assert
    assert len(result) == 1
    assert result[0].name == "test_field"
    assert result[0].type == "STRING"

@patch('google.cloud.bigquery.Client')
def test_recompute_hashes(mock_bq_client):
    # Test implementation
    pass
```

---

### 4. Update API & Cloud Function to Python 3.13

**Current State:** API and cloud-function still on Python 3.9

**Required Changes:**

- [ ] Update `api/Dockerfile` to `FROM python:3.13`
- [ ] Update `api/app.yaml` to `runtime: python313` (or migrate to Cloud Run)
- [ ] Update `api/requirements.txt` dependencies for Python 3.13 compatibility
- [ ] Update `cloud-function/requirements.txt` for Python 3.13
- [ ] Test all services on Python 3.13
- [ ] Update documentation

**Files to Update:**
- `api/Dockerfile`
- `api/app.yaml`
- `api/requirements.txt`
- `cloud-function/requirements.txt`
- `api/README.md`
- `cloud-function/README.md`

---

### 5. Replace Unsafe Command Execution

**Current State:** Using `os.system()` for BigQuery operations

**Required Changes:**

- [ ] Replace `os.system()` in `utils/update_table_schemas.py`
- [ ] Use BigQuery Python client for table operations
- [ ] Add proper error handling for table copy/update operations
- [ ] Add validation of operation success

**File to Update:**
- `pipelines/utils/update_table_schemas.py`

**Example Implementation:**
```python
from google.cloud import bigquery
from google.api_core.exceptions import NotFound

def update_table_schemas(platform: str, organisation: str, project_name: str, 
                         pipeline_version: str, schemas_dir: Path):
    client = bigquery.Client(project=project_name)
    
    # Create backup using BigQuery client
    source_table = f"{project_name}.pipeline_{organisation}.aggregated_data_{platform}_{pipeline_version}"
    backup_table = f"{project_name}.pipeline_{organisation}_archive.aggregated_data_{platform}_{pipeline_version}"
    
    try:
        job = client.copy_table(source_table, backup_table)
        job.result()  # Wait for completion
        logger.info(f"Backup created: {backup_table}")
        
        # Update schema
        table_ref = client.get_table(source_table)
        # ... update logic
        
    except NotFound as e:
        logger.error(f"Table not found: {e}")
        raise
    except Exception as e:
        logger.error(f"Failed to update schema: {e}")
        raise
```

---

## Acceptance Criteria

- [ ] All GCP API calls have retry logic with exponential backoff
- [ ] All components use structured logging (no `print()` statements)
- [ ] Cloud Logging integration configured and tested
- [ ] Test suite achieves minimum 50% code coverage
- [ ] All services running on Python 3.13
- [ ] No use of `os.system()` for GCP operations
- [ ] CI/CD pipeline runs tests automatically
- [ ] Documentation updated to reflect changes

---

## Testing Plan

1. **Unit Tests:** Run `pytest --cov=. --cov-report=html` and verify >50% coverage
2. **Integration Tests:** Test on staging environment with dummy data
3. **Error Scenarios:** Verify retry logic works (simulate network failures)
4. **Logging:** Verify structured logs appear in Cloud Logging
5. **Python 3.13:** Deploy all services and verify compatibility

---

## Dependencies

- Access to GCP project for testing
- Staging environment for integration testing
- CI/CD pipeline setup (GitHub Actions or Cloud Build)

---

## Estimated Effort

**3-5 days** of focused development work

**Breakdown:**
- Error handling & retry: 1 day
- Structured logging: 1 day
- Unit testing infrastructure: 2 days
- Python 3.13 updates: 0.5 days
- Replace unsafe commands: 0.5 days

---

## Related Issues

This is Phase 1 of a 5-phase refactor:
- Phase 1: Foundation (this issue)
- Phase 2: Quality & Observability
- Phase 3: Architecture Modernization
- Phase 4: Security & Compliance
- Phase 5: Documentation & Operations

---

## Resources

- [Google Cloud Python Client Libraries](https://cloud.google.com/python/docs/reference)
- [Pytest Documentation](https://docs.pytest.org/)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)
- [Google Cloud Logging](https://cloud.google.com/logging/docs/setup/python)
