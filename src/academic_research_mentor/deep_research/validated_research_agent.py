"""Validated Deep Research Agent - Research with citation verification."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .deep_research_agent import (
    DeepResearchAgent, 
    ResearchConfig, 
    ResearchReport, 
    SearchResultSummary,
    ResearchDepth,
)


@dataclass
class ValidatedSource:
    """A source with verification metadata."""
    title: str
    url: str
    source: str
    year: Optional[int] = None
    authors: List[str] = field(default_factory=list)
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    venue: Optional[str] = None
    is_verified: bool = False
    verification_status: str = "unverified"
    confidence: float = 0.0
    evidence_grade: str = "D"
    evidence_score: float = 0.0


@dataclass
class ValidatedClaim:
    """An extracted claim with evidence grading."""
    text: str
    value: float
    unit: str
    metric_name: str
    source_title: str
    source_doi: Optional[str] = None
    source_arxiv_id: Optional[str] = None
    evidence_grade: str = "D"
    is_verifiable: bool = False


@dataclass
class ValidatedResearchReport:
    """Research report with validation information."""
    topic: str
    summary: str
    key_themes: List[str]
    sources: List[ValidatedSource]
    claims: List[ValidatedClaim]
    overall_grade: str
    overall_score: float
    verified_citations: int
    total_citations: int
    verifiable_claims: int
    total_claims: int
    validation_issues: List[Dict[str, str]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ValidatedResearchAgent:
    """Deep research with citation verification and evidence grading."""
    
    def __init__(self, config: Optional[ResearchConfig] = None):
        self.config = config or ResearchConfig()
        self.base_agent = DeepResearchAgent(config)
        self._verifier = None
        self._extractor = None
        self._grader = None
    
    def _get_verifier(self):
        if self._verifier is None:
            from ..verification import CitationVerifier
            self._verifier = CitationVerifier()
        return self._verifier
    
    def _get_extractor(self):
        if self._extractor is None:
            from ..verification import ClaimExtractor
            self._extractor = ClaimExtractor()
        return self._extractor
    
    def _get_grader(self):
        if self._grader is None:
            from ..verification import EvidenceGrader
            self._grader = EvidenceGrader()
        return self._grader
    
    def research(self, topic: str) -> ValidatedResearchReport:
        """Conduct deep research with validation."""
        print("=" * 70)
        print("VALIDATED DEEP RESEARCH: " + topic)
        print("=" * 70)
        
        print("")
        print("[Phase 1] Gathering sources from 5 FREE providers...")
        base_report = self.base_agent.research(topic)
        
        print("")
        print("[Phase 2] Verifying citations...")
        validated_sources = self._verify_sources(base_report.sources)
        
        print("")
        print("[Phase 3] Extracting and validating claims...")
        claims = self._extract_claims(base_report.summary, validated_sources)
        
        print("")
        print("[Phase 4] Grading evidence quality...")
        graded_sources, overall_grade, overall_score = self._grade_evidence(validated_sources)
        
        issues = self._compile_issues(validated_sources, claims)
        recommendations = self._generate_recommendations(validated_sources, claims, issues)
        
        verified_count = len([s for s in validated_sources if s.is_verified])
        verifiable_claims = len([c for c in claims if c.is_verifiable])
        
        print("")
        print("=" * 70)
        print("VALIDATION COMPLETE")
        print("=" * 70)
        print("Grade: " + overall_grade + " (Score: " + str(round(overall_score, 2)) + ")")
        print("Citations: " + str(verified_count) + "/" + str(len(validated_sources)) + " verified")
        print("Claims: " + str(verifiable_claims) + "/" + str(len(claims)) + " verifiable")
        
        return ValidatedResearchReport(
            topic=topic,
            summary=base_report.summary,
            key_themes=base_report.key_themes,
            sources=graded_sources,
            claims=claims,
            overall_grade=overall_grade,
            overall_score=overall_score,
            verified_citations=verified_count,
            total_citations=len(validated_sources),
            verifiable_claims=verifiable_claims,
            total_claims=len(claims),
            validation_issues=issues,
            recommendations=recommendations,
            metadata=base_report.metadata,
        )
    
    def _verify_sources(self, sources):
        verifier = self._get_verifier()
        validated = []
        
        for source in sources:
            arxiv_id = None
            if "arxiv.org" in source.url:
                match = re.search(r"arxiv\.org/abs/(\d+\.\d+)", source.url)
                if match:
                    arxiv_id = match.group(1)
            
            if arxiv_id:
                result = verifier.verify_arxiv_id(arxiv_id)
            else:
                result = verifier.verify(source.title, source.authors, source.year)
            
            validated.append(ValidatedSource(
                title=source.title,
                url=source.url,
                source=source.source,
                year=source.year,
                authors=source.authors,
                venue=source.venue,
                doi=result.doi,
                arxiv_id=result.arxiv_id or arxiv_id,
                is_verified=result.status.value == "verified",
                verification_status=result.status.value,
                confidence=result.confidence,
            ))
            
            status = "V" if result.status.value == "verified" else "?"
            print("  [" + status + "] " + source.title[:50] + "...")
        
        return validated
    
    def _extract_claims(self, text, sources):
        extractor = self._get_extractor()
        grader = self._get_grader()
        claims = []
        extracted = extractor.extract_from_text(text)
        
        for claim in extracted:
            matched_source = None
            for source in sources:
                if source.title.lower()[:30] in claim.context.lower():
                    matched_source = source
                    break
            
            assessment = grader.grade(
                has_doi=bool(matched_source and matched_source.doi),
                has_arxiv_id=bool(matched_source and matched_source.arxiv_id),
                citation_verified=bool(matched_source and matched_source.is_verified),
            )
            
            claims.append(ValidatedClaim(
                text=claim.text,
                value=claim.value,
                unit=claim.unit,
                metric_name=claim.metric_name,
                source_title=matched_source.title if matched_source else "",
                source_doi=matched_source.doi if matched_source else None,
                source_arxiv_id=matched_source.arxiv_id if matched_source else None,
                evidence_grade=assessment.grade.value,
                is_verifiable=bool(matched_source and (matched_source.doi or matched_source.arxiv_id)),
            ))
        
        return claims
    
    def _grade_evidence(self, sources):
        grader = self._get_grader()
        total_score = 0.0
        
        for source in sources:
            assessment = grader.grade(
                has_doi=bool(source.doi),
                has_arxiv_id=bool(source.arxiv_id),
                citation_verified=source.is_verified,
                is_peer_reviewed=source.venue is not None,
            )
            source.evidence_grade = assessment.grade.value
            source.evidence_score = assessment.score
            total_score += assessment.score
        
        avg_score = total_score / len(sources) if sources else 0.0
        
        if avg_score >= 0.85:
            grade = "A"
        elif avg_score >= 0.70:
            grade = "B"
        elif avg_score >= 0.50:
            grade = "C"
        elif avg_score >= 0.30:
            grade = "D"
        else:
            grade = "F"
        
        return sources, grade, avg_score
    
    def _compile_issues(self, sources, claims):
        issues = []
        unverified = [s for s in sources if not s.is_verified]
        if len(unverified) > len(sources) * 0.5:
            issues.append({
                "severity": "warning",
                "category": "citation",
                "message": str(len(unverified)) + "/" + str(len(sources)) + " citations not verified"
            })
        
        uncited = [c for c in claims if not c.is_verifiable]
        if uncited:
            issues.append({
                "severity": "warning",
                "category": "claim",
                "message": str(len(uncited)) + " claims lack verifiable citations"
            })
        return issues
    
    def _generate_recommendations(self, sources, claims, issues):
        recs = []
        if len([s for s in sources if s.is_verified]) < len(sources) * 0.7:
            recs.append("Verify paper titles against arXiv or CrossRef")
        if len([c for c in claims if c.is_verifiable]) < len(claims) * 0.5:
            recs.append("Include DOI/arXiv ID when reporting metrics")
        recs.append("Distinguish simulation from real-world results")
        recs.append("Specify dataset names, versions, and URLs")
        return recs
