"""OpenRouter API client for making LLM requests."""

from typing import List, Dict, Any, Optional
from .config import OPENROUTER_API_KEY, OPENROUTER_API_URL
from openai import AsyncOpenAI

# Create a single client instance to reuse across requests
_client = AsyncOpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_API_URL)


async def query_model(
    model: str,
    messages: List[Dict[str, str]],
    timeout: float = 120.0
) -> Optional[Dict[str, Any]]:
    """
    Query a single model via OpenRouter API.

    Args:
        model: OpenRouter model identifier (e.g., "openai/gpt-4o")
        messages: List of message dicts with 'role' and 'content'
        timeout: Request timeout in seconds

    Returns:
        Response dict with 'content' and optional 'reasoning_details', or None if failed
    """
    try:
        # log the model being queried
        print(f"Querying model: {model}")
        response = await _client.chat.completions.create(
            model=model,
            messages=messages,
            stream=False,
            timeout=timeout
        )

        message = response.choices[0].message
        return {
            'content': getattr(message, 'content', None),
            'reasoning_details': getattr(message, 'reasoning_details', None)
        }

    except Exception as e:
        print(f"Error querying model {model}: {e}")
        return None


async def query_models_parallel(
    models: List[str],
    messages: List[Dict[str, str]]
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Query multiple models in parallel.

    Args:
        models: List of OpenRouter model identifiers
        messages: List of message dicts to send to each model

    Returns:
        Dict mapping model identifier to response dict (or None if failed)
    """
    import asyncio

    # Create tasks for all models
    tasks = [query_model(model, messages) for model in models]

    # Wait for all to complete
    responses = await asyncio.gather(*tasks)

    # Map models to their responses
    return {model: response for model, response in zip(models, responses)}
