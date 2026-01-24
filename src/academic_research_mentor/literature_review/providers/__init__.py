"""Search providers package for multi-source literature discovery."""

from .base_provider import (
    SearchProvider,
    SearchResult,
    ProviderType,
    ProviderRegistry,
    get_registry,
    register_provider,
)

# Import providers to auto-register them
from . import arxiv_provider
from . import semantic_scholar_provider
from . import tavily_provider

__all__ = [
    "SearchProvider",
    "SearchResult",
    "ProviderType",
    "ProviderRegistry",
    "get_registry",
    "register_provider",
]