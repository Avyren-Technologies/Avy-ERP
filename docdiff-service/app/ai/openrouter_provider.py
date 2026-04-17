import base64

import httpx

from app.ai.base import AIProvider, AIResponse, RateLimitError, ServerError, TokenUsage, ai_retry
from app.config import settings

OPENROUTER_BASE = "https://openrouter.ai/api/v1"
AVAILABLE_MODELS = ["google/gemma-4-31b-it:free", "google/gemini-2.5-pro-preview"]


class OpenRouterProvider(AIProvider):
    def __init__(self, model_name: str = "google/gemma-4-31b-it:free"):
        self._model_name = model_name

    @property
    def provider_name(self) -> str:
        return "openrouter"

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
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64}"},
                })
        content.append({"type": "text", "text": prompt})

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": content})

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{OPENROUTER_BASE}/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model_name,
                    "messages": messages,
                    "max_tokens": 4096,
                },
            )

        if resp.status_code == 429:
            raise RateLimitError("OpenRouter rate limited")
        if resp.status_code >= 500:
            raise ServerError(f"OpenRouter server error: {resp.status_code}")
        resp.raise_for_status()

        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        usage_data = data.get("usage", {})
        usage = TokenUsage(
            input_tokens=usage_data.get("prompt_tokens", 0),
            output_tokens=usage_data.get("completion_tokens", 0),
        )
        return AIResponse(content=text, usage=usage, model=self._model_name)
