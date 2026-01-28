"""HAL search provider - FREE, no API key needed."""

from __future__ import annotations

import json
import urllib.request
import urllib.parse
from typing import Any, List, Optional

from .base_provider import SearchProvider, SearchResult, ProviderType, register_provider


class HALProvider(SearchProvider):
    """HAL provider for French/European academic research.
    
    FREE - No API key required.
    HAL (Hyper Articles en Ligne) is a French open archive.
    """

    BASE_URL = "https://api.archives-ouvertes.fr/search"

    def __init__(self):
        super().__init__(name="hal", provider_type=ProviderType.ACADEMIC)

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
                "rows": min(limit, 20),
                "fl": "title_s,abstract_s,authFullName_s,producedDateY_i,uri_s,journalTitle_s,docType_s",
                "wt": "json",
            }
            
            if from_year:
                params["fq"] = f"producedDateY_i:[{from_year} TO *]"
            
            url = f"{self.BASE_URL}?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={"User-Agent": "AcademicResearchMentor/1.0"})
            
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            results = []
            for doc in data.get("response", {}).get("docs", [])[:limit]:
                # Handle title (can be list or string)
                title = doc.get("title_s", ["Unknown"])
                if isinstance(title, list):
                    title = title[0] if title else "Unknown"
                
                # Handle abstract
                abstract = doc.get("abstract_s", [""])
                if isinstance(abstract, list):
                    abstract = abstract[0] if abstract else ""
                
                # Handle authors
                authors = doc.get("authFullName_s", [])
                if isinstance(authors, str):
                    authors = [authors]
                
                year = doc.get("producedDateY_i")
                url = doc.get("uri_s", "")
                venue = doc.get("journalTitle_s", "HAL")
                
                results.append(SearchResult(
                    title=str(title),
                    abstract=str(abstract)[:500],
                    url=url,
                    source="hal",
                    year=year,
                    authors=authors[:5],
                    venue=venue,
                ))
            
            return results
            
        except Exception as e:
            print(f"[HAL] Error: {e}")
            return []


# Auto-register
_provider = HALProvider()
register_provider(_provider)
