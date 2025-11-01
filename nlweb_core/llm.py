# Copyright (c) 2025 Microsoft Corporation.
# Licensed under the MIT License

"""
Very simple wrapper around the various LLM providers.  

WARNING: This code is under development and may undergo changes in future releases.
Backwards compatibility is not guaranteed at this time.

"""

from typing import Optional, Dict, Any
from nlweb_core.config import CONFIG
import asyncio
import threading
import subprocess
import sys

# Cache for loaded providers
_loaded_providers = {}

def init():
    """Initialize LLM providers based on configuration."""
    # Get all configured LLM endpoints
    for endpoint_name, endpoint_config in CONFIG.llm_endpoints.items():
        llm_type = endpoint_config.llm_type
        if llm_type and endpoint_name == CONFIG.preferred_llm_endpoint:
            try:
                # Use _get_provider which will load and cache the provider
                _get_provider(llm_type)
            except Exception as e:
                pass

# Mapping of LLM types to their required pip packages
_llm_type_packages = {
    "openai": ["openai>=1.12.0"],
    "anthropic": ["anthropic>=0.18.1"],
    "gemini": ["google-cloud-aiplatform>=1.38.0"],
    "azure_openai": ["openai>=1.12.0"],
    "llama_azure": ["openai>=1.12.0"],
    "deepseek_azure": ["openai>=1.12.0"],
    "inception": ["aiohttp>=3.9.1"],
    "snowflake": ["httpx>=0.28.1"],
    "huggingface": ["huggingface_hub>=0.31.0"],
}

# Cache for installed packages
_installed_packages = set()

def _ensure_package_installed(llm_type: str):
    """
    Ensure the required packages for an LLM type are installed.
    
    Args:
        llm_type: The type of LLM provider
    """
    if llm_type not in _llm_type_packages:
        return
    
    packages = _llm_type_packages[llm_type]
    for package in packages:
        # Extract package name without version for caching
        package_name = package.split(">=")[0].split("==")[0]
        
        if package_name in _installed_packages:
            continue
            
        try:
            # Try to import the package first
            if package_name == "google-cloud-aiplatform":
                __import__("vertexai")
            elif package_name == "huggingface_hub":
                __import__("huggingface_hub")
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
                raise ValueError(f"Failed to install required package {package} for {llm_type}")

def _get_provider(llm_type: str):
    """
    Lazily load and return the provider for the given LLM type.
    
    Args:
        llm_type: The type of LLM provider to load
        
    Returns:
        The provider instance
        
    Raises:
        ValueError: If the LLM type is unknown
    """
    # Return cached provider if already loaded
    if llm_type in _loaded_providers:
        return _loaded_providers[llm_type]

    # Ensure required packages are installed
    _ensure_package_installed(llm_type)

    # Dynamically import the provider based on llm_type
    if llm_type == "openai":
        from nlweb_core.llm_providers.openai import provider
        _loaded_providers[llm_type] = provider
    elif llm_type == "anthropic":
        from nlweb_core.llm_providers.anthropic import provider
        _loaded_providers[llm_type] = provider
    elif llm_type == "gemini":
        from nlweb_core.llm_providers.gemini import provider
        _loaded_providers[llm_type] = provider
    elif llm_type == "azure_openai":
        from nlweb_core.llm_providers.azure_oai import provider
        _loaded_providers[llm_type] = provider
    elif llm_type == "llama_azure":
        from nlweb_core.llm_providers.azure_llama import provider
        _loaded_providers[llm_type] = provider
    elif llm_type == "deepseek_azure":
        from nlweb_core.llm_providers.azure_deepseek import provider
        _loaded_providers[llm_type] = provider
    elif llm_type == "inception":
        from nlweb_core.llm_providers.inception import provider
        _loaded_providers[llm_type] = provider
    elif llm_type == "snowflake":
        from nlweb_core.llm_providers.snowflake import provider
        _loaded_providers[llm_type] = provider
    elif llm_type == "huggingface":
        from nlweb_core.llm_providers.huggingface import provider
        _loaded_providers[llm_type] = provider
    else:
        raise ValueError(f"Unknown LLM type: {llm_type}")

    return _loaded_providers[llm_type]

async def ask_llm(
    prompt: str,
    schema: Dict[str, Any],
    provider: Optional[str] = None,
    level: str = "low",
    timeout: int = 8,
    query_params: Optional[Dict[str, Any]] = None,
    max_length: int = 512
) -> Dict[str, Any]:
    """
    Route an LLM request to the specified endpoint, with dispatch based on llm_type.
    
    Args:
        prompt: The text prompt to send to the LLM
        schema: JSON schema that the response should conform to
        provider: The LLM endpoint to use (if None, use preferred endpoint from config)
        level: The model tier to use ('low' or 'high')
        timeout: Request timeout in seconds
        query_params: Optional query parameters for development mode provider override
        max_length: Maximum length of the response in tokens (default: 512)
        
    Returns:
        Parsed JSON response from the LLM
        
    Raises:
        ValueError: If the endpoint is unknown or response cannot be parsed
        TimeoutError: If the request times out
    """
    # Determine provider, with development mode override support
    provider_name = provider or CONFIG.preferred_llm_endpoint

    print(f"[LLM] Provider: {provider_name}, Level: {level}")

    # In development mode, allow query param override
    if CONFIG.is_development_mode() and query_params:
        from nlweb_core.utils.utils import get_param
        override_provider = get_param(query_params, "llm_provider", str, None)
        if override_provider:
            provider_name = override_provider

        # Also allow level override in development mode
        override_level = get_param(query_params, "llm_level", str, None)
        if override_level:
            level = override_level

    if provider_name not in CONFIG.llm_endpoints:
        error_msg = f"Unknown provider '{provider_name}'"
        print(f"[LLM] ERROR: {error_msg}")
        print(f"[LLM] Available endpoints: {list(CONFIG.llm_endpoints.keys())}")
        return {}

    # Get provider config using the helper method
    provider_config = CONFIG.get_llm_provider(provider_name)
    if not provider_config or not provider_config.models:
        error_msg = f"Missing model configuration for provider '{provider_name}'"
        print(f"[LLM] ERROR: {error_msg}")
        return {}

    # Get llm_type for dispatch
    llm_type = provider_config.llm_type
    print(f"[LLM] LLM type: {llm_type}")

    model_id = getattr(provider_config.models, level)
    print(f"[LLM] Model ID: {model_id}")
    print(f"[LLM] Prompt (first 200 chars): {prompt[:200] if len(prompt) > 200 else prompt}")
    print(f"[LLM] Schema: {schema}")

    # Initialize variables for exception handling
    llm_type_for_error = llm_type

    try:

        # Get the provider instance based on llm_type
        try:
            provider_instance = _get_provider(llm_type)
            print(f"[LLM] Got provider instance: {type(provider_instance).__name__}")
        except ValueError as e:
            error_msg = str(e)
            print(f"[LLM] ERROR getting provider: {error_msg}")
            return {}

        # Simply call the provider's get_completion method without locking
        # Each provider should handle thread-safety internally
        print(f"[LLM] Calling get_completion...")
        result = await asyncio.wait_for(
            provider_instance.get_completion(prompt, schema, model=model_id, timeout=timeout, max_tokens=max_length),
            timeout=timeout
        )
        print(f"[LLM] Got result: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
        return result

    except asyncio.TimeoutError:
        print(f"[LLM] ERROR: Timeout after {timeout}s")
        return {}
    except Exception as e:
        error_msg = f"LLM call failed: {type(e).__name__}: {str(e)}"
        print(f"[LLM] ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return {}


def get_available_providers() -> list:
    """
    Get a list of LLM providers that have their required API keys available.
    
    Returns:
        List of provider names that are available for use.
    """
    available_providers = []
    
    for provider_name, provider_config in CONFIG.llm_endpoints.items():
        # Check if provider config exists and has required fields
        if (provider_config and 
            hasattr(provider_config, 'api_key') and provider_config.api_key and 
            provider_config.api_key.strip() != "" and
            hasattr(provider_config, 'models') and provider_config.models and
            provider_config.models.high and provider_config.models.low):
            available_providers.append(provider_name)
    
    return available_providers
