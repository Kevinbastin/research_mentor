"""Research validator - comprehensive validation of research outputs."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime

from .citation_verifier import CitationVerifier, VerifiedCitation, VerificationStatus
from .claim_extractor import ClaimExtractor, ExtractedClaim, ClaimSource
from .evidence_grader import EvidenceGrader, EvidenceAssessment, EvidenceGrade


@dataclass
class ValidationIssue:
    """A validation issue found in research output."""
    severity: str  # "error", "warning", "info"
    category: str  # "citation", "claim", "methodology", "data"
    message: str
    location: str = ""
    suggestion: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity,
            "category": self.category,
            "message": self.message,
            "location": self.location,
            "suggestion": self.suggestion,
        }


@dataclass
class ValidationReport:
    """Complete validation report for research output."""
    timestamp: str
    is_valid: bool
    overall_grade: str
    overall_score: float
    total_citations: int
    verified_citations: int
    total_claims: int
    verified_claims: int
    issues: List[ValidationIssue] = field(default_factory=list)
    citations: List[VerifiedCitation] = field(default_factory=list)
    claims: List[ExtractedClaim] = field(default_factory=list)
    evidence_assessments: List[EvidenceAssessment] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "is_valid": self.is_valid,
            "overall_grade": self.overall_grade,
            "overall_score": self.overall_score,
            "total_citations": self.total_citations,
            "verified_citations": self.verified_citations,
            "total_claims": self.total_claims,
            "verified_claims": self.verified_claims,
            "issues": [i.to_dict() for i in self.issues],
            "recommendations": self.recommendations,
            "metadata": self.metadata,
        }
    
    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            f"=== Validation Report ===",
            f"Grade: {self.overall_grade} (Score: {self.overall_score:.2f})",
            f"Citations: {self.verified_citations}/{self.total_citations} verified",
            f"Claims: {self.verified_claims}/{self.total_claims} verifiable",
            f"Issues: {len([i for i in self.issues if i.severity == error])} errors, "
            f"{len([i for i in self.issues if i.severity == warning])} warnings",
        ]
        
        if self.issues:
            lines.append("\n--- Issues ---")
            for issue in self.issues[:10]:
                lines.append(f"[{issue.severity.upper()}] {issue.category}: {issue.message}")
        
        if self.recommendations:
            lines.append("\n--- Recommendations ---")
            for rec in self.recommendations[:5]:
                lines.append(f"• {rec}")
        
        return "\n".join(lines)


class ResearchValidator:
    """Validates research outputs for accuracy, citations, and evidence quality."""
    
    def __init__(self):
        self.citation_verifier = CitationVerifier()
        self.claim_extractor = ClaimExtractor()
        self.evidence_grader = EvidenceGrader()
    
    def validate(
        self,
        text: str,
        sources: List[Dict[str, Any]] = None,
        strict_mode: bool = False,
    ) -> ValidationReport:
        """Validate research text with sources."""
        
        issues = []
        citations = []
        claims = []
        evidence_assessments = []
        
        # 1. Verify all citations
        if sources:
            for source in sources:
                title = source.get("title", "")
                authors = source.get("authors", [])
                year = source.get("year")
                doi = source.get("doi")
                arxiv_id = source.get("arxiv_id")
                
                if doi:
                    verified = self.citation_verifier.verify_doi(doi)
                elif arxiv_id:
                    verified = self.citation_verifier.verify_arxiv_id(arxiv_id)
                else:
                    verified = self.citation_verifier.verify(title, authors, year)
                
                citations.append(verified)
                
                # Check for issues
                if verified.status == VerificationStatus.NOT_FOUND:
                    issues.append(ValidationIssue(
                        severity="error",
                        category="citation",
                        message=f"Paper not found: {title[:50]}...",
                        suggestion="Verify paper title or check DOI/arXiv ID"
                    ))
                elif verified.status == VerificationStatus.SYNTHETIC:
                    issues.append(ValidationIssue(
                        severity="error",
                        category="citation",
                        message=f"Paper may be synthetic: {title[:50]}...",
                        suggestion="This title may be AI-generated, verify original source"
                    ))
                elif verified.status == VerificationStatus.PARTIAL:
                    issues.append(ValidationIssue(
                        severity="warning",
                        category="citation",
                        message=f"Title mismatch: {title[:30]}... vs {verified.verified_title[:30]}...",
                        suggestion="Use exact title from verified source"
                    ))
        
        # 2. Extract and validate claims
        claims = self.claim_extractor.extract_from_text(text)
        
        for claim in claims:
            # Validate each claim
            validation = self.claim_extractor.validate_claim(claim)
            
            if not validation["is_valid"]:
                for issue_msg in validation["issues"]:
                    issues.append(ValidationIssue(
                        severity="error",
                        category="claim",
                        message=issue_msg,
                        location=claim.text[:50],
                    ))
            
            for warning_msg in validation.get("warnings", []):
                issues.append(ValidationIssue(
                    severity="warning",
                    category="claim",
                    message=warning_msg,
                    location=claim.text[:50],
                ))
            
            # Grade evidence for each claim
            assessment = self.evidence_grader.grade_claim(claim)
            evidence_assessments.append(assessment)
        
        # 3. Check for unverified numerical claims
        unverified_numbers = self._find_unverified_numbers(text, claims)
        for num_text in unverified_numbers:
            issues.append(ValidationIssue(
                severity="warning",
                category="claim",
                message=f"Unverified numerical claim: {num_text[:50]}",
                suggestion="Attach DOI or arXiv ID to verify this metric"
            ))
        
        # 4. Check for methodology issues
        methodology_issues = self._check_methodology(text)
        issues.extend(methodology_issues)
        
        # 5. Check for dataset issues
        dataset_issues = self._check_datasets(text)
        issues.extend(dataset_issues)
        
        # 6. Check for simulation vs real-world distinction
        sim_issues = self._check_simulation_distinction(text)
        issues.extend(sim_issues)
        
        # 7. Calculate overall grade
        verified_count = len([c for c in citations if c.status == VerificationStatus.VERIFIED])
        verifiable_claims = len([c for c in claims if c.is_verifiable])
        
        grade_summary = self.evidence_grader.summarize_grades(evidence_assessments) if evidence_assessments else {
            "overall_grade": "C" if verified_count > 0 else "D",
            "average_score": 0.5 if verified_count > 0 else 0.3,
            "recommendations": ["Add more verifiable citations"]
        }
        
        # Determine if valid
        error_count = len([i for i in issues if i.severity == "error"])
        is_valid = error_count == 0 if strict_mode else error_count < 3
        
        # Compile recommendations
        recommendations = list(set(grade_summary.get("recommendations", [])))
        
        if verified_count < len(citations) * 0.5:
            recommendations.append("Verify more citations against academic databases")
        
        if verifiable_claims < len(claims) * 0.5:
            recommendations.append("Add DOIs/arXiv IDs to support numerical claims")
        
        return ValidationReport(
            timestamp=datetime.now().isoformat(),
            is_valid=is_valid,
            overall_grade=grade_summary.get("overall_grade", "D"),
            overall_score=grade_summary.get("average_score", 0.3),
            total_citations=len(citations),
            verified_citations=verified_count,
            total_claims=len(claims),
            verified_claims=verifiable_claims,
            issues=issues,
            citations=citations,
            claims=claims,
            evidence_assessments=evidence_assessments,
            recommendations=recommendations,
            metadata={
                "strict_mode": strict_mode,
                "sources_provided": len(sources) if sources else 0,
            }
        )
    
    def _find_unverified_numbers(self, text: str, claims: List[ExtractedClaim]) -> List[str]:
        """Find numerical claims not covered by extracted claims."""
        unverified = []
        
        # Pattern for numerical claims
        patterns = [
            r"\d+\.?\d*\s*%\s+(?:accuracy|improvement|reduction|increase)",
            r"achieves?\s+\d+\.?\d*\s*%",
            r"\d+\.?\d*x\s+(?:faster|speedup)",
        ]
        
        claimed_positions = set()
        for claim in claims:
            # Mark positions of verified claims
            match = re.search(re.escape(claim.text), text)
            if match:
                claimed_positions.add(match.start())
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                if match.start() not in claimed_positions:
                    unverified.append(match.group(0))
        
        return unverified[:5]  # Limit to 5
    
    def _check_methodology(self, text: str) -> List[ValidationIssue]:
        """Check for methodology issues."""
        issues = []
        
        # Check for fair comparison
        unfair_patterns = [
            (r"outperforms?\s+(?:all\s+)?(?:previous|existing|other)", 
             "Broad comparison claim without specific baselines"),
            (r"state-of-the-art\s+(?:results?|performance)",
             "SOTA claim requires specific comparison details"),
        ]
        
        for pattern, message in unfair_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                # Check if comparison details are provided
                has_details = re.search(
                    r"(?:compared\s+(?:to|with)|baseline|benchmark)\s+\w+",
                    text, re.IGNORECASE
                )
                if not has_details:
                    issues.append(ValidationIssue(
                        severity="warning",
                        category="methodology",
                        message=message,
                        suggestion="Specify exact baselines, datasets, and evaluation metrics"
                    ))
        
        # Check for missing experimental details
        detail_keywords = ["hardware", "gpu", "cpu", "epochs", "batch size", "learning rate"]
        if not any(kw in text.lower() for kw in detail_keywords):
            issues.append(ValidationIssue(
                severity="info",
                category="methodology",
                message="Limited experimental setup details",
                suggestion="Include hardware specs, hyperparameters, and training details"
            ))
        
        return issues
    
    def _check_datasets(self, text: str) -> List[ValidationIssue]:
        """Check for dataset specification issues."""
        issues = []
        
        # Vague dataset references
        vague_patterns = [
            (r"(?:kaggle|open[- ]?source)\s+dataset", 
             "Vague dataset reference"),
            (r"publicly\s+available\s+dataset",
             "Dataset not specifically named"),
            (r"benchmark\s+dataset(?![\s:]+[A-Z])",
             "Benchmark dataset not specified"),
        ]
        
        for pattern, message in vague_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(ValidationIssue(
                    severity="warning",
                    category="data",
                    message=message,
                    suggestion="Specify dataset name, version, and access URL"
                ))
        
        return issues
    
    def _check_simulation_distinction(self, text: str) -> List[ValidationIssue]:
        """Check if simulation and real-world results are distinguished."""
        issues = []
        
        has_simulation = bool(re.search(r"simulat(?:ion|ed|or)", text, re.IGNORECASE))
        has_real = bool(re.search(r"real[- ]?world|physical|hardware|robot", text, re.IGNORECASE))
        
        if has_simulation and has_real:
            # Check if they are distinguished
            distinction_patterns = [
                r"simulation\s+(?:vs\.?|versus|compared\s+to)\s+real",
                r"(?:in\s+)?simulation.*(?:in\s+)?real[- ]?world",
                r"transfer(?:red)?\s+(?:from|to)\s+(?:simulation|real)",
            ]
            
            has_distinction = any(
                re.search(p, text, re.IGNORECASE) 
                for p in distinction_patterns
            )
            
            if not has_distinction:
                issues.append(ValidationIssue(
                    severity="warning",
                    category="methodology",
                    message="Simulation and real-world results may be mixed",
                    suggestion="Clearly distinguish simulation from real-world experiments"
                ))
        
        return issues
    
    def validate_summary(
        self,
        summary: str,
        sources: List[Dict[str, Any]],
    ) -> ValidationReport:
        """Validate a research summary against its sources."""
        return self.validate(summary, sources, strict_mode=False)
    
    def reviewer_check(self, text: str, sources: List[Dict[str, Any]] = None) -> str:
        """Perform reviewer-style validation check and return formatted report."""
        report = self.validate(text, sources, strict_mode=True)
        return report.summary()
