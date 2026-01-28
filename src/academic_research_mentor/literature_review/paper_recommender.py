"""100% FREE Paper Recommender - No paid APIs, no rate limits.

Uses ONLY completely FREE APIs:
1. OpenAlex (FREE, no key, unlimited)
2. arXiv (FREE, no key, unlimited)
3. Unpaywall (FREE, just email)
4. CrossRef (FREE, polite pool)

NO Semantic Scholar (has 100 req/5min limit)
NO Tavily (PAID)
NO OpenRouter (PAID)
"""

from __future__ import annotations

import re
import httpx
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib.parse import quote


@dataclass
class RecommendedPaper:
    """A recommended similar paper with full metadata."""
    title: str
    authors: List[str]
    year: Optional[int]
    abstract: str
    url: str
    pdf_url: Optional[str]
    doi: Optional[str]
    arxiv_id: Optional[str]
    venue: Optional[str]
    citation_count: int
    similarity_score: float
    recommendation_reason: str
    source: str  # Which FREE API found it


class FREEPaperRecommender:
    """100% FREE paper recommendation engine - NO paid APIs."""
    
    # 100% FREE APIs
    OPENALEX_API = "https://api.openalex.org"  # FREE, no key, unlimited
    ARXIV_API = "https://export.arxiv.org/api/query"  # FREE, no key, unlimited
    UNPAYWALL_API = "https://api.unpaywall.org/v2"  # FREE, just email
    CROSSREF_API = "https://api.crossref.org/works"  # FREE, polite pool
    
    # Email for Unpaywall (required by TOS, but FREE)
    UNPAYWALL_EMAIL = "research-mentor@localhost"
    
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self._client = None
    
    def _get_client(self) -> httpx.Client:
        if self._client is None:
            headers = {
                "User-Agent": "AcademicResearchMentor/1.0 (mailto:research@localhost)",
            }
            self._client = httpx.Client(timeout=self.timeout, headers=headers)
        return self._client
    
    def find_similar(
        self,
        paper_id: str,
        limit: int = 10,
    ) -> List[RecommendedPaper]:
        """Find similar papers using 100% FREE APIs.
        
        Args:
            paper_id: DOI, arXiv ID, or paper title
            limit: Maximum recommendations
            
        Returns:
            List of recommended similar papers
        """
        recommendations = []
        
        # Determine ID type and search
        if paper_id.startswith("10."):
            # It's a DOI - use OpenAlex
            recommendations.extend(self._openalex_related_by_doi(paper_id, limit))
        elif re.match(r"^\d{4}\.\d{4,5}", paper_id):
            # It's an arXiv ID - use arXiv similar
            recommendations.extend(self._arxiv_similar(paper_id, limit))
            # Also try OpenAlex
            recommendations.extend(self._openalex_by_query(paper_id, limit // 2))
        else:
            # Treat as title/query - use OpenAlex search
            recommendations.extend(self._openalex_by_query(paper_id, limit))
        
        # Deduplicate and rank
        seen = set()
        unique = []
        for rec in recommendations:
            key = (rec.title.lower()[:50], rec.year)
            if key not in seen:
                seen.add(key)
                unique.append(rec)
        
        # Sort by citation count + similarity
        unique.sort(key=lambda x: (x.similarity_score, x.citation_count), reverse=True)
        return unique[:limit]
    
    def find_citing_papers(self, doi: str, limit: int = 10) -> List[RecommendedPaper]:
        """Find papers that cite a given paper using OpenAlex (FREE)."""
        return self._openalex_citing(doi, limit)
    
    def find_referenced_papers(self, doi: str, limit: int = 10) -> List[RecommendedPaper]:
        """Find papers referenced by a given paper using OpenAlex (FREE)."""
        return self._openalex_references(doi, limit)
    
    def _openalex_related_by_doi(self, doi: str, limit: int) -> List[RecommendedPaper]:
        """Get related works from OpenAlex (100% FREE)."""
        try:
            client = self._get_client()
            
            # Get work by DOI
            url = f"{self.OPENALEX_API}/works/doi:{doi}"
            resp = client.get(url)
            if resp.status_code != 200:
                return []
            
            work = resp.json()
            related_urls = work.get("related_works", [])[:limit]
            
            results = []
            for related_url in related_urls:
                work_id = related_url.split("/")[-1]
                rec = self._openalex_get_work(work_id, "related work")
                if rec:
                    results.append(rec)
            
            return results
            
        except Exception as e:
            print(f"[OpenAlex] Related works error: {e}")
            return []
    
    def _openalex_by_query(self, query: str, limit: int) -> List[RecommendedPaper]:
        """Search OpenAlex by text query (100% FREE)."""
        try:
            client = self._get_client()
            
            url = f"{self.OPENALEX_API}/works"
            params = {
                "search": query,
                "per_page": min(limit, 25),
                "sort": "relevance_score:desc",
            }
            resp = client.get(url, params=params)
            if resp.status_code != 200:
                return []
            
            data = resp.json()
            works = data.get("results", [])
            
            results = []
            for i, work in enumerate(works):
                score = 1.0 - (i * 0.03)
                rec = self._parse_openalex_work(work, score, "keyword match")
                results.append(rec)
            
            return results
            
        except Exception as e:
            print(f"[OpenAlex] Search error: {e}")
            return []
    
    def _openalex_citing(self, doi: str, limit: int) -> List[RecommendedPaper]:
        """Get papers citing this DOI using OpenAlex (FREE)."""
        try:
            client = self._get_client()
            
            # Get citing works
            url = f"{self.OPENALEX_API}/works"
            params = {
                "filter": f"cites:doi:{doi}",
                "per_page": min(limit, 25),
                "sort": "cited_by_count:desc",
            }
            resp = client.get(url, params=params)
            if resp.status_code != 200:
                return []
            
            data = resp.json()
            works = data.get("results", [])
            
            return [self._parse_openalex_work(w, 0.9, "cites this paper") for w in works]
            
        except Exception as e:
            print(f"[OpenAlex] Citing error: {e}")
            return []
    
    def _openalex_references(self, doi: str, limit: int) -> List[RecommendedPaper]:
        """Get papers referenced by this DOI using OpenAlex (FREE)."""
        try:
            client = self._get_client()
            
            # Get the work first
            url = f"{self.OPENALEX_API}/works/doi:{doi}"
            resp = client.get(url)
            if resp.status_code != 200:
                return []
            
            work = resp.json()
            ref_urls = work.get("referenced_works", [])[:limit]
            
            results = []
            for ref_url in ref_urls:
                work_id = ref_url.split("/")[-1]
                rec = self._openalex_get_work(work_id, "cited by this paper")
                if rec:
                    results.append(rec)
            
            return results
            
        except Exception as e:
            print(f"[OpenAlex] References error: {e}")
            return []
    
    def _openalex_get_work(self, work_id: str, reason: str) -> Optional[RecommendedPaper]:
        """Get a single OpenAlex work by ID (FREE)."""
        try:
            client = self._get_client()
            
            url = f"{self.OPENALEX_API}/works/{work_id}"
            resp = client.get(url)
            if resp.status_code != 200:
                return None
            
            work = resp.json()
            return self._parse_openalex_work(work, 0.85, reason)
            
        except Exception:
            return None
    
    def _parse_openalex_work(self, work: Dict, score: float, reason: str) -> RecommendedPaper:
        """Parse OpenAlex work to RecommendedPaper."""
        # Extract authors
        authors = []
        for authorship in work.get("authorships", [])[:10]:
            author = authorship.get("author", {})
            if author:
                authors.append(author.get("display_name", ""))
        
        # Get URLs
        primary_location = work.get("primary_location", {}) or {}
        source = primary_location.get("source", {}) or {}
        
        # Open access PDF
        oa_info = work.get("open_access", {}) or {}
        pdf_url = oa_info.get("oa_url")
        
        # DOI
        doi_full = work.get("doi", "")
        doi = doi_full.replace("https://doi.org/", "") if doi_full else None
        
        # Landing page
        url = doi_full or primary_location.get("landing_page_url", "")
        
        return RecommendedPaper(
            title=work.get("title", "Untitled") or "Untitled",
            authors=authors,
            year=work.get("publication_year"),
            abstract=work.get("abstract", "") or "",
            url=url,
            pdf_url=pdf_url,
            doi=doi,
            arxiv_id=None,  # Would need to extract from locations
            venue=source.get("display_name", ""),
            citation_count=work.get("cited_by_count", 0) or 0,
            similarity_score=score,
            recommendation_reason=reason,
            source="openalex",
        )
    
    def _arxiv_similar(self, arxiv_id: str, limit: int) -> List[RecommendedPaper]:
        """Find similar arXiv papers by category/keywords (100% FREE)."""
        try:
            import feedparser
            client = self._get_client()
            
            # Get the original paper first
            url = f"{self.ARXIV_API}?id_list={arxiv_id}"
            resp = client.get(url)
            if resp.status_code != 200:
                return []
            
            feed = feedparser.parse(resp.text)
            if not feed.entries:
                return []
            
            original = feed.entries[0]
            
            # Extract categories
            categories = [tag.get("term", "") for tag in original.get("tags", [])]
            primary_cat = categories[0] if categories else "cs.LG"
            
            # Extract key terms from title
            title = original.get("title", "")
            keywords = " ".join(title.split()[:5])
            
            # Search for similar
            search_url = f"{self.ARXIV_API}?search_query=cat:{primary_cat}+AND+all:{quote(keywords)}&max_results={limit}&sortBy=relevance"
            resp = client.get(search_url)
            if resp.status_code != 200:
                return []
            
            feed = feedparser.parse(resp.text)
            
            results = []
            for entry in feed.entries:
                entry_id = entry.get("id", "").split("/abs/")[-1].split("v")[0]
                if entry_id == arxiv_id:
                    continue  # Skip original
                
                authors = [a.get("name", "") for a in entry.get("authors", [])]
                
                # Extract year from published date
                published = entry.get("published", "")
                year = int(published[:4]) if published else None
                
                # Find PDF link
                pdf_link = None
                for link in entry.get("links", []):
                    if link.get("type") == "application/pdf":
                        pdf_link = link.get("href")
                        break
                
                if not pdf_link:
                    pdf_link = f"https://arxiv.org/pdf/{entry_id}.pdf"
                
                rec = RecommendedPaper(
                    title=entry.get("title", "").replace("\n", " "),
                    authors=authors,
                    year=year,
                    abstract=entry.get("summary", "").replace("\n", " "),
                    url=entry.get("id", ""),
                    pdf_url=pdf_link,
                    doi=None,
                    arxiv_id=entry_id,
                    venue="arXiv",
                    citation_count=0,  # arXiv doesn't have this
                    similarity_score=0.75,
                    recommendation_reason=f"same category ({primary_cat})",
                    source="arxiv",
                )
                results.append(rec)
            
            return results
            
        except Exception as e:
            print(f"[arXiv] Similar search error: {e}")
            return []
    
    def get_paper_with_links(self, paper_id: str) -> Optional[RecommendedPaper]:
        """Get a single paper with all links using FREE APIs."""
        try:
            # arXiv - always has PDF
            if re.match(r"^\d{4}\.\d{4,5}", paper_id):
                return RecommendedPaper(
                    title="",
                    authors=[],
                    year=None,
                    abstract="",
                    url=f"https://arxiv.org/abs/{paper_id}",
                    pdf_url=f"https://arxiv.org/pdf/{paper_id}.pdf",
                    doi=None,
                    arxiv_id=paper_id,
                    venue="arXiv",
                    citation_count=0,
                    similarity_score=1.0,
                    recommendation_reason="direct lookup",
                    source="arxiv",
                )
            
            # DOI - use OpenAlex (FREE)
            if paper_id.startswith("10."):
                client = self._get_client()
                url = f"{self.OPENALEX_API}/works/doi:{paper_id}"
                resp = client.get(url)
                if resp.status_code == 200:
                    work = resp.json()
                    return self._parse_openalex_work(work, 1.0, "direct lookup")
            
            # Title - search OpenAlex
            results = self._openalex_by_query(paper_id, 1)
            if results:
                return results[0]
            
            return None
            
        except Exception as e:
            print(f"[FREERecommender] Lookup error: {e}")
            return None


# Convenience functions using 100% FREE APIs
def find_similar_papers(paper_id: str, limit: int = 10) -> List[RecommendedPaper]:
    """Find papers similar to the given paper (100% FREE)."""
    recommender = FREEPaperRecommender()
    return recommender.find_similar(paper_id, limit)


def get_paper_pdf_link(paper_id: str) -> Optional[str]:
    """Get PDF link for a paper (100% FREE)."""
    recommender = FREEPaperRecommender()
    paper = recommender.get_paper_with_links(paper_id)
    return paper.pdf_url if paper else None


def get_citing_papers(paper_id: str, limit: int = 10) -> List[RecommendedPaper]:
    """Get papers that cite the given paper (100% FREE via OpenAlex)."""
    recommender = FREEPaperRecommender()
    if paper_id.startswith("10."):
        return recommender.find_citing_papers(paper_id, limit)
    return []


# Backwards compatibility - alias old class name
PaperRecommender = FREEPaperRecommender
