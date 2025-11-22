from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import anthropic
import openai
from .config import settings


class LLMClient(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict:
        """Send chat completion request"""
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Estimate token count"""
        pass


class OpenAIClient(LLMClient):
    """OpenAI API client"""
    
    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict:
        """Send chat completion to OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model=kwargs.get("model", self.model),
                messages=messages,
                temperature=kwargs.get("temperature", settings.llm_temperature),
                max_tokens=kwargs.get("max_tokens", settings.llm_max_tokens)
            )
            
            return {
                "content": response.choices[0].message.content,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "model": response.model,
                "finish_reason": response.choices[0].finish_reason
            }
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """Rough token estimation (4 chars ≈ 1 token)"""
        return len(text) // 4


class AnthropicClient(LLMClient):
    """Anthropic Claude API client"""
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229"):
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> Dict:
        """Send chat completion to Anthropic"""
        try:
            # Anthropic requires system message separate
            system_message = None
            formatted_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                else:
                    formatted_messages.append(msg)
            
            response = await self.client.messages.create(
                model=kwargs.get("model", self.model),
                max_tokens=kwargs.get("max_tokens", settings.llm_max_tokens),
                temperature=kwargs.get("temperature", settings.llm_temperature),
                system=system_message if system_message else None,
                messages=formatted_messages
            )
            
            return {
                "content": response.content[0].text,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens
                },
                "model": response.model,
                "finish_reason": response.stop_reason
            }
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    def count_tokens(self, text: str) -> int:
        """Rough token estimation"""
        return len(text) // 4


def get_llm_client() -> LLMClient:
    """Factory function to get appropriate LLM client"""
    provider = settings.llm_provider.lower()
    
    if provider == "openai":
        if not settings.openai_api_key:
            raise ValueError("OpenAI API key not configured")
        return OpenAIClient(
            api_key=settings.openai_api_key,
            model=settings.llm_model
        )
    
    elif provider == "anthropic":
        if not settings.anthropic_api_key:
            raise ValueError("Anthropic API key not configured")
        return AnthropicClient(
            api_key=settings.anthropic_api_key,
            model=settings.llm_model
        )
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
