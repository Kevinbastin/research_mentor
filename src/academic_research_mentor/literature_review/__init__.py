"""Literature Review Module

This module provides intelligent literature review capabilities using O3 reasoning
for intent extraction and research synthesis.

Enterprise Features:
- Multi-provider search (arXiv, OpenReview, PubMed, HAL, Zenodo)
- Citation verification (DOI/arXiv APIs)
- Evidence grading (A-F with confidence scores)
- Similar paper recommendations
- PDF link resolution
"""

from .build_context import build_research_context
from .intent_extractor import extract_research_intent

# Enterprise components
from .paper_recommender import (
    PaperRecommender,
    RecommendedPaper,
    find_similar_papers,
    get_paper_pdf_link,
    get_citing_papers,
)

from .pdf_resolver import (
    PDFLinkResolver,
    ResolvedPaper,
    get_pdf_link,
    is_open_access,
    get_all_links,
)

from .enterprise_agent import (
    EnterpriseResearchAgent,
    EnterpriseResearchReport,
    EnterpriseSource,
    ExtractedClaim,
    SimilarPaper,
    enterprise_research,
)

__all__ = [
    # Core
    "build_research_context",
    "extract_research_intent",
    # Paper Recommender
    "PaperRecommender",
    "RecommendedPaper",
    "find_similar_papers",
    "get_paper_pdf_link",
    "get_citing_papers",
    # PDF Resolver
    "PDFLinkResolver",
    "ResolvedPaper",
    "get_pdf_link",
    "is_open_access",
    "get_all_links",
    # Enterprise Agent
    "EnterpriseResearchAgent",
    "EnterpriseResearchReport",
    "EnterpriseSource",
    "ExtractedClaim",
    "SimilarPaper",
    "enterprise_research",
]