# Testing Guide for Qdrant VectorDB Provider

## Setup

Install the package with dev dependencies:

```bash
pip install -e ".[dev]"
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run specific test file
```bash
pytest tests/test_qdrant_client.py
pytest tests/test_qdrant_writer.py
```

### Run specific test class
```bash
pytest tests/test_qdrant_client.py::TestQdrantClientInit
pytest tests/test_qdrant_writer.py::TestQdrantWriterMethods
```

### Run specific test
```bash
pytest tests/test_qdrant_client.py::TestQdrantClientInit::test_init_with_valid_config
```

### Run with coverage
```bash
pytest --cov=nlweb_qdrant_vectordb --cov-report=html
```

Coverage report will be in `htmlcov/index.html`

### Run with verbose output
```bash
pytest -v
```

### Run async tests only
```bash
pytest -m asyncio
```

## Test Structure

### test_qdrant_client.py
Tests for `QdrantClient` class:
- Initialization tests (URL and local path)
- Client connection and caching
- Collection management (create, exists, ensure)
- Search functionality (vector search with HNSW)
- Search by URL
- Get unique sites
- Site filtering
- Result formatting
- Path resolution

### test_qdrant_writer.py
Tests for `QdrantWriter` class:
- Initialization tests
- Document upload/upsert
- Batch processing (100 docs per batch)
- Document deletion
- Site deletion
- Custom collection handling
- Error handling in batches
- Empty embedding handling

## Fixtures

Common fixtures available in `conftest.py`:
- `sample_document`: Single test document
- `sample_documents`: Multiple test documents

## Mocking

Tests use `unittest.mock` for:
- Mocking CONFIG object
- Mocking Qdrant AsyncClient
- Mocking async operations
- Mocking embeddings
- Mocking collection responses

## Coverage Goals

Aim for:
- Line coverage: >90%
- Branch coverage: >85%

## Continuous Integration

Tests should be run on:
- Python 3.9, 3.10, 3.11, 3.12
- Multiple OS: Linux, macOS, Windows
