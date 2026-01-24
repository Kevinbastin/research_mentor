from __future__ import annotations

from typing import Any, Dict, List, Optional

# Re-exports for compatibility
from .tools.legacy.arxiv.client import arxiv_search as arxiv_search  # noqa: F401
from .tools.utils.math import math_ground as math_ground  # noqa: F401
from .tools.utils.methodology import methodology_validate as methodology_validate  # noqa: F401


def deep_research(
    topic: str,
    depth: str = "standard",
    from_year: Optional[int] = 2020,
    include_gap_analysis: bool = True,
) -> Dict[str, Any]:
    """Conduct comprehensive deep research on a topic."""
    from .deep_research import DeepResearchAgent, ResearchConfig, ResearchDepth
    
    depth_map = {
        "shallow": ResearchDepth.SHALLOW,
        "standard": ResearchDepth.STANDARD,
        "deep": ResearchDepth.DEEP,
    }
    
    config = ResearchConfig(
        depth=depth_map.get(depth, ResearchDepth.STANDARD),
        from_year=from_year,
        include_gap_analysis=include_gap_analysis,
    )
    
    agent = DeepResearchAgent(config=config)
    report = agent.research(topic)
    
    return {
        "topic": report.topic,
        "summary": report.summary,
        "key_themes": report.key_themes,
        "sources": [
            {
                "title": s.title,
                "url": s.url,
                "source": s.source,
                "summary": s.summary,
                "year": s.year,
                "citations": s.citations,
            }
            for s in report.sources
        ],
        "gap_analysis": report.gap_analysis,
        "future_directions": report.future_directions,
        "markdown_report": report.markdown_report,
        "metadata": report.metadata,
    }


GEMINI_FUNCTION_DECLARATIONS: List[Dict[str, Any]] = [
    {
        "name": "arxiv_search",
        "description": "Search arXiv for relevant papers.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "from_year": {"type": "number", "description": "Minimum publication year"},
                "limit": {"type": "number", "description": "Max results"},
                "sort_by": {"type": "string", "enum": ["relevance", "date"]},
            },
            "required": ["query"],
        },
    },
    {
        "name": "deep_research",
        "description": "Conduct comprehensive deep research on a topic.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "description": "Research topic"},
                "depth": {"type": "string", "enum": ["shallow", "standard", "deep"]},
                "from_year": {"type": "number"},
                "include_gap_analysis": {"type": "boolean"},
            },
            "required": ["topic"],
        },
    },
    {
        "name": "math_ground",
        "description": "Heuristic math grounding.",
        "parameters": {
            "type": "object",
            "properties": {
                "text_or_math": {"type": "string"},
                "options": {"type": "object"},
            },
            "required": ["text_or_math"],
        },
    },
    {
        "name": "methodology_validate",
        "description": "Validate experiment plan.",
        "parameters": {
            "type": "object",
            "properties": {
                "plan": {"type": "string"},
                "checklist": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["plan"],
        },
    },
]


def get_gemini_tools_block() -> List[Dict[str, Any]]:
    return [{"function_declarations": GEMINI_FUNCTION_DECLARATIONS}]


def handle_mentor_function_call(function_name: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
    if function_name == "arxiv_search":
        return arxiv_search(
            query=str(function_args.get("query", "")),
            from_year=function_args.get("from_year"),
            limit=int(function_args.get("limit", 10)),
            sort_by=str(function_args.get("sort_by", "relevance")),
        )
    if function_name == "deep_research":
        return deep_research(
            topic=str(function_args.get("topic", "")),
            depth=str(function_args.get("depth", "standard")),
            from_year=function_args.get("from_year"),
            include_gap_analysis=function_args.get("include_gap_analysis", True),
        )
    if function_name == "math_ground":
        return math_ground(
            text_or_math=str(function_args.get("text_or_math", "")),
            options=function_args.get("options"),
        )
    if function_name == "methodology_validate":
        return methodology_validate(
            plan=str(function_args.get("plan", "")),
            checklist=function_args.get("checklist"),
        )
    return {"error": f"Unknown function: {function_name}"}
