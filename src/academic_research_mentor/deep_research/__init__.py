"""Deep Research package for comprehensive research workflows.

Based on Open Deep Research: https://github.com/langchain-ai/open_deep_research
Provides native, validated, comparative, and trend analysis implementations.
"""

# Native implementation (lighter, no LangChain dependency)
from .deep_research_agent import DeepResearchAgent, ResearchConfig, ResearchReport, ResearchDepth
from .report_generator import ReportGenerator

# Validated research with citation verification
from .validated_research_agent import (
    ValidatedResearchAgent,
    ValidatedResearchReport,
    ValidatedSource,
    ValidatedClaim,
)

# Comparative research for comparing approaches
from .comparative_research import (
    ComparativeResearchAgent,
    ComparisonResult,
    ApproachSummary,
    compare_approaches,
)

# Trend analysis over time
from .trend_analysis import (
    TrendAnalysisAgent,
    TrendAnalysisResult,
    YearlyTrend,
    analyze_research_trends,
)


# LangGraph implementation (full Open Deep Research compatible)
def get_langchain_researcher():
    """Get the LangGraph deep researcher (lazy import)."""
    from .langchain_researcher import (
        deep_researcher,
        run_deep_research,
        run_deep_research_sync,
        DeepResearchConfig,
    )
    return deep_researcher, run_deep_research, run_deep_research_sync, DeepResearchConfig


__all__ = [
    # Native implementation
    "DeepResearchAgent",
    "ResearchConfig", 
    "ResearchReport",
    "ResearchDepth",
    "ReportGenerator",
    # Validated research
    "ValidatedResearchAgent",
    "ValidatedResearchReport",
    "ValidatedSource",
    "ValidatedClaim",
    # Comparative research
    "ComparativeResearchAgent",
    "ComparisonResult",
    "ApproachSummary",
    "compare_approaches",
    # Trend analysis
    "TrendAnalysisAgent",
    "TrendAnalysisResult",
    "YearlyTrend",
    "analyze_research_trends",
    # LangGraph (lazy)
    "get_langchain_researcher",
]
