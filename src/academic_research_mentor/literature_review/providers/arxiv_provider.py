"""Enhanced arXiv search provider wrapping existing arxiv_search functionality."""

from __future__ import annotations

import os
from typing import Any, List, Optional

from .base_provider import SearchProvider, SearchResult, ProviderType, register_provider


class ArxivProvider(SearchProvider):
    """Enhanced arXiv provider using existing arxiv_search infrastructure.
    
    Wraps the legacy arxiv_search function with the new provider interface.
    """

    def __init__(self):
        super().__init__(name="arxiv", provider_type=ProviderType.ACADEMIC)

    def is_available(self) -> bool:
        """arXiv is always available (no API key required)."""
        return True

    def search(
        self,
        query: str,
        limit: int = 10,
        from_year: Optional[int] = None,
        sort_by: str = "relevance",
        **kwargs: Any,
    ) -> List[SearchResult]:
        """Search arXiv for papers.
        
        Args:
            query: Search query
            limit: Maximum results (max 25)
            from_year: Filter papers from this year onwards
            sort_by: "relevance" or "date"
            
        Returns:
            List of SearchResult objects
        """
        try:
            from ...mentor_tools import arxiv_search
            import re
            
            response = arxiv_search(
                query=query,
                from_year=from_year,
                limit=min(limit, 25),
                sort_by=sort_by,
            )
            
            results = []
            for paper in response.get("papers", []):
                url = paper.get("url", "")
                
                # Extract arXiv ID from URL (e.g., https://arxiv.org/abs/2307.01189v2)
                arxiv_id = None
                if "/abs/" in url:
                    arxiv_id = url.split("/abs/")[-1].split("v")[0]  # Remove version
                
                # Generate PDF URL
                pdf_url = None
                if arxiv_id:
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
                
                result = SearchResult(
                    title=paper.get("title", "Untitled"),
                    abstract=paper.get("abstract", paper.get("summary", "")),
                    url=url,
                    source="arxiv",
                    year=paper.get("year"),
                    authors=paper.get("authors", []),
                    venue=paper.get("venue", "arXiv"),
                    metadata={
                        "arxiv_id": arxiv_id,
                        "pdf_url": pdf_url,
                        "categories": paper.get("categories", []),
                    },
                )
                results.append(result)
            
            return results

        except Exception as e:
            print(f"[arXiv] Search error: {e}")
            return []


# Auto-register when module is imported
# Auto-register
_register_instance = ArxivProvider()
register_provider(_register_instance)

def _register_unused():
    provider = ArxivProvider()
    register_provider(provider)


