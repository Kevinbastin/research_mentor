"""Tavily search provider for real-time web search."""

from __future__ import annotations

import os
from typing import Any, List, Optional

from .base_provider import SearchProvider, SearchResult, ProviderType, register_provider


class TavilyProvider(SearchProvider):
    """Tavily API provider for real-time web search.
    
    Tavily provides AI-optimized search results with high-quality
    summaries and academic content filtering.
    """

    def __init__(self):
        super().__init__(name="tavily", provider_type=ProviderType.WEB)
        self._api_key = os.getenv("TAVILY_API_KEY")
        self._client = None

    def _get_client(self):
        """Lazy initialization of Tavily client."""
        if self._client is None and self._api_key:
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=self._api_key)
            except ImportError:
                print("Tavily package not installed. Run: pip install tavily-python")
                return None
        return self._client

    def is_available(self) -> bool:
        """Check if Tavily API key is configured."""
        return bool(self._api_key)

    def search(
        self,
        query: str,
        limit: int = 10,
        from_year: Optional[int] = None,
        search_depth: str = "advanced",
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None,
        **kwargs: Any,
    ) -> List[SearchResult]:
        """Execute Tavily search.
        
        Args:
            query: Search query
            limit: Maximum results (max 20 for Tavily)
            from_year: Not directly supported, but helps filter results
            search_depth: "basic" or "advanced" (more thorough)
            include_domains: Limit to specific domains
            exclude_domains: Exclude specific domains
            
        Returns:
            List of SearchResult objects
        """
        client = self._get_client()
        if not client:
            return []

        # Enhance query with year filter if specified
        enhanced_query = query
        if from_year:
            enhanced_query = f"{query} after:{from_year}"

        # Academic domains to prioritize
        academic_domains = include_domains or [
            "arxiv.org",
            "scholar.google.com",
            "semanticscholar.org",
            "openreview.net",
            "acm.org",
            "ieee.org",
            "nature.com",
            "sciencedirect.com",
        ]

        try:
            response = client.search(
                query=enhanced_query,
                search_depth=search_depth,
                max_results=min(limit, 20),  # Tavily max is 20
                include_domains=academic_domains if not include_domains else include_domains,
                exclude_domains=exclude_domains,
            )

            results = []
            for item in response.get("results", []):
                result = SearchResult(
                    title=item.get("title", "Untitled"),
                    abstract=item.get("content", "")[:500],  # Truncate long content
                    url=item.get("url", ""),
                    source="tavily",
                    relevance_score=item.get("score"),
                    metadata={
                        "raw_content": item.get("raw_content"),
                    },
                )
                results.append(result)

            return results

        except Exception as e:
            print(f"[Tavily] Search error: {e}")
            return []


# Auto-register when module is imported
def _register():
    provider = TavilyProvider()
    if provider.is_available():
        register_provider(provider)


_register()