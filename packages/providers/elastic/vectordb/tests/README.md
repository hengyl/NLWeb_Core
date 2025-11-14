# Testing Guide for Elasticsearch VectorDB Provider

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
pytest tests/test_elasticsearch_client.py
pytest tests/test_elasticsearch_writer.py
```

### Run specific test class
```bash
pytest tests/test_elasticsearch_client.py::TestElasticsearchClientInit
pytest tests/test_elasticsearch_writer.py::TestElasticsearchWriterMethods
```

### Run specific test
```bash
pytest tests/test_elasticsearch_client.py::TestElasticsearchClientInit::test_init_with_valid_config
```

### Run with coverage
```bash
pytest --cov=nlweb_elastic_vectordb --cov-report=html
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

### test_elasticsearch_client.py
Tests for `ElasticsearchClient` class:
- Initialization tests
- Client connection and caching
- Index management (create, delete)
- Search functionality (vector search, KNN)
- Search by URL
- Get unique sites
- Response formatting
- Context manager

### test_elasticsearch_writer.py
Tests for `ElasticsearchWriter` class:
- Initialization tests
- Document upload/indexing
- Batch processing
- Document deletion
- Site deletion
- Custom index handling
- Error handling

## Fixtures

Common fixtures available in `conftest.py`:
- `sample_document`: Single test document
- `sample_documents`: Multiple test documents

## Mocking

Tests use `unittest.mock` for:
- Mocking CONFIG object
- Mocking Elasticsearch client
- Mocking async operations
- Mocking embeddings

## Coverage Goals

Aim for:
- Line coverage: >90%
- Branch coverage: >85%

## Continuous Integration

Tests should be run on:
- Python 3.9, 3.10, 3.11, 3.12
- Multiple OS: Linux, macOS, Windows
