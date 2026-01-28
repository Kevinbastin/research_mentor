"""Search providers package - 100% FREE providers only."""

from .base_provider import (
    SearchProvider,
    SearchResult,
    ProviderType,
    ProviderRegistry,
    get_registry,
    register_provider,
)

# Import FREE provider classes
from .arxiv_provider import ArxivProvider
from .openreview_provider import OpenReviewProvider
from .pubmed_provider import PubMedProvider
from .hal_provider import HALProvider
from .zenodo_provider import ZenodoProvider

__all__ = [
    "SearchProvider",
    "SearchResult",
    "ProviderType",
    "ProviderRegistry",
    "get_registry",
    "register_provider",
    "ArxivProvider",
    "OpenReviewProvider",
    "PubMedProvider",
    "HALProvider",
    "ZenodoProvider",
]
