"""Claim extraction - extracts numerical claims from papers."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum


class ClaimType(Enum):
    ACCURACY = "accuracy"
    PERFORMANCE = "performance"
    IMPROVEMENT = "improvement"
    RESOURCE = "resource"
    DATASET = "dataset"
    COMPARISON = "comparison"
    OTHER = "other"


class ClaimSource(Enum):
    ABSTRACT = "abstract"
    RESULTS = "results"
    TABLE = "table"
    FIGURE = "figure"
    CONCLUSION = "conclusion"
    UNKNOWN = "unknown"


@dataclass
class ExtractedClaim:
    """A numerical claim extracted from a paper."""
    text: str
    value: float
    unit: str = ""
    claim_type: ClaimType = ClaimType.OTHER
    metric_name: str = ""
    context: str = ""
    source_section: ClaimSource = ClaimSource.UNKNOWN
    paper_title: str = ""
    paper_doi: Optional[str] = None
    paper_arxiv_id: Optional[str] = None
    confidence: float = 0.0
    is_verifiable: bool = False
    experimental_setup: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "value": self.value,
            "unit": self.unit,
            "claim_type": self.claim_type.value,
            "metric_name": self.metric_name,
            "confidence": self.confidence,
        }


class ClaimExtractor:
    """Extracts numerical claims from text."""
    
    ACCURACY_PATTERNS = [
        r"(?:accuracy|acc)[\s:]*(?:of\s+)?(\d+\.?\d*)\s*%",
        r"(\d+\.?\d*)\s*%\s+(?:accuracy|acc)",
        r"F1[\s\-:]?(?:score)?[\s:]*(?:of\s+)?(\d+\.?\d*)",
        r"precision[\s:]*(?:of\s+)?(\d+\.?\d*)",
        r"recall[\s:]*(?:of\s+)?(\d+\.?\d*)",
    ]
    
    PERFORMANCE_PATTERNS = [
        r"(\d+\.?\d*)\s*(?:ms|milliseconds?)\s+(?:latency|inference)",
        r"latency[\s:]*(?:of\s+)?(\d+\.?\d*)\s*(?:ms|milliseconds?)",
        r"(\d+\.?\d*)\s*(?:FPS|fps)",
    ]
    
    IMPROVEMENT_PATTERNS = [
        r"(\d+\.?\d*)\s*%\s+(?:improvement|better|faster)",
        r"(?:improves?|outperforms?)\s+(?:by\s+)?(\d+\.?\d*)\s*%",
        r"(\d+\.?\d*)x\s+(?:faster|speedup)",
    ]
    
    def __init__(self):
        self.extracted_claims: List[ExtractedClaim] = []
    
    def extract_from_text(
        self,
        text: str,
        paper_title: str = "",
        paper_doi: str = None,
        paper_arxiv_id: str = None,
        source_section: ClaimSource = ClaimSource.UNKNOWN,
    ) -> List[ExtractedClaim]:
        """Extract all numerical claims from text."""
        claims = []
        
        claims.extend(self._extract_pattern_claims(
            text, self.ACCURACY_PATTERNS, ClaimType.ACCURACY, "%",
            paper_title, paper_doi, paper_arxiv_id, source_section
        ))
        
        claims.extend(self._extract_pattern_claims(
            text, self.PERFORMANCE_PATTERNS, ClaimType.PERFORMANCE, "",
            paper_title, paper_doi, paper_arxiv_id, source_section
        ))
        
        claims.extend(self._extract_pattern_claims(
            text, self.IMPROVEMENT_PATTERNS, ClaimType.IMPROVEMENT, "%",
            paper_title, paper_doi, paper_arxiv_id, source_section
        ))
        
        self.extracted_claims.extend(claims)
        return claims
    
    def _extract_pattern_claims(
        self,
        text: str,
        patterns: List[str],
        claim_type: ClaimType,
        default_unit: str,
        paper_title: str,
        paper_doi: str,
        paper_arxiv_id: str,
        source_section: ClaimSource,
    ) -> List[ExtractedClaim]:
        """Extract claims matching given patterns."""
        claims = []
        
        for pattern in patterns:
            for match in re.finditer(pattern, text, re.IGNORECASE):
                try:
                    value = float(match.group(1))
                    
                    start = max(0, match.start() - 100)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end].strip()
                    
                    unit = default_unit
                    matched_text = match.group(0)
                    if "ms" in matched_text.lower():
                        unit = "ms"
                    elif "fps" in matched_text.lower():
                        unit = "FPS"
                    
                    metric_name = self._extract_metric_name(matched_text)
                    confidence = 0.5
                    if paper_doi:
                        confidence += 0.3
                    elif paper_arxiv_id:
                        confidence += 0.25
                    
                    is_verifiable = bool(paper_doi or paper_arxiv_id)
                    
                    claim = ExtractedClaim(
                        text=matched_text,
                        value=value,
                        unit=unit,
                        claim_type=claim_type,
                        metric_name=metric_name,
                        context=context,
                        source_section=source_section,
                        paper_title=paper_title,
                        paper_doi=paper_doi,
                        paper_arxiv_id=paper_arxiv_id,
                        confidence=confidence,
                        is_verifiable=is_verifiable,
                    )
                    claims.append(claim)
                    
                except (ValueError, IndexError):
                    continue
        
        return claims
    
    def _extract_metric_name(self, text: str) -> str:
        """Extract the metric name from matched text."""
        text_lower = text.lower()
        
        keywords = ["accuracy", "acc", "f1", "precision", "recall", "latency", "fps"]
        for keyword in keywords:
            if keyword in text_lower:
                return keyword.upper() if len(keyword) <= 3 else keyword.capitalize()
        
        return "metric"
    
    def validate_claim(self, claim: ExtractedClaim) -> Dict[str, Any]:
        """Validate an extracted claim."""
        validation = {"is_valid": True, "issues": [], "warnings": []}
        
        if claim.claim_type == ClaimType.ACCURACY:
            if claim.value > 100 or claim.value < 0:
                validation["is_valid"] = False
                validation["issues"].append("Invalid accuracy: " + str(claim.value) + "%")
        
        if not claim.paper_doi and not claim.paper_arxiv_id:
            validation["warnings"].append("No DOI or arXiv ID for verification")
        
        return validation
