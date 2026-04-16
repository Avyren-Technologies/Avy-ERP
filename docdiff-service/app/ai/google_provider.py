from google import genai
from google.genai import types

from app.ai.base import AIProvider, AIResponse, RateLimitError, ServerError, TokenUsage, ai_retry
from app.config import settings

AVAILABLE_MODELS = ["gemini-3.1-pro", "gemini-3-flash"]


class GoogleProvider(AIProvider):
    def __init__(self, model_name: str = "gemini-3.1-pro"):
        self._model_name = model_name
        self._client = genai.Client(api_key=settings.google_api_key)

    @property
    def provider_name(self) -> str:
        return "google"

    @property
    def model_name(self) -> str:
        return self._model_name

    @staticmethod
    def available_models() -> list[str]:
        return AVAILABLE_MODELS

    @ai_retry
    async def call(self, prompt: str, images: list[bytes] | None = None) -> AIResponse:
        contents = []
        if images:
            for img in images:
                contents.append(types.Part.from_bytes(data=img, mime_type="image/png"))
        contents.append(prompt)

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=contents,
            )
        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "rate" in error_str:
                raise RateLimitError(str(e)) from e
            if "500" in error_str or "503" in error_str:
                raise ServerError(str(e)) from e
            raise

        text = response.text or ""
        usage = TokenUsage()
        if response.usage_metadata:
            usage.input_tokens = response.usage_metadata.prompt_token_count or 0
            usage.output_tokens = response.usage_metadata.candidates_token_count or 0
        return AIResponse(content=text, usage=usage, model=self._model_name)
