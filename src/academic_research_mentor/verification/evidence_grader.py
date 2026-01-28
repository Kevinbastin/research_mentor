"""Evidence grading - rates the strength of research claims."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List
from enum import Enum


class EvidenceGrade(Enum):
    A = "A"  # Strong: Verified DOI/arXiv, reproducible
    B = "B"  # Moderate: Verified source, experimental results
    C = "C"  # Weak: Unverified but plausible
    D = "D"  # Very Weak: Unverified, missing info
    F = "F"  # Unreliable: Contradictory or fabricated


@dataclass
class EvidenceAssessment:
    """Assessment of evidence quality."""
    grade: EvidenceGrade
    score: float
    factors: Dict[str, float] = field(default_factory=dict)
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "grade": self.grade.value,
            "score": self.score,
            "factors": self.factors,
            "strengths": self.strengths,
            "weaknesses": self.weaknesses,
        }


class EvidenceGrader:
    """Grades evidence quality for research claims."""
    
    WEIGHTS = {
        "citation_verified": 0.25,
        "doi_present": 0.15,
        "peer_reviewed": 0.15,
        "reproducible": 0.15,
        "experimental_details": 0.10,
        "dataset_specified": 0.10,
        "comparison_fair": 0.05,
        "confidence_interval": 0.05,
    }
    
    def grade(
        self,
        has_doi: bool = False,
        has_arxiv_id: bool = False,
        citation_verified: bool = False,
        is_peer_reviewed: bool = False,
        has_experimental_details: bool = False,
        dataset_specified: bool = False,
        has_reproducible_code: bool = False,
        has_confidence_interval: bool = False,
        comparison_is_fair: bool = True,
        simulation_vs_real_distinguished: bool = True,
        is_synthetic: bool = False,
    ) -> EvidenceAssessment:
        """Grade evidence based on multiple factors."""
        
        factors = {}
        strengths = []
        weaknesses = []
        recommendations = []
        
        if citation_verified:
            factors["citation_verified"] = 1.0
            strengths.append("Citation verified")
        elif has_doi or has_arxiv_id:
            factors["citation_verified"] = 0.7
            strengths.append("Has DOI/arXiv ID")
        else:
            factors["citation_verified"] = 0.0
            weaknesses.append("Citation not verified")
            recommendations.append("Verify citation against CrossRef or arXiv")
        
        if has_doi:
            factors["doi_present"] = 1.0
        elif has_arxiv_id:
            factors["doi_present"] = 0.8
        else:
            factors["doi_present"] = 0.0
            recommendations.append("Include DOI or arXiv ID")
        
        if is_peer_reviewed:
            factors["peer_reviewed"] = 1.0
            strengths.append("Peer-reviewed")
        else:
            factors["peer_reviewed"] = 0.3
        
        if has_reproducible_code:
            factors["reproducible"] = 1.0
            strengths.append("Code available")
        elif has_experimental_details:
            factors["reproducible"] = 0.5
        else:
            factors["reproducible"] = 0.0
            weaknesses.append("Not reproducible")
            recommendations.append("Include experimental details")
        
        if has_experimental_details:
            factors["experimental_details"] = 1.0
        else:
            factors["experimental_details"] = 0.0
            weaknesses.append("Missing experimental details")
        
        if dataset_specified:
            factors["dataset_specified"] = 1.0
        else:
            factors["dataset_specified"] = 0.0
            recommendations.append("Specify dataset name, version, URL")
        
        factors["comparison_fair"] = 1.0 if comparison_is_fair else 0.0
        factors["confidence_interval"] = 1.0 if has_confidence_interval else 0.0
        
        score = sum(
            factors.get(key, 0.0) * weight
            for key, weight in self.WEIGHTS.items()
        )
        
        if is_synthetic:
            score *= 0.2
            weaknesses.append("Content appears synthetic")
        
        if not simulation_vs_real_distinguished:
            score *= 0.8
            weaknesses.append("Simulation/real not distinguished")
        
        if score >= 0.85:
            grade = EvidenceGrade.A
        elif score >= 0.70:
            grade = EvidenceGrade.B
        elif score >= 0.50:
            grade = EvidenceGrade.C
        elif score >= 0.30:
            grade = EvidenceGrade.D
        else:
            grade = EvidenceGrade.F
        
        return EvidenceAssessment(
            grade=grade,
            score=score,
            factors=factors,
            strengths=strengths,
            weaknesses=weaknesses,
            recommendations=recommendations,
        )
    
    def grade_claim(self, claim) -> EvidenceAssessment:
        """Grade a specific claim object."""
        return self.grade(
            has_doi=bool(getattr(claim, "paper_doi", None)),
            has_arxiv_id=bool(getattr(claim, "paper_arxiv_id", None)),
            citation_verified=getattr(claim, "is_verifiable", False),
        )
