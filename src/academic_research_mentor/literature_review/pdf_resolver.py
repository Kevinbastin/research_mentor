"""100% FREE PDF Link Resolver - No paid APIs.

Uses ONLY completely FREE APIs:
1. arXiv (FREE, always has PDF)
2. Unpaywall (FREE, just needs email, best OA database)
3. OpenAlex (FREE, has OA links)
4. PubMed Central (FREE for PMC papers)

NO Semantic Scholar (rate limited)
NO paid APIs
"""

from __future__ import annotations

import re
import httpx
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ResolvedPaper:
    """Paper with all resolved links."""
    title: str
    doi: Optional[str]
    arxiv_id: Optional[str]
    pmc_id: Optional[str]
    
    # Links
    pdf_url: Optional[str]
    html_url: Optional[str]
    landing_page: Optional[str]
    
    # Metadata
    is_open_access: bool
    oa_status: str  # gold, green, bronze, hybrid, closed
    license: Optional[str]
    source: str  # Which FREE resolver found the PDF


class FREEPDFResolver:
    """100% FREE PDF link resolver - NO paid APIs."""
    
    # 100% FREE APIs
    UNPAYWALL_API = "https://api.unpaywall.org/v2"  # FREE, just email
    UNPAYWALL_EMAIL = "research-mentor@localhost"
    
    OPENALEX_API = "https://api.openalex.org"  # FREE, no key
    
    ARXIV_PDF_BASE = "https://arxiv.org/pdf"
    ARXIV_ABS_BASE = "https://arxiv.org/abs"
    
    PMC_PDF_BASE = "https://www.ncbi.nlm.nih.gov/pmc/articles"
    
    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
        self._client = None
    
    def _get_client(self) -> httpx.Client:
        if self._client is None:
            headers = {
                "User-Agent": "AcademicResearchMentor/1.0 (mailto:research@localhost)",
            }
            self._client = httpx.Client(timeout=self.timeout, headers=headers)
        return self._client
    
    def resolve(
        self,
        doi: Optional[str] = None,
        arxiv_id: Optional[str] = None,
        title: Optional[str] = None,
        pmc_id: Optional[str] = None,
    ) -> Optional[ResolvedPaper]:
        """Resolve PDF link using 100% FREE APIs.
        
        Priority:
        1. arXiv (if arxiv_id) - Always has FREE PDF
        2. PMC (if pmc_id) - Always has FREE PDF
        3. Unpaywall (if DOI) - Best FREE open access database
        4. OpenAlex (if DOI) - FREE backup
        """
        resolved = None
        
        # 1. arXiv - guaranteed FREE PDF
        if arxiv_id:
            resolved = self._resolve_arxiv(arxiv_id)
            if resolved and resolved.pdf_url:
                return resolved
        
        # 2. PMC - guaranteed FREE PDF
        if pmc_id:
            resolved = self._resolve_pmc(pmc_id)
            if resolved and resolved.pdf_url:
                return resolved
        
        # 3. Unpaywall - best FREE open access database
        if doi:
            resolved = self._resolve_unpaywall(doi)
            if resolved and resolved.pdf_url:
                return resolved
        
        # 4. OpenAlex - FREE backup
        if doi:
            resolved = self._resolve_openalex(doi)
            if resolved and resolved.pdf_url:
                return resolved
        
        return resolved
    
    def _resolve_arxiv(self, arxiv_id: str) -> ResolvedPaper:
        """Resolve arXiv paper - always has FREE PDF."""
        # Clean arxiv ID
        arxiv_id = arxiv_id.replace("arXiv:", "").strip()
        base_id = re.sub(r"v\d+$", "", arxiv_id)
        
        return ResolvedPaper(
            title="",
            doi=None,
            arxiv_id=base_id,
            pmc_id=None,
            pdf_url=f"{self.ARXIV_PDF_BASE}/{base_id}.pdf",
            html_url=f"{self.ARXIV_ABS_BASE}/{base_id}",
            landing_page=f"{self.ARXIV_ABS_BASE}/{base_id}",
            is_open_access=True,
            oa_status="green",
            license="arXiv",
            source="arxiv",
        )
    
    def _resolve_pmc(self, pmc_id: str) -> ResolvedPaper:
        """Resolve PMC paper - always has FREE PDF."""
        pmc_id = pmc_id.replace("PMC", "").strip()
        
        return ResolvedPaper(
            title="",
            doi=None,
            arxiv_id=None,
            pmc_id=f"PMC{pmc_id}",
            pdf_url=f"{self.PMC_PDF_BASE}/PMC{pmc_id}/pdf/",
            html_url=f"{self.PMC_PDF_BASE}/PMC{pmc_id}/",
            landing_page=f"{self.PMC_PDF_BASE}/PMC{pmc_id}/",
            is_open_access=True,
            oa_status="gold",
            license="PMC",
            source="pmc",
        )
    
    def _resolve_unpaywall(self, doi: str) -> Optional[ResolvedPaper]:
        """Resolve via Unpaywall - 100% FREE, best OA database."""
        try:
            client = self._get_client()
            
            # Clean DOI
            doi = doi.replace("https://doi.org/", "").replace("http://doi.org/", "")
            
            url = f"{self.UNPAYWALL_API}/{doi}"
            params = {"email": self.UNPAYWALL_EMAIL}
            
            resp = client.get(url, params=params)
            if resp.status_code != 200:
                return None
            
            data = resp.json()
            best_oa = data.get("best_oa_location", {}) or {}
            
            return ResolvedPaper(
                title=data.get("title", ""),
                doi=doi,
                arxiv_id=None,
                pmc_id=None,
                pdf_url=best_oa.get("url_for_pdf"),
                html_url=best_oa.get("url"),
                landing_page=data.get("doi_url"),
                is_open_access=data.get("is_oa", False),
                oa_status=data.get("oa_status", "closed"),
                license=best_oa.get("license"),
                source="unpaywall",
            )
            
        except Exception as e:
            print(f"[Unpaywall] Error: {e}")
            return None
    
    def _resolve_openalex(self, doi: str) -> Optional[ResolvedPaper]:
        """Resolve via OpenAlex - 100% FREE."""
        try:
            client = self._get_client()
            
            url = f"{self.OPENALEX_API}/works/doi:{doi}"
            resp = client.get(url)
            if resp.status_code != 200:
                return None
            
            data = resp.json()
            oa_info = data.get("open_access", {}) or {}
            
            return ResolvedPaper(
                title=data.get("title", ""),
                doi=doi,
                arxiv_id=None,
                pmc_id=None,
                pdf_url=oa_info.get("oa_url"),
                html_url=None,
                landing_page=data.get("doi"),
                is_open_access=oa_info.get("is_oa", False),
                oa_status=oa_info.get("oa_status", "closed"),
                license=None,
                source="openalex",
            )
            
        except Exception as e:
            print(f"[OpenAlex] Error: {e}")
            return None


# Convenience functions - 100% FREE
def get_pdf_link(
    doi: Optional[str] = None,
    arxiv_id: Optional[str] = None,
    pmc_id: Optional[str] = None,
) -> Optional[str]:
    """Get PDF link for a paper (100% FREE)."""
    resolver = FREEPDFResolver()
    paper = resolver.resolve(doi=doi, arxiv_id=arxiv_id, pmc_id=pmc_id)
    return paper.pdf_url if paper else None


def is_open_access(doi: str) -> bool:
    """Check if a paper is open access (100% FREE via Unpaywall)."""
    resolver = FREEPDFResolver()
    paper = resolver.resolve(doi=doi)
    return paper.is_open_access if paper else False


def get_all_links(
    doi: Optional[str] = None,
    arxiv_id: Optional[str] = None,
) -> Dict[str, Optional[str]]:
    """Get all available links for a paper (100% FREE)."""
    resolver = FREEPDFResolver()
    paper = resolver.resolve(doi=doi, arxiv_id=arxiv_id)
    
    if not paper:
        return {}
    
    return {
        "pdf_url": paper.pdf_url,
        "html_url": paper.html_url,
        "landing_page": paper.landing_page,
        "is_open_access": paper.is_open_access,
        "oa_status": paper.oa_status,
        "license": paper.license,
    }


# Backwards compatibility
PDFLinkResolver = FREEPDFResolver
