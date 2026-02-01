"""
AI client adapter module providing unified interface for multiple AI providers.
"""

import json
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import anthropic
import openai
from dashscope import Generation


class AIClient(ABC):
    """Base class for AI clients with unified interface."""

    def __init__(self, model: str, api_key: str):
        self.model = model
        self.api_key = api_key

    @abstractmethod
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate content using AI model.

        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)

        Returns:
            Generated text content
        """
        pass


class AnthropicClient(AIClient):
    """Claude API client."""

    def __init__(self, model: str, api_key: str):
        super().__init__(model, api_key)
        self.client = anthropic.Anthropic(api_key=api_key)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = [{"role": "user", "content": prompt}]

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": messages
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = self.client.messages.create(**kwargs)
        return response.content[0].text


class OpenAIClient(AIClient):
    """OpenAI GPT client."""

    def __init__(self, model: str, api_key: str):
        super().__init__(model, api_key)
        self.client = openai.OpenAI(api_key=api_key)

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            max_tokens=4096
        )

        return response.choices[0].message.content


class DashScopeClient(AIClient):
    """Alibaba DashScope (Qwen) client."""

    def __init__(self, model: str, api_key: str):
        super().__init__(model, api_key)
        import dashscope
        dashscope.api_key = api_key

    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        response = Generation.call(
            model=self.model,
            messages=messages,
            result_format='message'
        )

        if response.status_code == 200:
            return response.output.choices[0].message.content
        else:
            raise Exception(f"DashScope API error: {response.message}")


def get_client(provider: str, model: str, api_key: str) -> AIClient:
    """
    Factory method to create appropriate AI client.

    Args:
        provider: Provider name ('anthropic', 'openai', or 'dashscope')
        model: Model name
        api_key: API key

    Returns:
        AIClient instance

    Raises:
        ValueError: If provider is not supported
    """
    provider = provider.lower()

    if provider == "anthropic":
        return AnthropicClient(model, api_key)
    elif provider == "openai":
        return OpenAIClient(model, api_key)
    elif provider == "dashscope":
        return DashScopeClient(model, api_key)
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def load_api_config(username: str) -> Optional[Dict[str, Any]]:
    """
    Load API configuration from user's api_key.txt file.

    Args:
        username: The username

    Returns:
        Dictionary with API configurations, or None if file doesn't exist
    """
    from config import USERS_DIR, API_KEY_FILE

    api_file = USERS_DIR / username / API_KEY_FILE

    if not api_file.exists() or api_file.stat().st_size == 0:
        return None

    try:
        with open(api_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError:
        return None


def save_api_config(username: str, config: Dict[str, Any]) -> bool:
    """
    Save API configuration to user's api_key.txt file.

    Args:
        username: The username
        config: API configuration dictionary

    Returns:
        True if saved successfully
    """
    from config import USERS_DIR, API_KEY_FILE

    api_file = USERS_DIR / username / API_KEY_FILE

    with open(api_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    return True
