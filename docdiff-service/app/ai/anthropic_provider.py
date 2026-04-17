import base64

import anthropic

from app.ai.base import AIProvider, AIResponse, RateLimitError, ServerError, TokenUsage, ai_retry
from app.config import settings

AVAILABLE_MODELS = ["claude-3-7-sonnet-20250219", "claude-3-opus-20240229"]


class AnthropicProvider(AIProvider):
    def __init__(self, model_name: str = "claude-3-7-sonnet-20250219"):
        self._model_name = model_name
        self._client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)

    @property
    def provider_name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._model_name

    @staticmethod
    def available_models() -> list[str]:
        return AVAILABLE_MODELS

    @ai_retry
    async def call(self, prompt: str, images: list[bytes] | None = None, system: str | None = None) -> AIResponse:
        content = []
        if images:
            for img in images:
                b64 = base64.standard_b64encode(img).decode("utf-8")
                content.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": "image/png", "data": b64},
                })
        content.append({"type": "text", "text": prompt})

        try:
            kwargs = {
                "model": self._model_name,
                "max_tokens": 4096,
                "messages": [{"role": "user", "content": content}],
            }
            if system:
                kwargs["system"] = system
            response = await self._client.messages.create(**kwargs)
        except anthropic.RateLimitError as e:
            raise RateLimitError(str(e)) from e
        except anthropic.InternalServerError as e:
            raise ServerError(str(e)) from e

        text = response.content[0].text if response.content else ""
        usage = TokenUsage(
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
        )
        return AIResponse(content=text, usage=usage, model=self._model_name)
