import base64

import httpx

from app.ai.base import AIProvider, AIResponse, RateLimitError, ServerError, TokenUsage, ai_retry
from app.config import settings

AVAILABLE_MODELS = ["qwen3-vl-8b", "qwen3-vl-30b-a3b"]


class QwenLocalProvider(AIProvider):
    def __init__(self, model_name: str = "qwen3-vl-8b"):
        self._model_name = model_name
        self._endpoint = settings.qwen_local_endpoint

    @property
    def provider_name(self) -> str:
        return "qwen_local"

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

        async with httpx.AsyncClient(timeout=180.0) as client:
            try:
                resp = await client.post(
                    f"{self._endpoint}/chat/completions",
                    json={
                        "model": self._model_name,
                        "messages": messages,
                        "max_tokens": 4096,
                    },
                )
            except httpx.ConnectError as e:
                raise ServerError(f"Qwen local endpoint unreachable: {e}") from e

        if resp.status_code == 429:
            raise RateLimitError("Qwen local rate limited")
        if resp.status_code >= 500:
            raise ServerError(f"Qwen server error: {resp.status_code}")
        resp.raise_for_status()

        data = resp.json()
        text = data["choices"][0]["message"]["content"]
        usage_data = data.get("usage", {})
        usage = TokenUsage(
            input_tokens=usage_data.get("prompt_tokens", 0),
            output_tokens=usage_data.get("completion_tokens", 0),
        )
        return AIResponse(content=text, usage=usage, model=self._model_name)
