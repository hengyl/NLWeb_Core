# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""
Pytest configuration for Qdrant vectordb tests
"""

import pytest


@pytest.fixture(scope="session")
def event_loop_policy():
    """Set event loop policy for async tests"""
    import asyncio
    return asyncio.get_event_loop_policy()


@pytest.fixture
def sample_document():
    """Sample document for testing"""
    return {
        'url': 'https://example.com/page1',
        'site': 'example.com',
        'name': 'page1',
        'schema_json': '{"title": "Page 1", "content": "Test content"}',
        'embedding': [0.1] * 1536
    }


@pytest.fixture
def sample_documents():
    """Multiple sample documents for testing"""
    return [
        {
            'url': 'https://example.com/page1',
            'site': 'example.com',
            'name': 'page1',
            'schema_json': '{"title": "Page 1"}',
            'embedding': [0.1] * 1536
        },
        {
            'url': 'https://example.com/page2',
            'site': 'example.com',
            'name': 'page2',
            'schema_json': '{"title": "Page 2"}',
            'embedding': [0.2] * 1536
        },
        {
            'url': 'https://another.com/page3',
            'site': 'another.com',
            'name': 'page3',
            'schema_json': '{"title": "Page 3"}',
            'embedding': [0.3] * 1536
        }
    ]
