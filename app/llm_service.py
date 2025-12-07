"""
Generic LLM service for OpenAI API integration.

This module provides a reusable client for interacting with OpenAI's API.
Customize the methods for your specific use case.

Usage:
    from app.llm_service import get_llm_service

    llm = get_llm_service()
    if llm:
        response = await llm.chat([
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello!"}
        ])
"""
import json
import logging
from typing import Optional, Dict, Any, List
from functools import lru_cache
import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


class LLMService:
    """
    Generic OpenAI/LLM client - customize for your use case.
    
    Supports:
    - Chat completions
    - Simple text completion wrapper
    - JSON mode
    - Configurable temperature, tokens, etc.
    """

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.openai_api_key.get_secret_value() if settings.openai_api_key else None
        self.base_url = settings.openai_base_url.rstrip("/")
        self.model = settings.llm_model
        self.temperature = settings.llm_temperature
        self.max_tokens = settings.llm_max_tokens
        self.timeout = settings.llm_timeout
        self.max_retries = settings.llm_max_retries

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        json_mode: bool = False,
        **kwargs
    ) -> Optional[str]:
        """
        Send a chat completion request to OpenAI API.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Override default model
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            json_mode: If True, request JSON response format
            **kwargs: Additional parameters to pass to the API

        Returns:
            The assistant's response text, or None on error
        """
        if not self.api_key:
            logger.warning("LLM service called but no API key configured")
            return None

        # Build request payload
        payload = {
            "model": model or self.model,
            "messages": messages,
            "temperature": temperature if temperature is not None else self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
            **kwargs
        }

        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # Retry loop
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        f"{self.base_url}/chat/completions",
                        headers=headers,
                        json=payload
                    )

                    if response.status_code != 200:
                        error_text = response.text
                        logger.error(f"OpenAI API error: {response.status_code} - {error_text}")
                        last_error = f"API error: {response.status_code}"
                        continue

                    data = response.json()

                    # Extract response content
                    choices = data.get("choices", [])
                    if not choices:
                        logger.error("No choices in API response")
                        return None

                    content = choices[0].get("message", {}).get("content", "")

                    # Log token usage if available
                    usage = data.get("usage", {})
                    if usage:
                        logger.debug(
                            f"LLM tokens: prompt={usage.get('prompt_tokens')}, "
                            f"completion={usage.get('completion_tokens')}, "
                            f"total={usage.get('total_tokens')}"
                        )

                    return content

            except httpx.TimeoutException:
                logger.warning(f"LLM request timeout (attempt {attempt + 1}/{self.max_retries + 1})")
                last_error = "Request timeout"
            except Exception as e:
                logger.error(f"LLM request failed: {str(e)}")
                last_error = str(e)

        logger.error(f"LLM request failed after {self.max_retries + 1} attempts: {last_error}")
        return None

    async def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Optional[str]:
        """
        Simple text completion wrapper around chat().

        Args:
            prompt: The user's prompt
            system_prompt: Optional system message
            **kwargs: Additional parameters passed to chat()

        Returns:
            The completion text, or None on error
        """
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        return await self.chat(messages, **kwargs)

    async def complete_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Get a JSON response from the LLM.

        Args:
            prompt: The user's prompt (should request JSON output)
            system_prompt: Optional system message
            **kwargs: Additional parameters passed to chat()

        Returns:
            Parsed JSON dict, or None on error
        """
        response = await self.complete(
            prompt,
            system_prompt=system_prompt,
            json_mode=True,
            **kwargs
        )

        if not response:
            return None

        try:
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM JSON response: {e}")
            return None


@lru_cache()
def get_llm_service() -> Optional[LLMService]:
    """
    Get LLM service instance if configured.
    
    Returns:
        LLMService instance if API key is configured, None otherwise
    """
    settings = get_settings()
    
    if not settings.openai_api_key:
        logger.debug("LLM service not available: OPENAI_API_KEY not configured")
        return None
    
    logger.info(f"LLM service initialized: model={settings.llm_model}")
    return LLMService()

