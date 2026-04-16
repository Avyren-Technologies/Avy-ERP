import logging
from app.ai.base import AIProvider
from app.config import settings

logger = logging.getLogger("docdiff.ai")

_providers: dict[str, type[AIProvider]] = {}


def register_provider(name: str, provider_cls: type[AIProvider]):
    _providers[name] = provider_cls


def get_provider(provider_name: str, model_name: str) -> AIProvider:
    if provider_name not in _providers:
        raise ValueError(
            f"Unknown provider: {provider_name}. Available: {list(_providers.keys())}"
        )
    provider_cls = _providers[provider_name]
    return provider_cls(model_name=model_name)


def get_default_provider() -> AIProvider:
    return get_provider(settings.default_provider, settings.default_model)


def list_available_providers() -> list[dict]:
    providers = []
    for name, cls in _providers.items():
        providers.append({
            "provider": name,
            "models": cls.available_models() if hasattr(cls, "available_models") else [],
        })
    return providers
