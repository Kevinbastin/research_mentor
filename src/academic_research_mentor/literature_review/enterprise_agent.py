"""Enterprise-grade Academic Research Agent.

Combines all features for production-ready research:
1. Multi-provider search (5 FREE academic sources)
2. Citation verification (DOI/arXiv validation)
3. Evidence grading (A-F with confidence scores)
4. Similar paper recommendations
5. PDF link resolution
6. Structured output with full metadata
"""

from __future__ import annotations

import os
import json
import hashlib
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set

from .paper_recommender import PaperRecommender, RecommendedPaper
from .pdf_resolver import PDFLinkResolver, ResolvedPaper


@dataclass
class EnterpriseSource:
    """Enterprise-grade source with full metadata."""
    # Core identifiers
    title: str
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    pmc_id: Optional[str] = None
    
    # Metadata
    authors: List[str] = field(default_factory=list)
    year: Optional[int] = None
    venue: Optional[str] = None
    abstract: str = ""
    
    # Links (all resolved)
    url: str = ""
    pdf_url: Optional[str] = None
    html_url: Optional[str] = None
    
    # Verification
    is_verified: bool = False
    verification_method: str = "none"
    
    # Evidence quality
    evidence_grade: str = "D"
    evidence_score: float = 0.0
    confidence: float = 0.0
    
    # Citations
    citation_count: int = 0
    
    # Open access
    is_open_access: bool = False
    oa_status: str = "unknown"
    
    # Source provider
    provider: str = "unknown"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExtractedClaim:
    """A claim extracted from research with source linking."""
    claim_text: str
    value: Optional[float] = None
    unit: str = ""
    metric_name: str = ""
    
    # Source linking
    source_title: str = ""
    source_doi: Optional[str] = None
    source_arxiv_id: Optional[str] = None
    
    # Verification
    is_verified: bool = False
    evidence_grade: str = "D"
    
    # Context
    context: str = ""
    page_number: Optional[int] = None


@dataclass  
class SimilarPaper:
    """A recommended similar paper."""
    title: str
    authors: List[str]
    year: Optional[int]
    url: str
    pdf_url: Optional[str]
    doi: Optional[str]
    arxiv_id: Optional[str]
    citation_count: int
    similarity_score: float
    recommendation_reason: str


@dataclass
class EnterpriseResearchReport:
    """Enterprise-grade research report with full metadata."""
    # Query info
    topic: str
    query_id: str
    timestamp: str
    
    # Summary
    executive_summary: str
    key_findings: List[str]
    research_gaps: List[str]
    
    # Sources
    sources: List[EnterpriseSource]
    total_sources: int
    verified_sources: int
    open_access_sources: int
    
    # Claims
    claims: List[ExtractedClaim]
    verified_claims: int
    total_claims: int
    
    # Quality metrics
    overall_grade: str
    overall_score: float
    confidence_score: float
    
    # Similar papers
    similar_papers: List[SimilarPaper]
    
    # Validation
    validation_issues: List[Dict[str, str]]
    recommendations: List[str]
    
    # Provider breakdown
    provider_stats: Dict[str, int]
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "query_id": self.query_id,
            "timestamp": self.timestamp,
            "executive_summary": self.executive_summary,
            "key_findings": self.key_findings,
            "research_gaps": self.research_gaps,
            "sources": [s.to_dict() for s in self.sources],
            "total_sources": self.total_sources,
            "verified_sources": self.verified_sources,
            "open_access_sources": self.open_access_sources,
            "claims": [asdict(c) for c in self.claims],
            "verified_claims": self.verified_claims,
            "total_claims": self.total_claims,
            "overall_grade": self.overall_grade,
            "overall_score": self.overall_score,
            "confidence_score": self.confidence_score,
            "similar_papers": [asdict(p) for p in self.similar_papers],
            "validation_issues": self.validation_issues,
            "recommendations": self.recommendations,
            "provider_stats": self.provider_stats,
            "metadata": self.metadata,
        }
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)


class EnterpriseResearchAgent:
    """Enterprise-grade research agent with all features."""
    
    def __init__(
        self,
        enable_verification: bool = True,
        enable_recommendations: bool = True,
        enable_pdf_resolution: bool = True,
        max_sources_per_provider: int = 10,
        max_similar_papers: int = 5,
    ):
        self.enable_verification = enable_verification
        self.enable_recommendations = enable_recommendations
        self.enable_pdf_resolution = enable_pdf_resolution
        self.max_sources_per_provider = max_sources_per_provider
        self.max_similar_papers = max_similar_papers
        
        # Lazy-loaded components
        self._recommender = None
        self._pdf_resolver = None
        self._verifier = None
        self._grader = None
    
    def _get_recommender(self) -> PaperRecommender:
        if self._recommender is None:
            self._recommender = PaperRecommender()
        return self._recommender
    
    def _get_pdf_resolver(self) -> PDFLinkResolver:
        if self._pdf_resolver is None:
            self._pdf_resolver = PDFLinkResolver()
        return self._pdf_resolver
    
    def _get_verifier(self):
        if self._verifier is None:
            from ..verification import CitationVerifier
            self._verifier = CitationVerifier()
        return self._verifier
    
    def _get_grader(self):
        if self._grader is None:
            from ..verification import EvidenceGrader
            self._grader = EvidenceGrader()
        return self._grader
    
    def research(self, topic: str) -> EnterpriseResearchReport:
        """Conduct enterprise-grade research on a topic.
        
        Args:
            topic: Research topic/question
            
        Returns:
            EnterpriseResearchReport with full metadata
        """
        print("=" * 70)
        print(f"🔬 ENTERPRISE RESEARCH: {topic}")
        print("=" * 70)
        
        # Generate query ID
        query_id = hashlib.md5(f"{topic}{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        timestamp = datetime.now().isoformat()
        
        # Step 1: Multi-provider search
        print("\n📚 Step 1: Searching 5 academic providers...")
        raw_sources = self._search_all_providers(topic)
        print(f"   Found {len(raw_sources)} total sources")
        
        # Step 2: Deduplicate
        print("\n🔄 Step 2: Deduplicating sources...")
        unique_sources = self._deduplicate_sources(raw_sources)
        print(f"   {len(unique_sources)} unique sources after deduplication")
        
        # Step 3: Resolve PDF links
        if self.enable_pdf_resolution:
            print("\n📄 Step 3: Resolving PDF links...")
            unique_sources = self._resolve_pdf_links(unique_sources)
            pdf_count = sum(1 for s in unique_sources if s.pdf_url)
            print(f"   Found PDF links for {pdf_count}/{len(unique_sources)} sources")
        
        # Step 4: Verify citations
        if self.enable_verification:
            print("\n✅ Step 4: Verifying citations...")
            unique_sources = self._verify_sources(unique_sources)
            verified = sum(1 for s in unique_sources if s.is_verified)
            print(f"   Verified {verified}/{len(unique_sources)} sources")
        
        # Step 5: Grade evidence
        print("\n📊 Step 5: Grading evidence quality...")
        unique_sources = self._grade_sources(unique_sources)
        
        # Step 6: Find similar papers
        similar_papers = []
        if self.enable_recommendations and unique_sources:
            print("\n🔗 Step 6: Finding similar papers...")
            similar_papers = self._find_similar_papers(unique_sources[:3])
            print(f"   Found {len(similar_papers)} similar papers")
        
        # Step 7: Generate report
        print("\n📝 Step 7: Generating report...")
        report = self._generate_report(
            topic=topic,
            query_id=query_id,
            timestamp=timestamp,
            sources=unique_sources,
            similar_papers=similar_papers,
        )
        
        print("\n" + "=" * 70)
        print(f"✨ RESEARCH COMPLETE")
        print(f"   Sources: {report.total_sources} ({report.verified_sources} verified)")
        print(f"   Open Access: {report.open_access_sources}")
        print(f"   Grade: {report.overall_grade} (Score: {report.overall_score:.2f})")
        print(f"   Similar Papers: {len(report.similar_papers)}")
        print("=" * 70)
        
        return report
    
    def _search_all_providers(self, topic: str) -> List[EnterpriseSource]:
        """Search all 5 FREE academic providers."""
        sources = []
        
        # Import providers
        try:
            from .providers import (
                ArxivProvider,
                OpenReviewProvider, 
                PubMedProvider,
                HALProvider,
                ZenodoProvider,
            )
            
            providers = [
                ("arXiv", ArxivProvider()),
                ("OpenReview", OpenReviewProvider()),
                ("PubMed", PubMedProvider()),
                ("HAL", HALProvider()),
                ("Zenodo", ZenodoProvider()),
            ]
            
            for name, provider in providers:
                try:
                    if not provider.is_available():
                        print(f"   ⚠️ {name}: Not available")
                        continue
                    
                    results = provider.search(topic, limit=self.max_sources_per_provider)
                    
                    for result in results:
                        source = EnterpriseSource(
                            title=result.title,
                            doi=result.metadata.get("doi"),
                            arxiv_id=result.metadata.get("arxiv_id"),
                            pmc_id=result.metadata.get("pmc_id"),
                            authors=result.authors,
                            year=result.year,
                            venue=result.venue,
                            abstract=result.abstract,
                            url=result.url,
                            pdf_url=result.metadata.get("pdf_url"),
                            provider=name.lower(),
                        )
                        sources.append(source)
                    
                    print(f"   ✓ {name}: {len(results)} papers")
                    
                except Exception as e:
                    print(f"   ✗ {name}: Error - {e}")
            
        except ImportError as e:
            print(f"   ⚠️ Provider import error: {e}")
        
        return sources
    
    def _deduplicate_sources(self, sources: List[EnterpriseSource]) -> List[EnterpriseSource]:
        """Remove duplicate sources based on DOI, arXiv ID, or title."""
        seen_dois: Set[str] = set()
        seen_arxiv: Set[str] = set()
        seen_titles: Set[str] = set()
        unique = []
        
        for source in sources:
            # Check by DOI
            if source.doi:
                if source.doi.lower() in seen_dois:
                    continue
                seen_dois.add(source.doi.lower())
            
            # Check by arXiv ID
            if source.arxiv_id:
                if source.arxiv_id.lower() in seen_arxiv:
                    continue
                seen_arxiv.add(source.arxiv_id.lower())
            
            # Check by normalized title
            norm_title = source.title.lower()[:50]
            if norm_title in seen_titles:
                continue
            seen_titles.add(norm_title)
            
            unique.append(source)
        
        return unique
    
    def _resolve_pdf_links(self, sources: List[EnterpriseSource]) -> List[EnterpriseSource]:
        """Resolve PDF links for all sources."""
        resolver = self._get_pdf_resolver()
        
        for source in sources:
            if source.pdf_url:
                source.is_open_access = True
                continue
            
            try:
                resolved = resolver.resolve(
                    doi=source.doi,
                    arxiv_id=source.arxiv_id,
                    pmc_id=source.pmc_id,
                )
                
                if resolved:
                    source.pdf_url = resolved.pdf_url
                    source.html_url = resolved.html_url
                    source.is_open_access = resolved.is_open_access
                    source.oa_status = resolved.oa_status
                    
            except Exception:
                pass
        
        return sources
    
    def _verify_sources(self, sources: List[EnterpriseSource]) -> List[EnterpriseSource]:
        """Verify all sources via DOI/arXiv APIs."""
        verifier = self._get_verifier()
        
        for source in sources:
            try:
                if source.doi:
                    verified = verifier.verify_doi(source.doi)
                    if verified:
                        source.is_verified = True
                        source.verification_method = "doi"
                        continue
                
                if source.arxiv_id:
                    verified = verifier.verify_arxiv(source.arxiv_id)
                    if verified:
                        source.is_verified = True
                        source.verification_method = "arxiv"
                        continue
                
            except Exception:
                pass
        
        return sources
    
    def _grade_sources(self, sources: List[EnterpriseSource]) -> List[EnterpriseSource]:
        """Grade evidence quality for all sources."""
        grader = self._get_grader()
        
        for source in sources:
            try:
                grade_result = grader.grade_source({
                    "doi": source.doi,
                    "arxiv_id": source.arxiv_id,
                    "venue": source.venue,
                    "year": source.year,
                    "is_verified": source.is_verified,
                    "citation_count": source.citation_count,
                })
                
                source.evidence_grade = grade_result.grade
                source.evidence_score = grade_result.score
                source.confidence = grade_result.confidence
                
            except Exception:
                source.evidence_grade = "D"
                source.evidence_score = 0.4
                source.confidence = 0.3
        
        return sources
    
    def _find_similar_papers(self, top_sources: List[EnterpriseSource]) -> List[SimilarPaper]:
        """Find similar papers based on top sources."""
        recommender = self._get_recommender()
        similar = []
        
        for source in top_sources:
            try:
                # Use DOI or arXiv ID
                paper_id = source.doi or source.arxiv_id
                if not paper_id:
                    continue
                
                recommendations = recommender.find_similar(paper_id, limit=3)
                
                for rec in recommendations:
                    similar.append(SimilarPaper(
                        title=rec.title,
                        authors=rec.authors,
                        year=rec.year,
                        url=rec.url,
                        pdf_url=rec.pdf_url,
                        doi=rec.doi,
                        arxiv_id=rec.arxiv_id,
                        citation_count=rec.citation_count,
                        similarity_score=rec.similarity_score,
                        recommendation_reason=rec.recommendation_reason,
                    ))
                    
            except Exception:
                pass
        
        # Deduplicate and limit
        seen = set()
        unique = []
        for paper in similar:
            key = paper.title.lower()[:50]
            if key not in seen:
                seen.add(key)
                unique.append(paper)
        
        return unique[:self.max_similar_papers]
    
    def _generate_report(
        self,
        topic: str,
        query_id: str,
        timestamp: str,
        sources: List[EnterpriseSource],
        similar_papers: List[SimilarPaper],
    ) -> EnterpriseResearchReport:
        """Generate the final research report."""
        # Calculate metrics
        verified_sources = sum(1 for s in sources if s.is_verified)
        open_access_sources = sum(1 for s in sources if s.is_open_access)
        
        # Calculate provider stats
        provider_stats: Dict[str, int] = {}
        for source in sources:
            provider_stats[source.provider] = provider_stats.get(source.provider, 0) + 1
        
        # Calculate overall score
        if sources:
            avg_score = sum(s.evidence_score for s in sources) / len(sources)
            verification_rate = verified_sources / len(sources)
            overall_score = (avg_score * 0.6 + verification_rate * 0.4)
        else:
            overall_score = 0.0
        
        # Determine grade
        if overall_score >= 0.9:
            overall_grade = "A"
        elif overall_score >= 0.8:
            overall_grade = "B"
        elif overall_score >= 0.6:
            overall_grade = "C"
        elif overall_score >= 0.4:
            overall_grade = "D"
        else:
            overall_grade = "F"
        
        # Generate validation issues
        validation_issues = []
        if verified_sources < len(sources) * 0.5:
            validation_issues.append({
                "type": "low_verification",
                "message": f"Only {verified_sources}/{len(sources)} sources verified",
                "severity": "warning",
            })
        
        if open_access_sources < len(sources) * 0.3:
            validation_issues.append({
                "type": "low_open_access",
                "message": f"Only {open_access_sources}/{len(sources)} sources are open access",
                "severity": "info",
            })
        
        # Generate recommendations
        recommendations = [
            "Review unverified sources manually before citing",
            "Check PDF links for accessibility",
            "Consider similar papers for additional context",
        ]
        
        if overall_grade in ["D", "F"]:
            recommendations.insert(0, "⚠️ Low evidence quality - verify claims independently")
        
        # Generate summaries (placeholder - would use LLM in production)
        executive_summary = f"Research on '{topic}' found {len(sources)} sources across {len(provider_stats)} providers."
        
        key_findings = [
            f"Found {len(sources)} relevant academic papers",
            f"Verified {verified_sources} sources via DOI/arXiv",
            f"Open access available for {open_access_sources} papers",
            f"Recommended {len(similar_papers)} similar papers for further reading",
        ]
        
        research_gaps = [
            "Additional verification needed for unverified sources",
            "Some papers may require institutional access",
        ]
        
        return EnterpriseResearchReport(
            topic=topic,
            query_id=query_id,
            timestamp=timestamp,
            executive_summary=executive_summary,
            key_findings=key_findings,
            research_gaps=research_gaps,
            sources=sources,
            total_sources=len(sources),
            verified_sources=verified_sources,
            open_access_sources=open_access_sources,
            claims=[],  # Would extract from content
            verified_claims=0,
            total_claims=0,
            overall_grade=overall_grade,
            overall_score=overall_score,
            confidence_score=overall_score * 0.9,
            similar_papers=similar_papers,
            validation_issues=validation_issues,
            recommendations=recommendations,
            provider_stats=provider_stats,
            metadata={
                "version": "1.0.0",
                "agent": "EnterpriseResearchAgent",
                "features": {
                    "verification": self.enable_verification,
                    "recommendations": self.enable_recommendations,
                    "pdf_resolution": self.enable_pdf_resolution,
                },
            },
        )


# Convenience function
def enterprise_research(topic: str) -> EnterpriseResearchReport:
    """Run enterprise-grade research on a topic."""
    agent = EnterpriseResearchAgent()
    return agent.research(topic)
