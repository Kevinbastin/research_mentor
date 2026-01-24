"""Search provider abstraction layer for multi-source literature discovery."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ProviderType(Enum):
    """Types of search providers."""
    ACADEMIC = "academic"      # arXiv, Semantic Scholar, OpenReview
    WEB = "web"               # Tavily, Google Scholar
    HYBRID = "hybrid"         # MCP, custom


@dataclass
class SearchResult:
    """Unified search result from any provider."""
    title: str
    abstract: str
    url: str
    source: str
    year: Optional[int] = None
    authors: List[str] = field(default_factory=list)
    citations: Optional[int] = None
    venue: Optional[str] = None
    relevance_score: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "abstract": self.abstract,
            "url": self.url,
            "source": self.source,
            "year": self.year,
            "authors": self.authors,
            "citations": self.citations,
            "venue": self.venue,
            "relevance_score": self.relevance_score,
            **self.metadata,
        }


class SearchProvider(ABC):
    """Abstract base class for all search providers."""

    def __init__(self, name: str, provider_type: ProviderType):
        self.name = name
        self.provider_type = provider_type
        self._enabled = True

    @property
    def enabled(self) -> bool:
        """Check if provider is enabled."""
        return self._enabled

    def enable(self) -> None:
        """Enable this provider."""
        self._enabled = True

    def disable(self) -> None:
        """Disable this provider."""
        self._enabled = False

    @abstractmethod
    def search(
        self,
        query: str,
        limit: int = 10,
        from_year: Optional[int] = None,
        **kwargs: Any,
    ) -> List[SearchResult]:
        """Execute a search query.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            from_year: Filter results from this year onwards
            **kwargs: Provider-specific options
            
        Returns:
            List of SearchResult objects
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Check if this provider is available (API keys configured, etc.)."""
        pass

    def get_config(self) -> Dict[str, Any]:
        """Return provider configuration (for debugging/logging)."""
        return {
            "name": self.name,
            "type": self.provider_type.value,
            "enabled": self.enabled,
            "available": self.is_available(),
        }


class ProviderRegistry:
    """Registry of all available search providers."""

    def __init__(self):
        self._providers: Dict[str, SearchProvider] = {}

    def register(self, provider: SearchProvider) -> None:
        """Register a new provider."""
        self._providers[provider.name] = provider

    def get(self, name: str) -> Optional[SearchProvider]:
        """Get a provider by name."""
        return self._providers.get(name)

    def get_all(self) -> List[SearchProvider]:
        """Get all registered providers."""
        return list(self._providers.values())

    def get_enabled(self) -> List[SearchProvider]:
        """Get all enabled providers."""
        return [p for p in self._providers.values() if p.enabled]

    def get_available(self) -> List[SearchProvider]:
        """Get all enabled and available providers."""
        return [p for p in self._providers.values() if p.enabled and p.is_available()]

    def get_by_type(self, provider_type: ProviderType) -> List[SearchProvider]:
        """Get providers by type."""
        return [p for p in self._providers.values() if p.provider_type == provider_type]

    def search_all(
        self,
        query: str,
        limit_per_provider: int = 10,
        from_year: Optional[int] = None,
        provider_types: Optional[List[ProviderType]] = None,
    ) -> Dict[str, List[SearchResult]]:
        """Execute search across all available providers.
        
        Args:
            query: Search query string
            limit_per_provider: Max results per provider
            from_year: Filter results from this year
            provider_types: Optional filter by provider type
            
        Returns:
            Dict mapping provider name to list of results
        """
        results: Dict[str, List[SearchResult]] = {}
        
        providers = self.get_available()
        if provider_types:
            providers = [p for p in providers if p.provider_type in provider_types]
        
        for provider in providers:
            try:
                provider_results = provider.search(
                    query=query,
                    limit=limit_per_provider,
                    from_year=from_year,
                )
                results[provider.name] = provider_results
            except Exception as e:
                print(f"[{provider.name}] Search failed: {e}")
                results[provider.name] = []
        
        return results

    def __len__(self) -> int:
        return len(self._providers)


# Global registry instance
_registry = ProviderRegistry()


def get_registry() -> ProviderRegistry:
    """Get the global provider registry."""
    return _registry


def register_provider(provider: SearchProvider) -> None:
    """Register a provider in the global registry."""
    _registry.register(provider)