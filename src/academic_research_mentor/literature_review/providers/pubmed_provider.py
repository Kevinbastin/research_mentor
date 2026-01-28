"""PubMed Central search provider - FREE, no API key needed."""

from __future__ import annotations

import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Any, List, Optional

from .base_provider import SearchProvider, SearchResult, ProviderType, register_provider


class PubMedProvider(SearchProvider):
    """PubMed Central provider for medical/clinical research.
    
    FREE - No API key required (uses NCBI E-utilities).
    """

    SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    FETCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"

    def __init__(self):
        super().__init__(name="pubmed", provider_type=ProviderType.ACADEMIC)

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
            # Step 1: Search for IDs
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": min(limit, 20),
                "retmode": "json",
                "sort": "relevance",
            }
            
            if from_year:
                search_params["mindate"] = f"{from_year}/01/01"
                search_params["maxdate"] = "3000/12/31"
                search_params["datetype"] = "pdat"
            
            search_url = f"{self.SEARCH_URL}?" + urllib.parse.urlencode(search_params)
            req = urllib.request.Request(search_url, headers={"User-Agent": "AcademicResearchMentor/1.0"})
            
            with urllib.request.urlopen(req, timeout=15) as resp:
                search_data = json.loads(resp.read().decode("utf-8"))
            
            id_list = search_data.get("esearchresult", {}).get("idlist", [])
            if not id_list:
                return []
            
            # Step 2: Fetch details for IDs
            fetch_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "xml",
            }
            
            fetch_url = f"{self.FETCH_URL}?" + urllib.parse.urlencode(fetch_params)
            req = urllib.request.Request(fetch_url, headers={"User-Agent": "AcademicResearchMentor/1.0"})
            
            with urllib.request.urlopen(req, timeout=15) as resp:
                xml_data = resp.read().decode("utf-8")
            
            root = ET.fromstring(xml_data)
            results = []
            
            for article in root.findall(".//PubmedArticle"):
                medline = article.find(".//MedlineCitation")
                if medline is None:
                    continue
                
                # Extract PMID
                pmid = medline.findtext("PMID", "")
                
                # Extract title
                title_elem = medline.find(".//ArticleTitle")
                title = "".join(title_elem.itertext()) if title_elem is not None else "Unknown"
                
                # Extract abstract
                abstract_elem = medline.find(".//Abstract/AbstractText")
                abstract = "".join(abstract_elem.itertext()) if abstract_elem is not None else ""
                
                # Extract authors
                authors = []
                for author in medline.findall(".//Author"):
                    lastname = author.findtext("LastName", "")
                    forename = author.findtext("ForeName", "")
                    if lastname:
                        authors.append(f"{forename} {lastname}".strip())
                
                # Extract year
                year = None
                pub_date = medline.find(".//PubDate")
                if pub_date is not None:
                    year_text = pub_date.findtext("Year")
                    if year_text and year_text.isdigit():
                        year = int(year_text)
                
                # Extract journal
                journal = medline.findtext(".//Journal/Title", "PubMed")
                
                url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                
                results.append(SearchResult(
                    title=title,
                    abstract=abstract[:500],
                    url=url,
                    source="pubmed",
                    year=year,
                    authors=authors[:5],
                    venue=journal,
                ))
            
            return results[:limit]
            
        except Exception as e:
            print(f"[PubMed] Error: {e}")
            return []


# Auto-register
_provider = PubMedProvider()
register_provider(_provider)
