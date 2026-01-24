"""Semantic Scholar API provider for academic paper search."""

from __future__ import annotations

import os
import time
from typing import Any, List, Optional
import urllib.request
import urllib.parse
import json

from .base_provider import SearchProvider, SearchResult, ProviderType, register_provider


class SemanticScholarProvider(SearchProvider):
    """Semantic Scholar API provider for academic paper search.
    
    Uses the free Semantic Scholar API (with optional API key for higher rate limits).
    Provides rich paper metadata including citations, authors, and venues.
    """

    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    # Rate limiting
    REQUESTS_PER_SECOND = 5  # With API key: 100/sec, without: 5/sec

    def __init__(self):
        super().__init__(name="semantic_scholar", provider_type=ProviderType.ACADEMIC)
        self._api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self._last_request_time = 0

    def is_available(self) -> bool:
        """Always available (free tier exists), but works better with API key."""
        return True

    def _rate_limit(self):
        """Enforce rate limiting."""
        current_time = time.time()
        min_interval = 1.0 / self.REQUESTS_PER_SECOND
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < min_interval:
            time.sleep(min_interval - time_since_last)
        
        self._last_request_time = time.time()

    def _make_request(self, endpoint: str, params: dict) -> dict:
        """Make API request with rate limiting."""
        self._rate_limit()
        
        url = f"{self.BASE_URL}/{endpoint}?{urllib.parse.urlencode(params)}"
        
        headers = {"Accept": "application/json"}
        if self._api_key:
            headers["x-api-key"] = self._api_key
        
        request = urllib.request.Request(url, headers=headers)
        
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            print(f"[Semantic Scholar] API error: {e}")
            return {}

    def search(
        self,
        query: str,
        limit: int = 10,
        from_year: Optional[int] = None,
        fields_of_study: Optional[List[str]] = None,
        open_access_only: bool = False,
        **kwargs: Any,
    ) -> List[SearchResult]:
        """Search Semantic Scholar for papers.
        
        Args:
            query: Search query
            limit: Maximum results (max 100)
            from_year: Filter papers from this year onwards
            fields_of_study: Filter by fields (e.g., "Computer Science")
            open_access_only: Only return open access papers
            
        Returns:
            List of SearchResult objects
        """
        params = {
            "query": query,
            "limit": min(limit, 100),
            "fields": "title,abstract,url,year,authors,venue,citationCount,openAccessPdf",
        }
        
        if from_year:
            params["year"] = f"{from_year}-"  # Year range: from_year to present
        
        if fields_of_study:
            params["fieldsOfStudy"] = ",".join(fields_of_study)
        
        if open_access_only:
            params["openAccessPdf"] = ""

        response = self._make_request("paper/search", params)
        
        results = []
        for paper in response.get("data", []):
            # Get PDF URL if available
            pdf_url = None
            if paper.get("openAccessPdf"):
                pdf_url = paper["openAccessPdf"].get("url")
            
            # Handle authors list
            authors = [
                author.get("name", "") 
                for author in paper.get("authors", [])
            ]
            
            result = SearchResult(
                title=paper.get("title", "Untitled"),
                abstract=paper.get("abstract", "No abstract available"),
                url=pdf_url or f"https://www.semanticscholar.org/paper/{paper.get('paperId', '')}",
                source="semantic_scholar",
                year=paper.get("year"),
                authors=authors,
                citations=paper.get("citationCount"),
                venue=paper.get("venue"),
                metadata={
                    "paper_id": paper.get("paperId"),
                    "open_access": bool(pdf_url),
                },
            )
            results.append(result)

        return results

    def get_paper_details(self, paper_id: str) -> Optional[SearchResult]:
        """Get detailed information about a specific paper."""
        params = {
            "fields": "title,abstract,url,year,authors,venue,citationCount,references,citations,openAccessPdf",
        }
        
        response = self._make_request(f"paper/{paper_id}", params)
        
        if not response:
            return None
        
        authors = [
            author.get("name", "") 
            for author in response.get("authors", [])
        ]
        
        pdf_url = None
        if response.get("openAccessPdf"):
            pdf_url = response["openAccessPdf"].get("url")
        
        return SearchResult(
            title=response.get("title", "Untitled"),
            abstract=response.get("abstract", ""),
            url=pdf_url or f"https://www.semanticscholar.org/paper/{paper_id}",
            source="semantic_scholar",
            year=response.get("year"),
            authors=authors,
            citations=response.get("citationCount"),
            venue=response.get("venue"),
            metadata={
                "paper_id": paper_id,
                "reference_count": len(response.get("references", [])),
                "citation_count": response.get("citationCount", 0),
                "open_access": bool(pdf_url),
            },
        )


# Auto-register when module is imported
def _register():
    provider = SemanticScholarProvider()
    register_provider(provider)


_register()