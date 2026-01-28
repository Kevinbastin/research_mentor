"""Zenodo search provider - FREE, no API key needed."""

from __future__ import annotations

import json
import urllib.request
import urllib.parse
from typing import Any, List, Optional

from .base_provider import SearchProvider, SearchResult, ProviderType, register_provider


class ZenodoProvider(SearchProvider):
    """Zenodo provider for research data, datasets, and supplements.
    
    FREE - No API key required.
    Zenodo is a general-purpose open repository by CERN.
    """

    BASE_URL = "https://zenodo.org/api/records"

    def __init__(self):
        super().__init__(name="zenodo", provider_type=ProviderType.ACADEMIC)

    def is_available(self) -> bool:
        return True

    def search(
        self,
        query: str,
        limit: int = 10,
        from_year: Optional[int] = None,
        **kwargs: Any,
    ) -> List[SearchResult]:
        try:
            params = {
                "q": query,
                "size": min(limit, 20),
                "sort": "bestmatch",
                "type": "publication",  # Focus on publications
            }
            
            url = f"{self.BASE_URL}?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={"User-Agent": "AcademicResearchMentor/1.0"})
            
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            results = []
            for hit in data.get("hits", {}).get("hits", [])[:limit]:
                metadata = hit.get("metadata", {})
                
                title = metadata.get("title", "Unknown")
                description = metadata.get("description", "")
                # Strip HTML tags from description
                import re
                description = re.sub(r"<[^>]+>", "", description)
                
                # Extract authors
                authors = []
                for creator in metadata.get("creators", []):
                    name = creator.get("name", "")
                    if name:
                        authors.append(name)
                
                # Extract year
                year = None
                pub_date = metadata.get("publication_date", "")
                if pub_date and len(pub_date) >= 4:
                    try:
                        year = int(pub_date[:4])
                    except:
                        pass
                
                # Filter by year if specified
                if from_year and year and year < from_year:
                    continue
                
                url = hit.get("links", {}).get("html", f"https://zenodo.org/record/{hit.get(id, )}")
                
                results.append(SearchResult(
                    title=title,
                    abstract=description[:500],
                    url=url,
                    source="zenodo",
                    year=year,
                    authors=authors[:5],
                    venue="Zenodo",
                ))
            
            return results
            
        except Exception as e:
            print(f"[Zenodo] Error: {e}")
            return []


# Auto-register
_provider = ZenodoProvider()
register_provider(_provider)
