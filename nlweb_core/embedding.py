# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""
Wrapper around the various embedding providers.

WARNING: This code is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time.
"""

from typing import Optional, List
import asyncio
import threading

from nlweb_core.config import CONFIG


# Add locks for thread-safe provider access
_provider_locks = {
    "openai": threading.Lock(),
    "gemini": threading.Lock(),
    "azure_openai": threading.Lock(),
    "snowflake": threading.Lock(),
    "elasticsearch": threading.Lock()
}

async def get_embedding(
    text: str,
    provider: Optional[str] = None,
    model: Optional[str] = None,
    timeout: int = 30,
    query_params: Optional[dict] = None
) -> List[float]:
    """
    Get embedding for the provided text using the specified provider and model.

    Args:
        text: The text to embed
        provider: Optional provider name, defaults to preferred_embedding_provider
        model: Optional model name, defaults to the provider's configured model
        timeout: Maximum time to wait for embedding response in seconds
        query_params: Optional query parameters from HTTP request

    Returns:
        List of floats representing the embedding vector
    """
    # Allow overriding provider in development mode
    if CONFIG.is_development_mode() and query_params:
        if 'embedding_provider' in query_params:
            provider = query_params['embedding_provider']

    provider = provider or CONFIG.preferred_embedding_provider

    # Truncate text to 20k characters to avoid token limit issues
    MAX_CHARS = 20000
    original_length = len(text)
    if original_length > MAX_CHARS:
        text = text[:MAX_CHARS]


    if provider not in CONFIG.embedding_providers:
        error_msg = f"Unknown embedding provider '{provider}'"
        raise ValueError(error_msg)

    # Get provider config using the helper method
    provider_config = CONFIG.get_embedding_provider(provider)
    if not provider_config:
        error_msg = f"Missing configuration for embedding provider '{provider}'"
        raise ValueError(error_msg)

    # Use the provided model or fall back to the configured model
    model_id = model or provider_config.model
    if not model_id:
        error_msg = f"No embedding model specified for provider '{provider}'"
        raise ValueError(error_msg)


    try:
        # Use a timeout wrapper for all embedding calls
        if provider == "openai":
            from nlweb_core.embedding_providers.openai_embedding import get_openai_embeddings
            result = await asyncio.wait_for(
                get_openai_embeddings(text, model=model_id),
                timeout=timeout
            )
            return result

        if provider == "gemini":
            from nlweb_core.embedding_providers.gemini_embedding import get_gemini_embeddings
            result = await asyncio.wait_for(
                get_gemini_embeddings(text, model=model_id),
                timeout=timeout
            )
            return result

        if provider == "azure_openai":
            from nlweb_core.embedding_providers.azure_oai_embedding import get_azure_embedding
            result = await asyncio.wait_for(
                get_azure_embedding(text, model=model_id),
                timeout=timeout
            )
            return result

        if provider == "ollama":
            from nlweb_core.embedding_providers.ollama_embedding import get_ollama_embedding
            result = await asyncio.wait_for(
                get_ollama_embedding(text, model=model_id),
                timeout=timeout
            )
            return result

        if provider == "snowflake":
            from nlweb_core.embedding_providers.snowflake_embedding import cortex_embed
            result = await asyncio.wait_for(
                cortex_embed(text, model=model_id),
                timeout=timeout
            )
            return result

        if provider == "elasticsearch":
            from nlweb_core.embedding_providers.elasticsearch_embedding import ElasticsearchEmbedding
            elasticsearch_embedding = ElasticsearchEmbedding()
            result = await elasticsearch_embedding.get_embeddings(
                text,
                model=model_id,
                timeout=timeout
            )
            await elasticsearch_embedding.close()
            return result

        error_msg = f"No embedding implementation for provider '{provider}'"
        raise ValueError(error_msg)

    except asyncio.TimeoutError:
        raise
    except Exception as e:
        raise
