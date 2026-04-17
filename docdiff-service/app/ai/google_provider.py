from google import genai
from google.genai import types

from app.ai.base import AIProvider, AIResponse, RateLimitError, ServerError, TokenUsage, ai_retry
from app.config import settings

AVAILABLE_MODELS = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-lite-001",
]


class GoogleProvider(AIProvider):
    def __init__(self, model_name: str = "gemini-2.5-flash"):
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
    async def call(self, prompt: str, images: list[bytes] | None = None, system: str | None = None) -> AIResponse:
        contents = []
        if images:
            for img in images:
                contents.append(types.Part.from_bytes(data=img, mime_type="image/png"))
        contents.append(prompt)

        # Adaptive generation config based on whether this is extraction (needs more tokens)
        # or classification (needs fewer tokens). Detect by image presence.
        is_extraction = images is not None and len(images) > 0
        generation_config = types.GenerateContentConfig(
            temperature=0.1,
            max_output_tokens=8192 if is_extraction else 512,
            response_mime_type="application/json",
        )
        if system:
            generation_config.system_instruction = system

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model_name,
                contents=contents,
                config=generation_config,
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
