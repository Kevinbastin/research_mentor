"""OpenReview search provider - FREE, no API key needed, no rate limits."""

from __future__ import annotations

import json
import urllib.request
import urllib.parse
from typing import Any, List, Optional
from datetime import datetime

from .base_provider import SearchProvider, SearchResult, ProviderType, register_provider


class OpenReviewProvider(SearchProvider):
    """OpenReview provider for AI/ML conference papers.
    
    FREE - No API key required, no rate limits.
    """

    BASE_URL = "https://api.openreview.net"

    def __init__(self):
        super().__init__(name="openreview", provider_type=ProviderType.ACADEMIC)

    def is_available(self) -> bool:
        return True

    def search(
        self,
        query: str,
        limit: int = 10,
        from_year: Optional[int] = None,
        **kwargs: Any,
    ) -> List[SearchResult]:
        """Search OpenReview for papers matching query."""
        results = []
        
        try:
            params = {
                "term": query,
                "content": "all",
                "limit": min(limit * 3, 50),
                "sort": "cdate:desc",
            }
            
            url = f"{self.BASE_URL}/notes/search?" + urllib.parse.urlencode(params)
            
            req = urllib.request.Request(url, headers={
                "User-Agent": "AcademicResearchMentor/1.0",
                "Accept": "application/json",
            })
            
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            query_words = set(w.lower() for w in query.split() if len(w) > 2)
            
            for note in data.get("notes", []):
                content = note.get("content", {})
                
                title = self._get_val(content.get("title", ""))
                if not title or len(title) < 5:
                    continue
                
                abstract = self._get_val(content.get("abstract", ""))
                
                text_lower = (title + " " + abstract).lower()
                if not any(word in text_lower for word in query_words):
                    continue
                
                authors = self._get_val(content.get("authors", []))
                if isinstance(authors, str):
                    authors = [a.strip() for a in authors.split(",")]
                elif not isinstance(authors, list):
                    authors = []
                
                invitation = note.get("invitation", "")
                venue = self._get_venue(invitation)
                year = self._get_year(note.get("cdate"))
                
                note_id = note.get("id", note.get("forum", ""))
                paper_url = f"https://openreview.net/forum?id={note_id}"
                
                results.append(SearchResult(
                    title=str(title),
                    abstract=str(abstract)[:500] if abstract else "",
                    url=paper_url,
                    source="OpenReview",
                    year=year,
                    authors=authors[:10],
                    venue=venue,
                ))
                
                if len(results) >= limit:
                    break
                    
        except Exception as e:
            print(f"[OpenReview] Error: {e}")
        
        return results[:limit]

    def _get_val(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return obj.get("value", "")
        return obj if obj else ""

    def _get_year(self, cdate: Optional[int]) -> Optional[int]:
        if cdate:
            try:
                return datetime.fromtimestamp(cdate / 1000).year
            except:
                pass
        return None

    def _get_venue(self, invitation: str) -> str:
        inv_lower = invitation.lower()
        for v in ["NeurIPS", "ICLR", "ICML", "AAAI", "CVPR", "ACL"]:
            if v.lower() in inv_lower:
                return v
        return "OpenReview"


_provider = OpenReviewProvider()
register_provider(_provider)
