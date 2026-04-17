import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger("docdiff.ai")


@dataclass
class TokenUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    cost_estimate: float = 0.0


@dataclass
class AIResponse:
    content: str
    usage: TokenUsage = field(default_factory=TokenUsage)
    model: str = ""


class RateLimitError(Exception):
    """Raised on 429 or rate limit errors — triggers retry."""

class ServerError(Exception):
    """Raised on 5xx errors — triggers retry."""

ai_retry = retry(
    retry=retry_if_exception_type((RateLimitError, ServerError, TimeoutError)),
    stop=stop_after_attempt(6),
    wait=wait_exponential(multiplier=3, min=5, max=60),
    before_sleep=lambda rs: logger.warning(
        f"AI call failed (attempt {rs.attempt_number}), retrying: {rs.outcome.exception()}"
    ),
)


class AIProvider(ABC):
    @abstractmethod
    async def call(self, prompt: str, images: list[bytes] | None = None) -> AIResponse:
        ...

    @property
    @abstractmethod
    def provider_name(self) -> str:
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        ...

    @property
    def supports_vision(self) -> bool:
        return True

    async def extract_page_content(self, image: bytes, prompt: str) -> AIResponse:
        return await self.call(prompt, images=[image])

    async def classify_difference(self, context: str, prompt: str) -> AIResponse:
        return await self.call(f"{prompt}\n\n{context}")

    async def transcribe_handwriting(self, image: bytes, prompt: str) -> AIResponse:
        return await self.call(prompt, images=[image])
