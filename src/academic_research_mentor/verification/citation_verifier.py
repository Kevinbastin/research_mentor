"""Citation verification - validates DOIs, arXiv IDs."""

from __future__ import annotations

import json
import re
import urllib.request
import urllib.parse
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class VerificationStatus(Enum):
    VERIFIED = "verified"
    PARTIAL = "partial"
    UNVERIFIED = "unverified"
    NOT_FOUND = "not_found"
    SYNTHETIC = "synthetic"


@dataclass
class VerifiedCitation:
    """A verified citation."""
    original_title: str
    verified_title: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    pubmed_id: Optional[str] = None
    url: str = ""
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    status: VerificationStatus = VerificationStatus.UNVERIFIED
    confidence: float = 0.0
    verification_source: str = ""
    issues: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_title": self.original_title,
            "verified_title": self.verified_title,
            "doi": self.doi,
            "arxiv_id": self.arxiv_id,
            "status": self.status.value,
            "confidence": self.confidence,
        }


class CitationVerifier:
    """Verifies citations against academic databases."""
    
    def __init__(self):
        self.verified_cache: Dict[str, VerifiedCitation] = {}
    
    def verify(self, title: str, authors: List[str] = None, year: int = None) -> VerifiedCitation:
        """Verify a citation exists."""
        cache_key = title.lower().strip()
        if cache_key in self.verified_cache:
            return self.verified_cache[cache_key]
        
        result = VerifiedCitation(original_title=title)
        
        # Try arXiv first
        arxiv_result = self._verify_arxiv(title)
        if arxiv_result and arxiv_result.status == VerificationStatus.VERIFIED:
            self.verified_cache[cache_key] = arxiv_result
            return arxiv_result
        
        # Try CrossRef
        crossref_result = self._verify_crossref(title, authors, year)
        if crossref_result and crossref_result.status == VerificationStatus.VERIFIED:
            self.verified_cache[cache_key] = crossref_result
            return crossref_result
        
        # Return best result
        if arxiv_result and arxiv_result.confidence > result.confidence:
            result = arxiv_result
        if crossref_result and crossref_result.confidence > result.confidence:
            result = crossref_result
        
        self.verified_cache[cache_key] = result
        return result
    
    def verify_arxiv_id(self, arxiv_id: str) -> VerifiedCitation:
        """Verify an arXiv ID exists."""
        result = VerifiedCitation(original_title="")
        arxiv_id = re.sub(r"^(arxiv:?)", "", arxiv_id, flags=re.IGNORECASE)
        
        try:
            url = "http://export.arxiv.org/api/query?id_list=" + arxiv_id
            req = urllib.request.Request(url, headers={"User-Agent": "ResearchMentor/1.0"})
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode("utf-8")
            
            import xml.etree.ElementTree as ET
            root = ET.fromstring(content)
            
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entry = root.find("atom:entry", ns)
            
            if entry is not None:
                title_elem = entry.find("atom:title", ns)
                if title_elem is not None and title_elem.text:
                    result.verified_title = " ".join(title_elem.text.split())
                    result.original_title = result.verified_title
                    result.arxiv_id = arxiv_id
                    result.url = "https://arxiv.org/abs/" + arxiv_id
                    result.status = VerificationStatus.VERIFIED
                    result.confidence = 1.0
                    result.verification_source = "arXiv"
                    
                    for author in entry.findall("atom:author", ns):
                        name_elem = author.find("atom:name", ns)
                        if name_elem is not None and name_elem.text:
                            result.authors.append(name_elem.text)
                    
                    published = entry.find("atom:published", ns)
                    if published is not None and published.text:
                        result.year = int(published.text[:4])
                else:
                    result.status = VerificationStatus.NOT_FOUND
            else:
                result.status = VerificationStatus.NOT_FOUND
                
        except Exception as e:
            result.status = VerificationStatus.UNVERIFIED
            result.issues.append("Error: " + str(e))
        
        return result
    
    def _verify_arxiv(self, title: str) -> Optional[VerifiedCitation]:
        """Search arXiv for a paper by title."""
        try:
            query = urllib.parse.quote('ti:"' + title + '"')
            url = "http://export.arxiv.org/api/query?search_query=" + query + "&max_results=3"
            
            req = urllib.request.Request(url, headers={"User-Agent": "ResearchMentor/1.0"})
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read().decode("utf-8")
            
            import xml.etree.ElementTree as ET
            root = ET.fromstring(content)
            
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            
            for entry in root.findall("atom:entry", ns):
                title_elem = entry.find("atom:title", ns)
                if title_elem is None or not title_elem.text:
                    continue
                
                found_title = " ".join(title_elem.text.split())
                similarity = self._title_similarity(title, found_title)
                
                if similarity > 0.8:
                    result = VerifiedCitation(original_title=title)
                    result.verified_title = found_title
                    result.status = VerificationStatus.VERIFIED
                    result.confidence = similarity
                    result.verification_source = "arXiv"
                    
                    for link in entry.findall("atom:link", ns):
                        href = link.get("href", "")
                        if "arxiv.org/abs/" in href:
                            result.arxiv_id = href.split("/abs/")[-1]
                            result.url = href
                            break
                    
                    for author in entry.findall("atom:author", ns):
                        name_elem = author.find("atom:name", ns)
                        if name_elem is not None and name_elem.text:
                            result.authors.append(name_elem.text)
                    
                    published = entry.find("atom:published", ns)
                    if published is not None and published.text:
                        result.year = int(published.text[:4])
                    
                    return result
            
            return None
            
        except Exception:
            return None
    
    def _verify_crossref(self, title: str, authors: List[str] = None, year: int = None) -> Optional[VerifiedCitation]:
        """Search CrossRef for a paper by title."""
        try:
            params = {"query.title": title, "rows": 3}
            if authors:
                params["query.author"] = authors[0]
            
            url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
            req = urllib.request.Request(url, headers={
                "User-Agent": "ResearchMentor/1.0 (mailto:research@example.com)"
            })
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            
            for item in data.get("message", {}).get("items", []):
                found_title = item.get("title", [""])[0]
                similarity = self._title_similarity(title, found_title)
                
                if similarity > 0.8:
                    result = VerifiedCitation(original_title=title)
                    result.verified_title = found_title
                    result.doi = item.get("DOI")
                    result.url = item.get("URL", "")
                    result.status = VerificationStatus.VERIFIED
                    result.confidence = similarity
                    result.verification_source = "CrossRef"
                    result.venue = item.get("container-title", [""])[0]
                    
                    for author in item.get("author", []):
                        name = (author.get("given", "") + " " + author.get("family", "")).strip()
                        if name:
                            result.authors.append(name)
                    
                    date_parts = item.get("published-print", {}).get("date-parts", [[]])
                    if date_parts and date_parts[0]:
                        result.year = date_parts[0][0]
                    
                    return result
            
            return None
            
        except Exception:
            return None
    
    def _title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity between two titles."""
        t1 = re.sub(r"[^\w\s]", "", title1.lower()).split()
        t2 = re.sub(r"[^\w\s]", "", title2.lower()).split()
        
        if not t1 or not t2:
            return 0.0
        
        set1 = set(t1)
        set2 = set(t2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
