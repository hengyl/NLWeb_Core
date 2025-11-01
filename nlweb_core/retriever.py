# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""
Unified vector database interface with support for Azure AI Search, Milvus, and Qdrant.
This module provides abstract base classes and concrete implementations for database operations.
"""

import os
import time
import asyncio
import subprocess
import sys
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Union, Tuple, Type
import json

from nlweb_core.config import CONFIG
from nlweb_core.utils.utils import get_param
from nlweb_core.utils.json_utils import merge_json_array

# Client cache for reusing instances
_client_cache = {}
_client_cache_lock = asyncio.Lock()

# Preloaded client modules
_preloaded_modules = {}

def init():
    """Initialize retrieval clients based on configuration."""
    # Preload modules for enabled endpoints
    for endpoint_name, endpoint_config in CONFIG.retrieval_endpoints.items():
        if endpoint_config.enabled and endpoint_config.db_type:
            db_type = endpoint_config.db_type
            try:
                # Ensure packages are installed
                _ensure_package_installed(db_type)
                
                # Preload the module
                if db_type == "azure_ai_search":
                    from nlweb_core.retrieval_providers.azure_search_client import AzureSearchClient
                    _preloaded_modules[db_type] = AzureSearchClient
                elif db_type == "milvus":
                    from nlweb_core.retrieval_providers.milvus_client import MilvusVectorClient
                    _preloaded_modules[db_type] = MilvusVectorClient
                elif db_type == "opensearch":
                    from nlweb_core.retrieval_providers.opensearch_client import OpenSearchClient
                    _preloaded_modules[db_type] = OpenSearchClient
                elif db_type == "qdrant":
                    from nlweb_core.retrieval_providers.qdrant import QdrantVectorClient
                    _preloaded_modules[db_type] = QdrantVectorClient
                elif db_type == "snowflake_cortex_search":
                    from nlweb_core.retrieval_providers.snowflake_client import SnowflakeCortexSearchClient
                    _preloaded_modules[db_type] = SnowflakeCortexSearchClient
                elif db_type == "elasticsearch":
                    from nlweb_core.retrieval_providers.elasticsearch_client import ElasticsearchClient
                    _preloaded_modules[db_type] = ElasticsearchClient
                elif db_type == "postgres":
                    from nlweb_core.retrieval_providers.postgres_client import PgVectorClient
                    _preloaded_modules[db_type] = PgVectorClient
                elif db_type == "shopify_mcp":
                    from nlweb_core.retrieval_providers.shopify_mcp import ShopifyMCPClient
                    _preloaded_modules[db_type] = ShopifyMCPClient
                elif db_type == "cloudflare_autorag":
                    from nlweb_core.retrieval_providers.cf_autorag_client import (
                        CloudflareAutoRAGClient,
                    )

                    _preloaded_modules[db_type] = CloudflareAutoRAGClient
                elif db_type == "bing_search":
                    from nlweb_core.retrieval_providers.bing_search_client import BingSearchClient
                    _preloaded_modules[db_type] = BingSearchClient

            except Exception as e:
                pass

# Mapping of database types to their required pip packages
_db_type_packages = {
    "azure_ai_search": ["azure-core", "azure-search-documents>=11.4.0"],
    "milvus": ["pymilvus>=1.1.0", "numpy"],
    "opensearch": ["httpx>=0.28.1"],
    "qdrant": ["qdrant-client>=1.14.0"],
    "snowflake_cortex_search": ["httpx>=0.28.1"],
    "elasticsearch": ["elasticsearch[async]>=8,<9"],
    "postgres": ["psycopg", "psycopg[binary]>=3.1.12", "psycopg[pool]>=3.2.0", "pgvector>=0.4.0"],
    "shopify_mcp": ["aiohttp>=3.8.0"],
    "cloudflare_autorag": ['cloudflare>=4.3.1', "httpx>=0.28.1", "zon>=3.0.0", "markdown>=3.8.2", "beautifulsoup4>=4.13.4"],
    "bing_search": ["httpx>=0.28.1"],  # Bing search uses httpx for API calls
}

# Cache for installed packages
_installed_packages = set()

def _ensure_package_installed(db_type: str):
    """
    Ensure the required packages for a database type are installed.
    
    Args:
        db_type: The type of database backend
    """
    if db_type not in _db_type_packages:
        return
    
    packages = _db_type_packages[db_type]
    for package in packages:
        # Extract package name without version for caching
        package_name = package.split(">=")[0].split("==")[0].split("[")[0]
        
        if package_name in _installed_packages:
            continue
            
        try:
            # Try to import the package first
            if package_name == "azure-core":
                __import__("azure.core")
            elif package_name == "azure-search-documents":
                __import__("azure.search.documents")
            elif package_name == "qdrant-client":
                __import__("qdrant_client")
            elif package_name == "elasticsearch":
                __import__("elasticsearch")
            elif package_name == "psycopg":
                __import__("psycopg")
            else:
                __import__(package_name)
            _installed_packages.add(package_name)
        except ImportError:
            # Package not installed, install it
            try:
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", package, "--quiet"
                ])
                _installed_packages.add(package_name)
            except subprocess.CalledProcessError as e:
                raise ValueError(f"Failed to install required package {package} for {db_type}")


class VectorDBClientInterface(ABC):
    """
    Abstract base class defining the interface for vector database clients.
    All vector database implementations should implement the search method.
    """

    @abstractmethod
    async def search(self, query: str, site: Union[str, List[str]],
                    num_results: int = 50, **kwargs) -> List[List[str]]:
        """
        Search for documents matching the query and site.

        Args:
            query: Search query string
            site: Site identifier or list of sites
            num_results: Maximum number of results to return
            **kwargs: Additional parameters

        Returns:
            List of search results, where each result is [url, json_str, name, site]
        """
        pass




class VectorDBClient:
    """
    Client for vector database operations using a single retrieval endpoint.
    """

    def __init__(self, endpoint_name: Optional[str] = None, query_params: Optional[Dict[str, Any]] = None):
        """
        Initialize the database client with a single endpoint.

        Args:
            endpoint_name: Name of the endpoint to use
            query_params: Optional query parameters for overriding endpoint
        """
        self.query_params = query_params or {}

        # Check if query_params specifies a database endpoint override
        if self.query_params:
            param_endpoint = self.query_params.get('db') or self.query_params.get('retrieval_backend')
            if param_endpoint:
                # Handle case where param_endpoint might be a list
                if isinstance(param_endpoint, list):
                    if len(param_endpoint) > 0:
                        param_endpoint = param_endpoint[0]
                    else:
                        param_endpoint = None

                if param_endpoint:
                    endpoint_name = param_endpoint

        # Require an endpoint name
        if not endpoint_name:
            # Use first enabled endpoint with valid credentials
            for name, config in CONFIG.retrieval_endpoints.items():
                if config.enabled and self._has_valid_credentials(name, config):
                    endpoint_name = name
                    break

            if not endpoint_name:
                raise ValueError("No endpoint specified and no enabled endpoints with valid credentials found")

        # Validate the endpoint
        if endpoint_name not in CONFIG.retrieval_endpoints:
            available_endpoints = list(CONFIG.retrieval_endpoints.keys())
            raise ValueError(f"Invalid endpoint: '{endpoint_name}'. Available endpoints: {', '.join(available_endpoints)}")

        endpoint_config = CONFIG.retrieval_endpoints[endpoint_name]

        # Validate credentials
        if not self._has_valid_credentials(endpoint_name, endpoint_config):
            raise ValueError(f"Endpoint '{endpoint_name}' is missing required credentials")

        self.endpoint_name = endpoint_name
        self.endpoint_config = endpoint_config
        self.db_type = endpoint_config.db_type

        
    def _has_valid_credentials(self, name: str, config) -> bool:
        """
        Check if an endpoint has valid credentials based on its database type.
        
        Args:
            name: Endpoint name
            config: Endpoint configuration
            
        Returns:
            True if endpoint has required credentials
        """
        db_type = config.db_type
        
        if db_type in ["azure_ai_search", "snowflake_cortex_search", "opensearch", "milvus"]:
            # These require API key and endpoint
            return bool(config.api_key and config.api_endpoint)
        elif db_type == "qdrant":
            # Qdrant can use either local path or remote URL
            if config.database_path:
                return True  # Local file-based storage
            else:
                return bool(config.api_endpoint)  # Remote server (api_key is optional)
        elif db_type == "elasticsearch":
            # Elasticsearch requires endpoint, API key is optional
            return bool(config.api_endpoint)
        elif db_type == "postgres":
            # PostgreSQL requires endpoint (connection string) and optionally api_key (password)
            return bool(config.api_endpoint)
        elif db_type == "shopify_mcp":
            # Shopify MCP doesn't require authentication
            return True
        elif db_type == "cloudflare_autorag":
            return bool(config.api_key)
            return bool(config.database_path)
        elif db_type == "bing_search":
            # Bing search just needs to be enabled (API key can be hardcoded or from env)
            return True
        else:
            return False
    
    async def get_client(self) -> VectorDBClientInterface:
        """
        Get or initialize the vector database client for this endpoint.
        Uses a cache to avoid creating duplicate client instances.

        Returns:
            Appropriate vector database client
        """
        # Use cache key combining db_type and endpoint
        cache_key = f"{self.db_type}_{self.endpoint_name}"

        # Check if client already exists in cache
        async with _client_cache_lock:
            if cache_key in _client_cache:
                return _client_cache[cache_key]

            # Ensure required packages are installed
            _ensure_package_installed(self.db_type)

            # Create the appropriate client using preloaded module or dynamic import
            try:
                # Use preloaded module if available
                if self.db_type in _preloaded_modules:
                    client_class = _preloaded_modules[self.db_type]
                # Otherwise load on demand
                elif self.db_type == "azure_ai_search":
                    from nlweb_core.retrieval_providers.azure_search_client import AzureSearchClient
                    client_class = AzureSearchClient
                elif self.db_type == "milvus":
                    from nlweb_core.retrieval_providers.milvus_client import MilvusVectorClient
                    client_class = MilvusVectorClient
                elif self.db_type == "opensearch":
                    from nlweb_core.retrieval_providers.opensearch_client import OpenSearchClient
                    client_class = OpenSearchClient
                elif self.db_type == "qdrant":
                    from nlweb_core.retrieval_providers.qdrant import QdrantVectorClient
                    client_class = QdrantVectorClient
                elif self.db_type == "snowflake_cortex_search":
                    from nlweb_core.retrieval_providers.snowflake_client import SnowflakeCortexSearchClient
                    client_class = SnowflakeCortexSearchClient
                elif self.db_type == "cloudflare_autorag":
                    from nlweb_core.retrieval_providers.cf_autorag_client import CloudflareAutoRAGClient
                    client_class = CloudflareAutoRAGClient
                elif self.db_type == "elasticsearch":
                    from nlweb_core.retrieval_providers.elasticsearch_client import ElasticsearchClient
                    client_class = ElasticsearchClient
                elif self.db_type == "postgres":
                    from nlweb_core.retrieval_providers.postgres_client import PgVectorClient
                    client_class = PgVectorClient
                elif self.db_type == "shopify_mcp":
                    from nlweb_core.retrieval_providers.shopify_mcp import ShopifyMCPClient
                    client_class = ShopifyMCPClient
                elif self.db_type == "bing_search":
                    from nlweb_core.retrieval_providers.bing_search_client import BingSearchClient
                    client_class = BingSearchClient
                else:
                    error_msg = f"Unsupported database type: {self.db_type}"
                    raise ValueError(error_msg)

                # Instantiate the client
                client = client_class(self.endpoint_name)
            except ImportError as e:
                raise ValueError(f"Failed to load client for {self.db_type}: {e}")

            # Store in cache and return
            _client_cache[cache_key] = client
            return client
    
    
    async def search(self, query: str, site: Union[str, List[str]],
                    num_results: int = 50, **kwargs) -> List[List[str]]:
        """
        Search for documents matching the query and site.

        Args:
            query: Search query string
            site: Site identifier or list of sites
            num_results: Maximum number of results to return
            **kwargs: Additional parameters

        Returns:
            List of search results
        """
     
        try:
            client = await self.get_client()
            return await client.search(query, site, num_results, **kwargs)

        except Exception as e:
            raise


# Factory function to make it easier to get a client with the right type
def get_vector_db_client(endpoint_name: Optional[str] = None, 
                        query_params: Optional[Dict[str, Any]] = None) -> VectorDBClient:
    """
    Factory function to create a vector database client with the appropriate configuration.
    Uses a global cache to avoid repeated initialization and site queries.
    
    Args:
        endpoint_name: Optional name of the endpoint to use
        query_params: Optional query parameters for overriding endpoint
        
    Returns:
        Configured VectorDBClient instance (cached if possible)
    """
    global _client_cache
    
    # Create a cache key based on endpoint_name
    # Note: We don't include query_params in the key since they're typically the same
    cache_key = endpoint_name or 'default'
    
    # Check if we have a cached client
    if cache_key in _client_cache:
        return _client_cache[cache_key]
    
    # Create a new client and cache it
    client = VectorDBClient(endpoint_name=endpoint_name, query_params=query_params)
    _client_cache[cache_key] = client
    
    return client




async def search(query: str,
                site: str = "all",
                num_results: int = 50,
                endpoint_name: Optional[str] = None,
                query_params: Optional[Dict[str, Any]] = None,
                handler: Optional[Any] = None,
                **kwargs) -> List[Dict[str, Any]]:
    """
    Simplified search interface that combines client creation and search in one call.
    
    Args:
        query: The search query
        site: Site to search in (default: "all")
        num_results: Number of results to return (default: 10)
        endpoint_name: Optional name of the endpoint to use
        query_params: Optional query parameters for overriding endpoint
        handler: Optional handler with http_handler for sending messages
        **kwargs: Additional parameters passed to the search method
        
    Returns:
        List of search results
        
    Example:
        results = await search("climate change", site="example.com", num_results=5)
    """
    client = get_vector_db_client(endpoint_name=endpoint_name, query_params=query_params)

    return await client.search(query, site, num_results, **kwargs)
    
    return results


